"""
Report generator for comparison results (CSV/Excel/text).
"""

import pandas as pd
from pathlib import Path
from typing import List
import numpy as np

from .config import ComparisonResult


class ReportGenerator:
    """Generate comparison reports."""

    def __init__(self):
        """Initialize report generator."""
        pass

    def generate_csv(self, results: List[ComparisonResult], output_path: str):
        """
        Generate CSV report.

        Args:
            results: List of comparison results
            output_path: Path to output CSV file
        """
        rows = []

        for result in results:
            row = {
                'entry_ref': result.test_case.entry_ref,
                'sense_id': result.test_case.sense_id,
                'word': result.test_case.word,
                'pos': result.test_case.pos,

                # New pipeline metrics
                'new_total_quotations': result.new_result.metadata.get('total_quotations', 0),
                'new_matching_quotations': result.new_result.metadata.get('matching_quotations', 0),
                'new_response_time': result.new_result.metadata.get('response_time', 0),
                'new_error': result.new_result.error or '',

                # Old pipeline metrics
                'old_total_quotations': result.old_result.metadata.get('total_quotations', 0),
                'old_matching_quotations': result.old_result.metadata.get('matching_quotations', 0),
                'old_response_time': result.old_result.metadata.get('response_time', 0),
                'old_error': result.old_result.error or '',

                # Comparison
                'improvement': self._calculate_improvement(result),
                'winner': self._determine_winner(result)
            }
            rows.append(row)

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        print(f"CSV report saved: {output_path}")

    def generate_excel(self, results: List[ComparisonResult], output_path: str):
        """
        Generate Excel report with multiple sheets.

        Args:
            results: List of comparison results
            output_path: Path to output Excel file
        """
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Sheet 1: Summary Statistics
            summary_df = self._create_summary_sheet(results)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Sheet 2: Detailed Results
            detailed_df = self._create_detailed_sheet(results)
            detailed_df.to_excel(writer, sheet_name='Detailed Results', index=False)

            # Sheet 3: Top Improvements
            improvements_df = self._create_improvements_sheet(results)
            improvements_df.to_excel(writer, sheet_name='Top Improvements', index=False)

            # Sheet 4: Failures (both pipelines failed)
            failures_df = self._create_failures_sheet(results)
            failures_df.to_excel(writer, sheet_name='Failures', index=False)

            # Sheet 5: New Pipeline Wins
            new_wins_df = self._create_new_wins_sheet(results)
            new_wins_df.to_excel(writer, sheet_name='New Pipeline Wins', index=False)

        print(f"Excel report saved: {output_path}")

    def generate_summary_text(self, results: List[ComparisonResult], output_path: str):
        """
        Generate plain text summary.

        Args:
            results: List of comparison results
            output_path: Path to output text file
        """
        new_successes = sum(1 for r in results if r.new_result.quotations and not r.new_result.error)
        old_successes = sum(1 for r in results if r.old_result.quotations and not r.old_result.error)

        new_wins = sum(1 for r in results if self._determine_winner(r) == 'new')
        old_wins = sum(1 for r in results if self._determine_winner(r) == 'old')
        ties = sum(1 for r in results if self._determine_winner(r) == 'tie')

        new_avg_matches = np.mean([len(r.new_result.quotations) for r in results])
        old_avg_matches = np.mean([len(r.old_result.quotations) for r in results])

        new_avg_time = np.mean([r.new_result.metadata.get('response_time', 0) for r in results])
        old_avg_time = np.mean([r.old_result.metadata.get('response_time', 0) for r in results])

        summary = f"""
{'='*80}
PIPELINE COMPARISON SUMMARY
{'='*80}

Total Test Cases: {len(results)}

Success Rates:
  New Pipeline: {new_successes}/{len(results)} ({new_successes/len(results)*100:.1f}%)
  Old Pipeline: {old_successes}/{len(results)} ({old_successes/len(results)*100:.1f}%)

Head-to-Head Comparison:
  New Pipeline Wins: {new_wins}
  Old Pipeline Wins: {old_wins}
  Ties: {ties}

Average Results per Test Case:
  New Pipeline: {new_avg_matches:.1f} quotations
  Old Pipeline: {old_avg_matches:.1f} quotations

Performance:
  New Pipeline Avg Response Time: {new_avg_time:.2f}s
  Old Pipeline Avg Response Time: {old_avg_time:.2f}s

{'='*80}
"""

        Path(output_path).write_text(summary)
        print(summary)
        print(f"Summary saved: {output_path}")

    def _avg_score(self, quotations: List[dict]) -> float:
        """Calculate average score."""
        if not quotations:
            return 0.0
        scores = [q.get('score', 0) for q in quotations]
        return float(np.mean(scores)) if scores else 0.0

    def _calculate_improvement(self, result: ComparisonResult) -> str:
        """Calculate improvement percentage."""
        new_count = len(result.new_result.quotations)
        old_count = len(result.old_result.quotations)

        if old_count == 0:
            return "+∞" if new_count > 0 else "0%"

        improvement = ((new_count - old_count) / old_count) * 100
        return f"{improvement:+.1f}%"

    def _determine_winner(self, result: ComparisonResult) -> str:
        """Determine which pipeline performed better."""
        new_count = len(result.new_result.quotations)
        old_count = len(result.old_result.quotations)

        if new_count > old_count:
            return 'new'
        elif old_count > new_count:
            return 'old'
        else:
            return 'tie'

    def _create_summary_sheet(self, results: List[ComparisonResult]) -> pd.DataFrame:
        """Create summary statistics sheet."""
        new_successes = sum(1 for r in results if r.new_result.quotations and not r.new_result.error)
        old_successes = sum(1 for r in results if r.old_result.quotations and not r.old_result.error)

        new_wins = sum(1 for r in results if self._determine_winner(r) == 'new')
        old_wins = sum(1 for r in results if self._determine_winner(r) == 'old')
        ties = sum(1 for r in results if self._determine_winner(r) == 'tie')

        data = {
            'Metric': [
                'Total Test Cases',
                'New Pipeline Success Rate',
                'Old Pipeline Success Rate',
                'New Pipeline Wins',
                'Old Pipeline Wins',
                'Ties',
                'Avg New Pipeline Matches',
                'Avg Old Pipeline Matches',
                'Avg New Pipeline Response Time',
                'Avg Old Pipeline Response Time'
            ],
            'Value': [
                len(results),
                f"{new_successes}/{len(results)} ({new_successes/len(results)*100:.1f}%)",
                f"{old_successes}/{len(results)} ({old_successes/len(results)*100:.1f}%)",
                new_wins,
                old_wins,
                ties,
                f"{np.mean([len(r.new_result.quotations) for r in results]):.1f}",
                f"{np.mean([len(r.old_result.quotations) for r in results]):.1f}",
                f"{np.mean([r.new_result.metadata.get('response_time', 0) for r in results]):.2f}s",
                f"{np.mean([r.old_result.metadata.get('response_time', 0) for r in results]):.2f}s"
            ]
        }

        return pd.DataFrame(data)

    def _create_detailed_sheet(self, results: List[ComparisonResult]) -> pd.DataFrame:
        """Create detailed results sheet."""
        rows = []
        for result in results:
            rows.append({
                'entry_ref': result.test_case.entry_ref,
                'sense_id': result.test_case.sense_id,
                'word': result.test_case.word,
                'pos': result.test_case.pos,
                'new_matches': len(result.new_result.quotations),
                'old_matches': len(result.old_result.quotations),
                'new_avg_score': self._avg_score(result.new_result.quotations),
                'old_avg_score': self._avg_score(result.old_result.quotations),
                'improvement': self._calculate_improvement(result),
                'winner': self._determine_winner(result),
                'new_error': result.new_result.error or '',
                'old_error': result.old_result.error or ''
            })
        return pd.DataFrame(rows)

    def _create_improvements_sheet(self, results: List[ComparisonResult]) -> pd.DataFrame:
        """Create sheet showing top improvements."""
        rows = []
        for result in results:
            new_count = len(result.new_result.quotations)
            old_count = len(result.old_result.quotations)
            diff = new_count - old_count

            if diff > 0:  # Only improvements
                rows.append({
                    'sense_id': result.test_case.sense_id,
                    'word': result.test_case.word,
                    'new_matches': new_count,
                    'old_matches': old_count,
                    'difference': diff,
                    'improvement': self._calculate_improvement(result)
                })

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values('difference', ascending=False).head(50)
        return df

    def _create_failures_sheet(self, results: List[ComparisonResult]) -> pd.DataFrame:
        """Create sheet showing cases where both failed."""
        failures = [
            r for r in results
            if (r.new_result.error or not r.new_result.quotations) and
               (r.old_result.error or not r.old_result.quotations)
        ]

        rows = []
        for result in failures:
            rows.append({
                'sense_id': result.test_case.sense_id,
                'word': result.test_case.word,
                'new_error': result.new_result.error or 'No results',
                'old_error': result.old_result.error or 'No results'
            })

        return pd.DataFrame(rows)

    def _create_new_wins_sheet(self, results: List[ComparisonResult]) -> pd.DataFrame:
        """Create sheet showing cases where new pipeline won."""
        wins = [r for r in results if self._determine_winner(r) == 'new']

        rows = []
        for result in wins:
            rows.append({
                'sense_id': result.test_case.sense_id,
                'word': result.test_case.word,
                'new_matches': len(result.new_result.quotations),
                'old_matches': len(result.old_result.quotations),
                'difference': len(result.new_result.quotations) - len(result.old_result.quotations),
                'improvement': self._calculate_improvement(result)
            })

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values('difference', ascending=False)
        return df


# Example usage
if __name__ == "__main__":
    from config import TestCase, PipelineResult, ComparisonResult

    # Create mock results
    test_case = TestCase("fine_n", "fine_n01_1", "fine", "n")

    new_result = PipelineResult(
        test_case=test_case,
        pipeline_name="new_pipeline",
        quotations=[{"content": "test", "score": 0.9}] * 15,
        metadata={"response_time": 2.5}
    )

    old_result = PipelineResult(
        test_case=test_case,
        pipeline_name="old_pipeline",
        quotations=[{"content": "test", "score": 0.7}] * 8,
        metadata={"response_time": 3.0}
    )

    comparison = ComparisonResult(test_case, new_result, old_result)

    # Generate reports
    generator = ReportGenerator()
    generator.generate_csv([comparison], "test_report.csv")
    generator.generate_summary_text([comparison], "test_summary.txt")
    print("Reports generated successfully!")
