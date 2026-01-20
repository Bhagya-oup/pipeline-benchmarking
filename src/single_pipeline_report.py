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
                'error_type',
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
                    'error_type': result.metadata.get('error_type', ''),
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
                'error_type': result.metadata.get('error_type', ''),
                'error': result.error or ''
            })

        df = pd.DataFrame(data)

        # Filter out formatter errors for statistics
        valid_df = df[df['error_type'] != 'formatter_error']
        formatter_errors_df = df[df['error_type'] == 'formatter_error']

        # Create Excel writer
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Sheet 1: All results
            df.to_excel(writer, sheet_name='Results', index=False)

            # Sheet 2: Summary statistics (excluding formatter errors)
            avg_quotations_per_case = valid_df['total_quotations'].mean() if len(valid_df) > 0 else 0
            avg_matches_per_case = valid_df['matching_quotations'].mean() if len(valid_df) > 0 else 0
            avg_match_rate_per_case = (avg_matches_per_case / avg_quotations_per_case * 100) if avg_quotations_per_case > 0 else 0

            summary_data = {
                'Metric': [
                    'Total Test Cases',
                    'Valid Cases (excl. all errors)',
                    'Formatter Errors (excluded from stats)',
                    'Pipeline Errors',
                    'Total Quotations',
                    'Total Matching Quotations',
                    'Avg Quotations per Case',
                    'Avg Matches per Case',
                    'Avg Match Rate per Case (%)',
                    'Success Rate (%)',
                    'Avg Response Time (s)'
                ],
                'Value': [
                    len(results),
                    len(valid_df),
                    len(formatter_errors_df),
                    len(df[(df['error'] != '') & (df['error_type'] != 'formatter_error')]),
                    valid_df['total_quotations'].sum(),
                    valid_df['matching_quotations'].sum(),
                    f"{avg_quotations_per_case:.2f}",
                    f"{avg_matches_per_case:.2f}",
                    f"{avg_match_rate_per_case:.1f}%",
                    (len(valid_df) / len(results) * 100 if len(results) > 0 else 0),
                    df['response_time'].mean()
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)

            # Sheet 3: Top performers (highest match counts, excluding formatter errors)
            top_matches = valid_df.nlargest(20, 'matching_quotations')[
                ['entry_ref', 'sense_id', 'word', 'total_quotations', 'matching_quotations', 'match_rate']
            ]
            top_matches.to_excel(writer, sheet_name='Top Matches', index=False)

            # Sheet 4: Zero matches (genuine zero matches, excluding formatter errors)
            zero_matches = valid_df[valid_df['matching_quotations'] == 0][
                ['entry_ref', 'sense_id', 'word', 'total_quotations', 'error']
            ]
            zero_matches.to_excel(writer, sheet_name='Zero Matches', index=False)

            # Sheet 5: Formatter Errors (LLM failures)
            if len(formatter_errors_df) > 0:
                formatter_errors_df[['entry_ref', 'sense_id', 'word', 'error']].to_excel(
                    writer, sheet_name='Formatter Errors', index=False
                )

            # Sheet 6: Other Pipeline Errors
            other_errors = df[(df['error'] != '') & (df['error_type'] != 'formatter_error')][
                ['entry_ref', 'sense_id', 'word', 'error_type', 'error']
            ]
            other_errors.to_excel(writer, sheet_name='Pipeline Errors', index=False)

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

        # Separate formatter errors from other errors
        formatter_errors = [r for r in results if r.metadata.get('error_type') == 'formatter_error']
        other_errors = [r for r in results if r.error and r.metadata.get('error_type') != 'formatter_error']

        # Filter out ALL errors (formatter + other) for match statistics
        valid_results = [r for r in results if not r.error]

        total_quotations = sum(r.metadata.get('total_quotations', 0) for r in valid_results)
        total_matching = sum(r.metadata.get('matching_quotations', 0) for r in valid_results)
        total_errors = len(other_errors)  # Don't count formatter errors here
        total_formatter_errors = len(formatter_errors)
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

            # KEY METRICS SECTION (Highlighted at top)
            f.write("="*80 + "\n")
            f.write("🎯 KEY PERFORMANCE METRICS\n")
            f.write("="*80 + "\n\n")

            # Metric 1: Average Match Rate Per Case
            avg_quotations_per_case = total_quotations/len(valid_results) if valid_results else 0
            avg_match_rate_per_case = (avg_matches/avg_quotations_per_case*100) if avg_quotations_per_case > 0 else 0

            f.write(f"1️⃣  AVERAGE MATCH RATE PER TEST CASE\n")
            f.write(f"    ┌{'─'*76}┐\n")
            f.write(f"    │ 🎯 {avg_matches:.2f} out of {avg_quotations_per_case:.1f} quotations matched per case ({avg_match_rate_per_case:.1f}%){'':>24}│\n")
            f.write(f"    └{'─'*76}┘\n")
            f.write(f"    What this means:\n")
            f.write(f"    • On average, when you query for a word sense, the pipeline returns\n")
            f.write(f"      ~{avg_quotations_per_case:.0f} quotations\n")
            f.write(f"    • Out of those {avg_quotations_per_case:.0f}, approximately {avg_matches:.1f} match the target sense\n")
            f.write(f"    • This is the most important metric for evaluating retrieval quality\n")
            f.write(f"\n")

            # Metric 2: Zero Match Cases
            f.write(f"2️⃣  ZERO MATCH CASES (Cases where no quotations matched)\n")
            f.write(f"    ┌{'─'*76}┐\n")
            if valid_results:
                zero_pct = (zero_matches/len(valid_results)*100)
                status_emoji = "🔴" if zero_pct > 50 else "🟡" if zero_pct > 30 else "🟢"
                f.write(f"    │ {status_emoji} {zero_matches} out of {len(valid_results)} test cases ({zero_pct:.1f}%){'':>37}│\n")
            f.write(f"    └{'─'*76}┘\n")
            f.write(f"    What this means:\n")
            f.write(f"    • These are test cases where the pipeline found 0 matching quotations\n")
            f.write(f"    • Lower is better - indicates pipeline can find matches for most senses\n")
            f.write(f"    • High zero-match rate suggests retrieval or semantic search issues\n")
            f.write(f"\n")

            # Metric 3: Consistency (Coefficient of Variation)
            f.write(f"3️⃣  CONSISTENCY (Coefficient of Variation)\n")
            f.write(f"    ┌{'─'*76}┐\n")
            cv_status_emoji = "🟢" if cv < 80 else "🟡" if cv < 120 else "🔴"
            f.write(f"    │ {cv_status_emoji} CV = {cv:.1f}% (Mean: {avg_matches:.2f}, Std Dev: {std_matches:.2f}){'':>32}│\n")
            f.write(f"    └{'─'*76}┘\n")
            f.write(f"    What this means:\n")
            f.write(f"    • Coefficient of Variation measures performance consistency\n")
            f.write(f"    • Lower CV = more predictable/consistent results across test cases\n")
            f.write(f"    • CV < 80% = Excellent, 80-120% = Good, > 120% = Variable\n")
            if cv < 80:
                f.write(f"    • 🟢 Your pipeline has excellent consistency!\n")
            elif cv < 120:
                f.write(f"    • 🟡 Your pipeline has good consistency\n")
            else:
                f.write(f"    • 🔴 Your pipeline has high variability - some cases perform much better\n")
            f.write(f"\n")

            f.write("="*80 + "\n")
            f.write("📊 DETAILED STATISTICS\n")
            f.write("="*80 + "\n\n")

            f.write(f"Total test cases: {len(results)}\n")
            f.write(f"Valid test cases (excluding ALL errors): {len(valid_results)}\n")
            if total_formatter_errors > 0:
                f.write(f"  - Pipeline errors: {total_errors}\n")
                f.write(f"  - Formatter errors: {total_formatter_errors} (excluded from match stats)\n")
            f.write(f"Total quotations returned: {total_quotations}\n")
            f.write(f"Total matching quotations: {total_matching}\n")
            f.write(f"\n")

            if total_formatter_errors > 0:
                f.write(f"NOTE: Match statistics exclude {total_formatter_errors} formatter error(s)\n")
                f.write(f"      (LLM failed to return classifications for all quotations)\n\n")

            f.write(f"Median matches per test case: {median_matches:.1f}\n")
            f.write(f"Average response time: {avg_response_time:.2f}s\n\n")

            f.write("="*80 + "\n")
            f.write("📈 MATCH DISTRIBUTION (How many cases returned X matches)\n")
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

            # Zero match cases detail
            if zero_matches > 0:
                f.write("="*80 + "\n")
                f.write("❌ ZERO MATCH CASES (Detailed List)\n")
                f.write("="*80 + "\n\n")
                f.write(f"These {zero_matches} test cases found NO matching quotations:\n")
                f.write(f"(These require investigation - possible issues with sense definition,\n")
                f.write(f" corpus coverage, or semantic search)\n\n")

                zero_match_cases = [r for r in valid_results if r.metadata.get('matching_quotations', 0) == 0]
                for idx, r in enumerate(zero_match_cases, 1):
                    f.write(f"  {idx:2d}. {r.test_case.word:15} ({r.test_case.pos:10}) - {r.test_case.entry_ref:20} (sense: {r.test_case.sense_id})\n")
                f.write(f"\n")

            # Perfect match cases detail
            if perfect_matches > 0:
                f.write("="*80 + "\n")
                f.write("🎯 PERFECT MATCH CASES (10/10 quotations matched)\n")
                f.write("="*80 + "\n\n")
                f.write(f"These {perfect_matches} test cases achieved perfect scores:\n\n")

                perfect_match_cases = [
                    r for r in valid_results
                    if r.metadata.get('matching_quotations', 0) == r.metadata.get('total_quotations', 0)
                    and r.metadata.get('total_quotations', 0) > 0
                ]
                for idx, r in enumerate(perfect_match_cases, 1):
                    f.write(f"  {idx}. {r.test_case.word:15} ({r.test_case.pos:10}) - {r.test_case.entry_ref:20} (sense: {r.test_case.sense_id})\n")
                f.write(f"\n")

            f.write("="*80 + "\n")
            f.write("⏱️  EXECUTION TIME\n")
            f.write("="*80 + "\n\n")

            f.write(f"Total execution time: {total_execution_time:.2f} seconds ({total_execution_time/60:.2f} minutes)\n")
            f.write(f"Time per test case: {total_execution_time/len(results):.2f} seconds\n\n" if results else "Time per test case: 0.00 seconds\n\n")

            f.write("="*80 + "\n")
            f.write("🔧 ERRORS AND RELIABILITY\n")
            f.write("="*80 + "\n\n")

            success_count = len(results) - total_errors - total_formatter_errors
            success_rate = (success_count / len(results) * 100) if results else 0
            success_emoji = "🟢" if success_rate == 100 else "🟡" if success_rate >= 95 else "🔴"

            f.write(f"{success_emoji} Success rate: {success_rate:.1f}% ({success_count}/{len(results)} cases)\n\n")

            f.write(f"Error breakdown:\n")
            f.write(f"  • Pipeline errors: {total_errors}\n")
            f.write(f"  • Formatter errors (LLM failures): {total_formatter_errors}\n")
            if total_formatter_errors > 0:
                f.write(f"    ⚠️  NOTE: Formatter errors are EXCLUDED from match statistics\n")
                f.write(f"           (These indicate LLM failed to return all quotation classifications)\n")
            f.write(f"\n")

            if total_formatter_errors > 0:
                f.write(f"📋 Formatter error cases ({total_formatter_errors} total):\n")
                f.write(f"   (LLM did not return classifications for all quotations)\n\n")
                for idx, r in enumerate(formatter_errors, 1):
                    f.write(f"  {idx}. {r.test_case.word:15} ({r.test_case.pos:10}) - {r.test_case.entry_ref:20} (sense: {r.test_case.sense_id})\n")
                f.write(f"\n")

            if total_errors > 0:
                f.write(f"🚨 Pipeline error cases ({total_errors} total):\n\n")
                for idx, r in enumerate(other_errors, 1):
                    f.write(f"  {idx}. {r.test_case.entry_ref} ({r.test_case.sense_id}): {r.error[:100]}\n")
                f.write(f"\n")

            if total_errors == 0 and total_formatter_errors == 0:
                f.write(f"✅ No errors! All {len(results)} test cases completed successfully.\n\n")

        return str(summary_path)
