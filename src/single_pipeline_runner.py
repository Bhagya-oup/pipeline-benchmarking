"""
Single pipeline runner with parallel execution and checkpointing.
"""

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
import time
from threading import Lock

from .config import TestCase, PipelineResult, ComparisonConfig
from .pipeline_executor import PipelineExecutor
from .checkpoint_manager import CheckpointManager


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, calls_per_minute: int):
        """
        Initialize rate limiter.

        Args:
            calls_per_minute: Maximum API calls per minute
        """
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute if calls_per_minute > 0 else 0
        self.last_call_time = 0
        self.lock = Lock()

    def wait_if_needed(self):
        """Wait if necessary to maintain rate limit."""
        if self.min_interval == 0:
            return

        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_call_time

            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)

            self.last_call_time = time.time()


class SinglePipelineRunner:
    """Run single pipeline benchmarking in parallel."""

    def __init__(
        self,
        executor: PipelineExecutor,
        config: ComparisonConfig,
        checkpoint_manager: CheckpointManager
    ):
        """
        Initialize single pipeline runner.

        Args:
            executor: Pipeline executor
            config: Configuration (parallel workers, rate limit, etc.)
            checkpoint_manager: Checkpoint manager for resumability
        """
        self.executor = executor
        self.config = config
        self.checkpoint_manager = checkpoint_manager
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)

    def run(self, test_cases: List[TestCase]) -> List[PipelineResult]:
        """
        Run pipeline for all test cases.

        Args:
            test_cases: List of test cases to process

        Returns:
            List of pipeline results
        """
        # Track total execution time
        import time
        start_time = time.time()

        # Resume from checkpoint if exists
        completed_ids = self.checkpoint_manager.get_completed_ids()
        remaining = [tc for tc in test_cases if tc.sense_id not in completed_ids]

        print(f"{'='*80}")
        print(f"PIPELINE BENCHMARKING")
        print(f"{'='*80}")
        print(f"Total test cases: {len(test_cases)}")
        print(f"Already completed: {len(completed_ids)}")
        print(f"Remaining: {len(remaining)}")
        print(f"Parallel workers: {self.config.parallel_workers}")
        print(f"{'='*80}\n")

        if not remaining:
            print("All test cases already completed!")
            results = self.checkpoint_manager.load()
            # Add total time to metadata
            for result in results:
                result.metadata['total_execution_time'] = 0
            return results

        # Load any previously completed results
        all_results = self.checkpoint_manager.load()
        total_count = len(test_cases)

        # Parallel execution using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            # Submit all test cases
            future_to_testcase = {
                executor.submit(self._execute_single, tc): tc
                for tc in remaining
            }

            # Process results as they complete
            for future in as_completed(future_to_testcase):
                test_case = future_to_testcase[future]

                try:
                    result = future.result()
                    all_results.append(result)

                    # Show result
                    total_quots = result.metadata.get('total_quotations', 0)
                    matching_quots = result.metadata.get('matching_quotations', 0)
                    error_msg = f" ERROR: {result.error[:50]}" if result.error else ""

                    print(f"[{len(all_results)}/{total_count}] {test_case.sense_id}: "
                          f"{matching_quots}/{total_quots} matching{error_msg}")

                    # Checkpoint periodically
                    if len(all_results) % self.config.checkpoint_interval == 0:
                        self.checkpoint_manager.save(all_results)
                        print(f"  → Checkpoint saved: {len(all_results)} results")

                except Exception as e:
                    print(f"[{len(all_results)}/{total_count}] {test_case.sense_id}: ERROR - {e}")

        # Final checkpoint
        self.checkpoint_manager.save(all_results)

        # Calculate total execution time
        end_time = time.time()
        total_time = end_time - start_time

        # Add total time to all results metadata
        for result in all_results:
            result.metadata['total_execution_time'] = total_time

        # Print total execution time
        print(f"\n{'='*80}")
        print(f"Total execution time: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
        print(f"{'='*80}\n")

        return all_results

    def _execute_single(self, test_case: TestCase) -> PipelineResult:
        """
        Execute pipeline on a single test case.

        Args:
            test_case: Test case to process

        Returns:
            Pipeline result
        """
        # Rate limiting
        self.rate_limiter.wait_if_needed()

        # Execute with retry
        return self._execute_with_retry(test_case, max_retries=3)

    def _execute_with_retry(
        self,
        test_case: TestCase,
        max_retries: int = 3
    ) -> PipelineResult:
        """
        Execute with exponential backoff retry.

        Args:
            test_case: Test case to process
            max_retries: Maximum number of retry attempts

        Returns:
            Pipeline result
        """
        for attempt in range(max_retries):
            try:
                result = self.executor.execute(test_case)

                # If result has error, retry
                if result.error:
                    raise Exception(result.error)

                return result

            except Exception as e:
                if attempt == max_retries - 1:
                    # Final attempt failed, return error result
                    return PipelineResult(
                        test_case=test_case,
                        pipeline_name=self.executor.config.name,
                        quotations=[],
                        metadata={'error_type': type(e).__name__},
                        error=f"Failed after {max_retries} attempts: {str(e)}"
                    )

                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s", end='')
                time.sleep(wait_time)
