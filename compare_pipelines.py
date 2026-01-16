#!/usr/bin/env python3
"""
Pipeline Comparison Tool

Compare two pipelines on the same test dataset with comprehensive metrics.
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

from src.config import PipelineConfig, ComparisonConfig
from src.test_case_loader import load_test_cases
from src.pipeline_executor import DeepsetPipelineExecutor
from src.parallel_runner import ParallelComparisonRunner
from src.checkpoint_manager import CheckpointManager
from src.metrics_calculator import MetricsCalculator
from src.report_generator import ReportGenerator

# Load environment variables from scripts/.env
env_path = Path(__file__).parent.parent / 'scripts' / '.env'
load_dotenv(env_path)


def load_credentials_from_env() -> dict:
    """Load API credentials from environment variables."""
    required = [
        'DEEPSET_API_KEY',
        'DEEPSET_WORKSPACE'
    ]

    credentials = {}
    missing = []

    for key in required:
        value = os.getenv(key)
        if not value:
            missing.append(key)
        credentials[key.lower()] = value

    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("\nSet these in your .env file or environment:")
        for key in missing:
            print(f"  {key}=your_value_here")
        print("\nNote: The Deepset pipeline handles Solr/Hero API calls internally.")
        sys.exit(1)

    return credentials


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Compare two pipelines on the same test dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic comparison
  python compare_pipelines.py --test-data data.csv --new-pipeline unified_simple --old-pipeline sense_retrieval_no_custom

  # Resume from checkpoint
  python compare_pipelines.py --test-data data.csv --new-pipeline unified_simple --old-pipeline sense_retrieval_no_custom --resume

  # Quick mode (heuristic metrics only)
  python compare_pipelines.py --test-data data.csv --new-pipeline unified_simple --old-pipeline sense_retrieval_no_custom --quick

  # More workers for faster execution
  python compare_pipelines.py --test-data data.csv --new-pipeline unified_simple --old-pipeline sense_retrieval_no_custom --workers 8
        """
    )

    parser.add_argument('--test-data', required=True, help='Path to test data file (CSV/JSON/TXT)')
    parser.add_argument('--new-pipeline', required=True, help='New pipeline name in Deepset Cloud')
    parser.add_argument('--old-pipeline', required=True, help='Old pipeline name in Deepset Cloud')
    parser.add_argument('--output', default='results', help='Output directory (default: results/)')
    parser.add_argument('--workers', type=int, default=4, help='Number of parallel workers (default: 4)')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--clear-checkpoint', action='store_true', help='Clear checkpoint and start fresh')
    parser.add_argument('--quick', action='store_true', help='Quick mode (heuristic metrics only)')

    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()

    print("="*80)
    print("PIPELINE COMPARISON TOOL")
    print("="*80)
    print(f"Test Data: {args.test_data}")
    print(f"New Pipeline: {args.new_pipeline}")
    print(f"Old Pipeline: {args.old_pipeline}")
    print(f"Output: {args.output}")
    print(f"Workers: {args.workers}")
    print("="*80)

    # 1. Load credentials
    print("\n[1/8] Loading credentials from environment...")
    credentials = load_credentials_from_env()
    print("✓ Credentials loaded")

    # 2. Load test cases
    print(f"\n[2/8] Loading test cases from {args.test_data}...")
    test_cases = load_test_cases(args.test_data)
    print(f"✓ Loaded {len(test_cases)} test cases")

    # 3. Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 4. Initialize pipeline configurations
    print("\n[3/8] Initializing pipeline configurations...")

    # Construct proper Deepset Cloud API URL
    workspace = credentials['deepset_workspace']
    api_base = "https://api.cloud.deepset.ai"

    new_config = PipelineConfig(
        name="new_pipeline",
        pipeline_name=args.new_pipeline,
        workspace_url=f"{api_base}/api/v1/workspaces/{workspace}",
        api_key=credentials['deepset_api_key']
    )

    old_config = PipelineConfig(
        name="old_pipeline",
        pipeline_name=args.old_pipeline,
        workspace_url=f"{api_base}/api/v1/workspaces/{workspace}",
        api_key=credentials['deepset_api_key']
    )

    comparison_config = ComparisonConfig(
        new_pipeline=new_config,
        old_pipeline=old_config,
        test_data_path=args.test_data,
        output_dir=str(output_dir),
        parallel_workers=args.workers,
        metrics_mode='heuristic' if args.quick else 'heuristic'
    )
    print("✓ Configurations initialized")

    # 5. Initialize components
    print("\n[4/8] Initializing executors and checkpoint manager...")
    new_executor = DeepsetPipelineExecutor(new_config, credentials)
    old_executor = DeepsetPipelineExecutor(old_config, credentials)

    checkpoint_manager = CheckpointManager(
        checkpoint_dir=str(output_dir / 'checkpoints'),
        run_id=timestamp
    )

    if args.clear_checkpoint:
        checkpoint_manager.clear()

    runner = ParallelComparisonRunner(
        new_executor=new_executor,
        old_executor=old_executor,
        config=comparison_config,
        checkpoint_manager=checkpoint_manager
    )
    print("✓ Components initialized")

    # 6. Run comparison
    print("\n[5/8] Starting comparison...")
    results = runner.run(test_cases)
    print(f"\n✓ Comparison complete! Processed {len(results)} test cases")

    # 7. Calculate metrics
    print("\n[6/8] Calculating metrics...")
    metrics_calculator = MetricsCalculator(
        mode=comparison_config.metrics_mode
    )
    enriched_results = metrics_calculator.calculate_for_all(results)
    print("✓ Metrics calculated")

    # 8. Generate reports
    print("\n[7/8] Generating reports...")
    report_generator = ReportGenerator()

    csv_path = str(output_dir / f'comparison_{timestamp}.csv')
    excel_path = str(output_dir / f'comparison_{timestamp}.xlsx')
    summary_path = str(output_dir / f'summary_{timestamp}.txt')

    report_generator.generate_csv(enriched_results, csv_path)
    report_generator.generate_excel(enriched_results, excel_path)
    report_generator.generate_summary_text(enriched_results, summary_path)

    print("\n[8/8] Complete!")
    print("\n" + "="*80)
    print("COMPARISON COMPLETE!")
    print("="*80)
    print(f"Results saved to: {output_dir}/")
    print(f"  - CSV: comparison_{timestamp}.csv")
    print(f"  - Excel: comparison_{timestamp}.xlsx")
    print(f"  - Summary: summary_{timestamp}.txt")
    print("="*80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved to checkpoint.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
