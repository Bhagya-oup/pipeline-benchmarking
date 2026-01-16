"""
Parallel comparison runner with rate limiting and error handling.
"""

import multiprocessing
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from typing import List
import time
from threading import Lock

from .config import TestCase, ComparisonResult, ComparisonConfig, PipelineResult
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


class ParallelComparisonRunner:
    """Run pipeline comparisons in parallel."""

    def __init__(
        self,
        new_executor: PipelineExecutor,
        old_executor: PipelineExecutor,
        config: ComparisonConfig,
        checkpoint_manager: CheckpointManager
    ):
        """
        Initialize parallel runner.

        Args:
            new_executor: Executor for new pipeline
            old_executor: Executor for old pipeline
            config: Comparison configuration
            checkpoint_manager: Checkpoint manager for resumability
        """
        self.new_executor = new_executor
        self.old_executor = old_executor
        self.config = config
        self.checkpoint_manager = checkpoint_manager
        self.rate_limiter = RateLimiter(config.rate_limit_per_minute)

    def run(self, test_cases: List[TestCase]) -> List[ComparisonResult]:
        """
        Run comparison for all test cases.

        Args:
            test_cases: List of test cases to process

        Returns:
            List of comparison results
        """
        # Resume from checkpoint if exists
        completed_ids = self.checkpoint_manager.get_completed_ids()
        remaining = [tc for tc in test_cases if tc.sense_id not in completed_ids]

        print(f"\n{'='*80}")
        print(f"PIPELINE COMPARISON")
        print(f"{'='*80}")
        print(f"Total test cases: {len(test_cases)}")
        print(f"Already completed: {len(completed_ids)}")
        print(f"Remaining: {len(remaining)}")
        print(f"Parallel workers: {self.config.parallel_workers}")
        print(f"{'='*80}\n")

        if not remaining:
            print("All test cases already completed!")
            return self.checkpoint_manager.load()

        # Load any previously completed results
        all_results = self.checkpoint_manager.load()
        initial_count = len(all_results)
        total_count = len(test_cases)

        # Parallel execution using ThreadPoolExecutor
        # (Threads work well since we're mostly waiting on network I/O)
        with ThreadPoolExecutor(max_workers=self.config.parallel_workers) as executor:
            # Submit all test cases
            future_to_testcase = {
                executor.submit(self._compare_single, tc): tc
                for tc in remaining
            }

            # Process results as they complete
            for future in as_completed(future_to_testcase):
                test_case = future_to_testcase[future]

                try:
                    result = future.result()
                    all_results.append(result)

                    # Show result
                    new_count = len(result.new_result.quotations)
                    old_count = len(result.old_result.quotations)
                    print(f"[{len(all_results)}/{total_count}] {test_case.sense_id}: New: {new_count}, Old: {old_count}")

                    # Checkpoint periodically
                    if len(all_results) % self.config.checkpoint_interval == 0:
                        self.checkpoint_manager.save(all_results)
                        print(f"  → Checkpoint saved: {len(all_results)} results")

                except Exception as e:
                    print(f"[{len(all_results)}/{total_count}] {test_case.sense_id}: ERROR - {e}")

        # Final checkpoint
        self.checkpoint_manager.save(all_results)

        return all_results

    def _compare_single(self, test_case: TestCase) -> ComparisonResult:
        """
        Compare both pipelines on a single test case.
        Calls BOTH pipelines in parallel for 2x speedup.

        Args:
            test_case: Test case to process

        Returns:
            Comparison result
        """
        # Rate limiting
        self.rate_limiter.wait_if_needed()

        # Execute BOTH pipelines in parallel using threads
        with ThreadPoolExecutor(max_workers=2) as executor:
            # Submit both pipeline calls simultaneously
            new_future = executor.submit(
                self._execute_with_retry,
                self.new_executor,
                test_case,
                3  # max_retries
            )
            old_future = executor.submit(
                self._execute_with_retry,
                self.old_executor,
                test_case,
                3  # max_retries
            )

            # Wait for both to complete
            new_result = new_future.result()
            old_result = old_future.result()

        return ComparisonResult(
            test_case=test_case,
            new_result=new_result,
            old_result=old_result
        )

    def _execute_with_retry(
        self,
        executor: PipelineExecutor,
        test_case: TestCase,
        max_retries: int = 3
    ) -> PipelineResult:
        """
        Execute with exponential backoff retry.

        Args:
            executor: Pipeline executor
            test_case: Test case to process
            max_retries: Maximum number of retry attempts

        Returns:
            Pipeline result
        """
        for attempt in range(max_retries):
            try:
                result = executor.execute(test_case)

                # If result has error, retry
                if result.error:
                    raise Exception(result.error)

                return result

            except Exception as e:
                if attempt == max_retries - 1:
                    # Final attempt failed, return error result
                    return PipelineResult(
                        test_case=test_case,
                        pipeline_name=executor.config.name,
                        quotations=[],
                        metadata={'error_type': type(e).__name__},
                        error=f"Failed after {max_retries} attempts: {str(e)}"
                    )

                # Exponential backoff
                wait_time = 2 ** attempt
                print(f"  Retry {attempt + 1}/{max_retries} after {wait_time}s", end='')
                time.sleep(wait_time)


# Example usage
if __name__ == "__main__":
    import os
    from config import PipelineConfig, ComparisonConfig, TestCase
    from pipeline_executor import DeepsetPipelineExecutor
    from checkpoint_manager import CheckpointManager

    # Create configs
    new_config = PipelineConfig(
        name="new_pipeline",
        pipeline_name="unified_simple",
        workspace_url=os.getenv("DEEPSET_WORKSPACE_URL", ""),
        api_key=os.getenv("DEEPSET_API_KEY", "")
    )

    old_config = PipelineConfig(
        name="old_pipeline",
        pipeline_name="sense_retrieval_no_custom",
        workspace_url=os.getenv("DEEPSET_WORKSPACE_URL", ""),
        api_key=os.getenv("DEEPSET_API_KEY", "")
    )

    comparison_config = ComparisonConfig(
        new_pipeline=new_config,
        old_pipeline=old_config,
        test_data_path="test_cases/sample.csv",
        output_dir="results/test",
        parallel_workers=2
    )

    # Create credentials
    credentials = {
        'solr_url': os.getenv("SOLR_URL", ""),
        'sketch_username': os.getenv("SKETCH_ENGINE_USERNAME", ""),
        'sketch_password': os.getenv("SKETCH_ENGINE_PASSWORD", "")
    }

    # Create executors
    new_executor = DeepsetPipelineExecutor(new_config, credentials)
    old_executor = DeepsetPipelineExecutor(old_config, credentials)

    # Create checkpoint manager
    checkpoint_manager = CheckpointManager("results/checkpoints", "test_run")

    # Create test cases
    test_cases = [
        TestCase("fine_n", "fine_n01_1", "fine", "n"),
        TestCase("fair_n", "fair_n02_3", "fair", "n")
    ]

    # Run comparison
    runner = ParallelComparisonRunner(
        new_executor,
        old_executor,
        comparison_config,
        checkpoint_manager
    )

    results = runner.run(test_cases)
    print(f"\nCompleted: {len(results)} comparisons")
