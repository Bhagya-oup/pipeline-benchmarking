"""
Metrics calculator for pipeline comparison.
"""

from typing import Dict, List
import numpy as np

from .config import PipelineResult, ComparisonResult


class MetricsCalculator:
    """Calculate comparison metrics for pipeline results."""

    def __init__(self, mode: str = 'heuristic'):
        """
        Initialize metrics calculator.

        Args:
            mode: Calculation mode ('heuristic', 'llm', or 'gold_labels')
        """
        self.mode = mode

    def calculate_for_result(self, result: PipelineResult) -> Dict:
        """
        Calculate metrics for a single pipeline result.

        Args:
            result: Pipeline result to analyze

        Returns:
            Dictionary with metrics
        """
        if self.mode == 'heuristic':
            return self._calculate_heuristic(result)
        elif self.mode == 'llm':
            return self._calculate_with_llm(result)
        elif self.mode == 'gold_labels':
            return self._calculate_with_gold_labels(result)
        else:
            raise ValueError(f"Unknown metrics mode: {self.mode}")

    def _calculate_heuristic(self, result: PipelineResult) -> Dict:
        """
        Calculate heuristic metrics based on scores.

        Fast, no external API calls needed.
        """
        quotations = result.quotations

        if not quotations:
            return {
                'num_results': 0,
                'coverage': 0,
                'high_score_count': 0,
                'avg_score': 0.0,
                'max_score': 0.0,
                'min_score': 0.0
            }

        scores = [q.get('score', 0) for q in quotations]
        high_score_count = sum(1 for s in scores if s >= 0.7)

        return {
            'num_results': len(quotations),
            'coverage': 1,  # Binary: found results or not
            'high_score_count': high_score_count,
            'avg_score': float(np.mean(scores)),
            'max_score': float(np.max(scores)),
            'min_score': float(np.min(scores))
        }

    def _calculate_with_llm(self, result: PipelineResult) -> Dict:
        """
        Calculate metrics using LLM verification.

        Slower but more accurate. Requires Azure OpenAI credentials.
        """
        # TODO: Implement LLM verification
        # For now, return heuristic metrics
        print("Warning: LLM verification not yet implemented, using heuristic")
        return self._calculate_heuristic(result)

    def _calculate_with_gold_labels(self, result: PipelineResult) -> Dict:
        """
        Calculate metrics using gold standard labels.

        Ideal if manual annotations are available.
        """
        gold_labels = result.test_case.gold_labels

        if not gold_labels:
            print("Warning: No gold labels provided, using heuristic")
            return self._calculate_heuristic(result)

        predicted_ids = [q.get('quotation_id') or q.get('doc_id') for q in result.quotations]

        true_positives = len(set(predicted_ids) & set(gold_labels))
        false_positives = len(set(predicted_ids) - set(gold_labels))
        false_negatives = len(set(gold_labels) - set(predicted_ids))

        precision = true_positives / len(predicted_ids) if predicted_ids else 0
        recall = true_positives / len(gold_labels) if gold_labels else 0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'num_results': len(predicted_ids)
        }

    def calculate_comparison_metrics(self, comparison: ComparisonResult) -> Dict:
        """
        Calculate comparison metrics between new and old pipeline.

        Args:
            comparison: Comparison result with both pipeline outputs

        Returns:
            Dictionary with comparison metrics
        """
        new_metrics = self.calculate_for_result(comparison.new_result)
        old_metrics = self.calculate_for_result(comparison.old_result)

        # Calculate improvement
        new_count = new_metrics.get('num_results', 0)
        old_count = old_metrics.get('num_results', 0)

        if old_count == 0:
            improvement = "+∞" if new_count > 0 else "0%"
            improvement_pct = float('inf') if new_count > 0 else 0.0
        else:
            improvement_pct = ((new_count - old_count) / old_count) * 100
            improvement = f"{improvement_pct:+.1f}%"

        # Determine winner
        if new_count > old_count:
            winner = 'new'
        elif old_count > new_count:
            winner = 'old'
        else:
            # Tie on count, use avg score as tiebreaker
            new_score = new_metrics.get('avg_score', 0)
            old_score = old_metrics.get('avg_score', 0)
            if new_score > old_score:
                winner = 'new'
            elif old_score > new_score:
                winner = 'old'
            else:
                winner = 'tie'

        return {
            'new_metrics': new_metrics,
            'old_metrics': old_metrics,
            'improvement': improvement,
            'improvement_pct': improvement_pct,
            'winner': winner
        }

    def calculate_for_all(self, results: List[ComparisonResult]) -> List[ComparisonResult]:
        """
        Calculate metrics for all comparison results.

        This enriches the results with calculated metrics.

        Args:
            results: List of comparison results

        Returns:
            Same list (metrics added to metadata)
        """
        for result in results:
            metrics = self.calculate_comparison_metrics(result)

            # Add metrics to metadata
            result.new_result.metadata['calculated_metrics'] = metrics['new_metrics']
            result.old_result.metadata['calculated_metrics'] = metrics['old_metrics']
            result.new_result.metadata['comparison'] = {
                'improvement': metrics['improvement'],
                'winner': metrics['winner']
            }

        return results


# Example usage
if __name__ == "__main__":
    from config import TestCase, PipelineResult, ComparisonResult

    # Create test case
    test_case = TestCase(
        entry_ref="fine_n",
        sense_id="fine_n01_1",
        word="fine",
        pos="n"
    )

    # Create pipeline results
    new_result = PipelineResult(
        test_case=test_case,
        pipeline_name="new_pipeline",
        quotations=[
            {"content": "test1", "score": 0.9},
            {"content": "test2", "score": 0.8},
            {"content": "test3", "score": 0.75}
        ],
        metadata={"response_time": 2.5}
    )

    old_result = PipelineResult(
        test_case=test_case,
        pipeline_name="old_pipeline",
        quotations=[
            {"content": "test1", "score": 0.7}
        ],
        metadata={"response_time": 3.0}
    )

    comparison = ComparisonResult(
        test_case=test_case,
        new_result=new_result,
        old_result=old_result
    )

    # Calculate metrics
    calculator = MetricsCalculator(mode='heuristic')
    metrics = calculator.calculate_comparison_metrics(comparison)

    print("New Pipeline:")
    print(f"  Results: {metrics['new_metrics']['num_results']}")
    print(f"  Avg Score: {metrics['new_metrics']['avg_score']:.3f}")

    print("\nOld Pipeline:")
    print(f"  Results: {metrics['old_metrics']['num_results']}")
    print(f"  Avg Score: {metrics['old_metrics']['avg_score']:.3f}")

    print(f"\nImprovement: {metrics['improvement']}")
    print(f"Winner: {metrics['winner']}")
