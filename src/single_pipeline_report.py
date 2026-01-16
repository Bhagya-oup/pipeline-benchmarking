"""
Report generator for single pipeline benchmarking results.
"""

import csv
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import List

from .config import PipelineResult


class SinglePipelineReportGenerator:
    """Generate reports for single pipeline benchmarking."""

    def __init__(self, output_dir: str):
        """
        Initialize report generator.

        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_csv(self, results: List[PipelineResult], pipeline_name: str) -> str:
        """
        Generate CSV report.

        Args:
            results: List of pipeline results
            pipeline_name: Name of the pipeline

        Returns:
            Path to generated CSV file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_path = self.output_dir / f"{pipeline_name}_{timestamp}.csv"

        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'entry_ref',
                'sense_id',
                'word',
                'pos',
                'total_quotations',
                'matching_quotations',
                'response_time',
                'error'
            ])

            writer.writeheader()

            for result in results:
                row = {
                    'entry_ref': result.test_case.entry_ref,
                    'sense_id': result.test_case.sense_id,
                    'word': result.test_case.word,
                    'pos': result.test_case.pos,
                    'total_quotations': result.metadata.get('total_quotations', 0),
                    'matching_quotations': result.metadata.get('matching_quotations', 0),
                    'response_time': result.metadata.get('response_time', 0),
                    'error': result.error or ''
                }
                writer.writerow(row)

        return str(csv_path)

    def generate_excel(self, results: List[PipelineResult], pipeline_name: str) -> str:
        """
        Generate Excel report with summary statistics.

        Args:
            results: List of pipeline results
            pipeline_name: Name of the pipeline

        Returns:
            Path to generated Excel file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        excel_path = self.output_dir / f"{pipeline_name}_{timestamp}.xlsx"

        # Create DataFrame from results
        data = []
        for result in results:
            data.append({
                'entry_ref': result.test_case.entry_ref,
                'sense_id': result.test_case.sense_id,
                'word': result.test_case.word,
                'pos': result.test_case.pos,
                'total_quotations': result.metadata.get('total_quotations', 0),
                'matching_quotations': result.metadata.get('matching_quotations', 0),
                'match_rate': (
                    result.metadata.get('matching_quotations', 0) /
                    result.metadata.get('total_quotations', 1)
                    if result.metadata.get('total_quotations', 0) > 0 else 0
                ),
                'response_time': result.metadata.get('response_time', 0),
                'error': result.error or ''
            })

        df = pd.DataFrame(data)

        # Create Excel writer
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Sheet 1: All results
            df.to_excel(writer, sheet_name='Results', index=False)

            # Sheet 2: Summary statistics
            summary_data = {
                'Metric': [
                    'Total Test Cases',
                    'Total Quotations',
                    'Total Matching Quotations',
                    'Overall Match Rate (%)',
                    'Avg Quotations per Case',
                    'Avg Matches per Case',
                    'Errors',
                    'Success Rate (%)',
                    'Avg Response Time (s)'
                ],
                'Value': [
                    len(results),
                    df['total_quotations'].sum(),
                    df['matching_quotations'].sum(),
                    (df['matching_quotations'].sum() / df['total_quotations'].sum() * 100
                     if df['total_quotations'].sum() > 0 else 0),
                    df['total_quotations'].mean(),
                    df['matching_quotations'].mean(),
                    df['error'].notna().sum(),
                    ((len(results) - df['error'].notna().sum()) / len(results) * 100),
                    df['response_time'].mean()
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Sheet 3: Top performers (highest match counts)
            top_matches = df.nlargest(20, 'matching_quotations')[
                ['entry_ref', 'sense_id', 'word', 'total_quotations', 'matching_quotations', 'match_rate']
            ]
            top_matches.to_excel(writer, sheet_name='Top Matches', index=False)

            # Sheet 4: Zero matches (cases that need investigation)
            zero_matches = df[df['matching_quotations'] == 0][
                ['entry_ref', 'sense_id', 'word', 'total_quotations', 'error']
            ]
            zero_matches.to_excel(writer, sheet_name='Zero Matches', index=False)

            # Sheet 5: Errors
            errors = df[df['error'] != ''][
                ['entry_ref', 'sense_id', 'word', 'error']
            ]
            errors.to_excel(writer, sheet_name='Errors', index=False)

        return str(excel_path)

    def generate_summary(self, results: List[PipelineResult], pipeline_name: str) -> str:
        """
        Generate text summary report.

        Args:
            results: List of pipeline results
            pipeline_name: Name of the pipeline

        Returns:
            Path to generated summary file
        """
        import numpy as np

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary_path = self.output_dir / f"{pipeline_name}_{timestamp}_summary.txt"

        # Filter out error cases for metrics
        valid_results = [r for r in results if not r.error]

        total_quotations = sum(r.metadata.get('total_quotations', 0) for r in valid_results)
        total_matching = sum(r.metadata.get('matching_quotations', 0) for r in valid_results)
        total_errors = sum(1 for r in results if r.error)
        avg_response_time = sum(r.metadata.get('response_time', 0) for r in results) / len(results) if results else 0

        # Get total execution time (same for all results)
        total_execution_time = results[0].metadata.get('total_execution_time', 0) if results else 0

        # Count cases by match distribution
        zero_matches = sum(1 for r in valid_results if r.metadata.get('matching_quotations', 0) == 0)
        at_least_1 = sum(1 for r in valid_results if r.metadata.get('matching_quotations', 0) >= 1)
        at_least_2 = sum(1 for r in valid_results if r.metadata.get('matching_quotations', 0) >= 2)
        at_least_3 = sum(1 for r in valid_results if r.metadata.get('matching_quotations', 0) >= 3)
        greater_than_5 = sum(1 for r in valid_results if r.metadata.get('matching_quotations', 0) > 5)

        perfect_matches = sum(
            1 for r in valid_results
            if r.metadata.get('matching_quotations', 0) == r.metadata.get('total_quotations', 0)
            and r.metadata.get('total_quotations', 0) > 0
        )

        # Calculate consistency metrics
        matches_per_case = [r.metadata.get('matching_quotations', 0) for r in valid_results]
        avg_matches = np.mean(matches_per_case) if matches_per_case else 0
        std_matches = np.std(matches_per_case, ddof=1) if len(matches_per_case) > 1 else 0
        cv = (std_matches / avg_matches * 100) if avg_matches > 0 else 0
        median_matches = np.median(matches_per_case) if matches_per_case else 0

        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write(f"PIPELINE BENCHMARKING SUMMARY\n")
            f.write("="*80 + "\n\n")

            f.write(f"Pipeline: {pipeline_name}\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            f.write("="*80 + "\n")
            f.write("OVERALL STATISTICS\n")
            f.write("="*80 + "\n\n")

            f.write(f"Total test cases: {len(results)}\n")
            f.write(f"Valid test cases (excluding errors): {len(valid_results)}\n")
            f.write(f"Total quotations returned: {total_quotations}\n")
            f.write(f"Total matching quotations: {total_matching}\n")
            if total_quotations > 0:
                f.write(f"Overall match rate: {total_matching/total_quotations*100:.1f}%\n")
            f.write(f"\n")

            f.write(f"Average quotations per test case: {total_quotations/len(valid_results):.2f}\n" if valid_results else "Average quotations per test case: 0.00\n")
            f.write(f"Average matches per test case: {avg_matches:.2f}\n")
            f.write(f"Median matches per test case: {median_matches:.1f}\n")
            f.write(f"Average response time: {avg_response_time:.2f}s\n\n")

            f.write("="*80 + "\n")
            f.write("MATCH DISTRIBUTION (How many cases returned X matches)\n")
            f.write("="*80 + "\n\n")

            if valid_results:
                total_valid = len(valid_results)
                f.write(f"⚠️  ZERO MATCHES (0):        {zero_matches:3d} cases ({zero_matches/total_valid*100:5.1f}%)\n")
                f.write(f"✅ AT LEAST 1 MATCH (≥1):   {at_least_1:3d} cases ({at_least_1/total_valid*100:5.1f}%)\n")
                f.write(f"   At least 2 matches (≥2):  {at_least_2:3d} cases ({at_least_2/total_valid*100:5.1f}%)\n")
                f.write(f"   At least 3 matches (≥3):  {at_least_3:3d} cases ({at_least_3/total_valid*100:5.1f}%)\n")
                f.write(f"   Greater than 5 (>5):      {greater_than_5:3d} cases ({greater_than_5/total_valid*100:5.1f}%)\n")
                f.write(f"   Perfect matches (100%):   {perfect_matches:3d} cases ({perfect_matches/total_valid*100:5.1f}%)\n")
            f.write(f"\n")

            f.write("="*80 + "\n")
            f.write("CONSISTENCY METRICS\n")
            f.write("="*80 + "\n\n")

            f.write(f"Mean matches per case:             {avg_matches:.2f}\n")
            f.write(f"Standard deviation:                {std_matches:.2f}\n")
            f.write(f"Coefficient of variation (CV):    {cv:.1f}%\n")
            f.write(f"  (Lower CV = more consistent/predictable performance)\n\n")

            f.write("="*80 + "\n")
            f.write("EXECUTION TIME\n")
            f.write("="*80 + "\n\n")

            f.write(f"Total execution time: {total_execution_time:.2f} seconds ({total_execution_time/60:.2f} minutes)\n")
            f.write(f"Time per test case: {total_execution_time/len(results):.2f} seconds\n\n" if results else "Time per test case: 0.00 seconds\n\n")

            f.write("="*80 + "\n")
            f.write("ERRORS\n")
            f.write("="*80 + "\n\n")

            f.write(f"Total errors: {total_errors}\n")
            f.write(f"Success rate: {(len(results) - total_errors) / len(results) * 100:.1f}%\n\n" if results else "Success rate: 0.0%\n\n")

            if total_errors > 0:
                f.write("Error cases:\n")
                for r in results:
                    if r.error:
                        f.write(f"  - {r.test_case.entry_ref} ({r.test_case.sense_id}): {r.error[:100]}\n")

        return str(summary_path)
