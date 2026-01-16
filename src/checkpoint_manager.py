"""
Checkpoint manager for resumable execution.
"""

import pickle
from pathlib import Path
from typing import List, Set, Union

from .config import ComparisonResult, PipelineResult


class CheckpointManager:
    """Manage checkpoints for resumable execution."""

    def __init__(self, checkpoint_dir: str, run_id: str):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
            run_id: Unique identifier for this run
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_file = self.checkpoint_dir / f"checkpoint_{run_id}.pkl"
        self.results: List[Union[ComparisonResult, PipelineResult]] = []

        # Load existing checkpoint if present
        if self.checkpoint_file.exists():
            print(f"Found existing checkpoint: {self.checkpoint_file.name}")
            self.load()

    def save(self, results: List[Union[ComparisonResult, PipelineResult]]):
        """
        Save current results to checkpoint.

        Args:
            results: List of results to save (ComparisonResult or PipelineResult)
        """
        self.results = results

        with open(self.checkpoint_file, 'wb') as f:
            pickle.dump(results, f)

        # Don't print here - SinglePipelineRunner will print

    def load(self) -> List[Union[ComparisonResult, PipelineResult]]:
        """
        Load results from checkpoint.

        Returns:
            List of results from checkpoint
        """
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'rb') as f:
                    self.results = pickle.load(f)
                print(f"  → Loaded {len(self.results)} results from checkpoint")
            except Exception as e:
                print(f"  → Warning: Failed to load checkpoint: {e}")
                self.results = []

        return self.results

    def get_completed_ids(self) -> Set[str]:
        """
        Get set of completed sense IDs.

        Returns:
            Set of sense_ids that have been completed
        """
        completed = set()
        for r in self.results:
            # Handle both ComparisonResult and PipelineResult
            if hasattr(r, 'test_case'):
                completed.add(r.test_case.sense_id)
        return completed

    def clear(self):
        """Clear checkpoint (start fresh)."""
        if self.checkpoint_file.exists():
            self.checkpoint_file.unlink()
            print(f"Checkpoint cleared: {self.checkpoint_file.name}")
        self.results = []

    def get_checkpoint_info(self) -> dict:
        """
        Get information about current checkpoint.

        Returns:
            Dictionary with checkpoint statistics
        """
        return {
            'exists': self.checkpoint_file.exists(),
            'file': str(self.checkpoint_file),
            'num_completed': len(self.results),
            'completed_ids': self.get_completed_ids()
        }


# Example usage
if __name__ == "__main__":
    from config import TestCase, PipelineResult, ComparisonResult, PipelineConfig

    # Create sample checkpoint
    checkpoint_dir = "results/checkpoints"
    run_id = "test_run_001"

    manager = CheckpointManager(checkpoint_dir, run_id)

    # Create mock results
    test_case = TestCase(
        entry_ref="fine_n",
        sense_id="fine_n01_1",
        word="fine",
        pos="n"
    )

    pipeline_result = PipelineResult(
        test_case=test_case,
        pipeline_name="new_pipeline",
        quotations=[{"content": "test", "score": 0.9}],
        metadata={"response_time": 2.5}
    )

    comparison_result = ComparisonResult(
        test_case=test_case,
        new_result=pipeline_result,
        old_result=pipeline_result
    )

    # Save checkpoint
    manager.save([comparison_result])

    # Load checkpoint
    loaded = manager.load()
    print(f"Loaded {len(loaded)} results")

    # Get info
    info = manager.get_checkpoint_info()
    print(f"Checkpoint info: {info}")

    # Clear
    manager.clear()
