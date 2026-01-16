#!/usr/bin/env python3
"""
Single Pipeline Benchmarking Tool

Runs ONE pipeline against test cases and reports matching quotations.
Can be run multiple times with different pipelines for comparison.

Usage:
    python benchmark_pipeline.py \
        --pipeline hybrid_bm25_cosine_reranker_with_original_input_json \
        --test-data test_cases/sample.csv \
        --output results/hybrid_run_1 \
        --workers 8

    python benchmark_pipeline.py \
        --pipeline oed-quotations \
        --test-data test_cases/sample.csv \
        --output results/base_run_1 \
        --workers 8
"""

import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import PipelineConfig, ComparisonConfig
from src.test_case_loader import load_test_cases
from src.pipeline_executor import DeepsetPipelineExecutor
from src.checkpoint_manager import CheckpointManager
from src.single_pipeline_runner import SinglePipelineRunner
from src.single_pipeline_report import SinglePipelineReportGenerator


def main():
    parser = argparse.ArgumentParser(
        description='Benchmark a single Deepset pipeline against test cases'
    )

    parser.add_argument(
        '--pipeline',
        required=True,
        help='Pipeline name in Deepset Cloud (e.g., oed-quotations)'
    )

    parser.add_argument(
        '--test-data',
        required=True,
        help='Path to test cases CSV file'
    )

    parser.add_argument(
        '--output',
        required=False,
        default=None,
        help='Output directory for results (default: auto-generated from pipeline name and timestamp)'
    )

    parser.add_argument(
        '--workers',
        type=int,
        default=4,
        help='Number of parallel workers (default: 4)'
    )

    parser.add_argument(
        '--rate-limit',
        type=int,
        default=60,
        help='API calls per minute (default: 60)'
    )

    parser.add_argument(
        '--checkpoint-interval',
        type=int,
        default=10,
        help='Save checkpoint every N test cases (default: 10)'
    )

    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from checkpoint if exists'
    )

    parser.add_argument(
        '--input-format',
        choices=['deepset_search', 'simple_query'],
        default='deepset_search',
        help='Input format for pipeline (default: deepset_search)'
    )

    parser.add_argument(
        '--endpoint',
        choices=['search', 'run'],
        default='search',
        help='API endpoint to use (default: search)'
    )

    args = parser.parse_args()

    # Load environment variables from scripts/.env
    env_path = Path(__file__).parent.parent / 'scripts' / '.env'
    if not env_path.exists():
        print(f"Error: .env file not found at {env_path}")
        print("Please ensure DEEPSET_API_KEY and DEEPSET_WORKSPACE are set")
        sys.exit(1)

    load_dotenv(env_path)

    # Get credentials
    api_key = os.getenv('DEEPSET_API_KEY')
    workspace = os.getenv('DEEPSET_WORKSPACE')

    if not api_key or not workspace:
        print("Error: Missing credentials in .env file")
        print("Required: DEEPSET_API_KEY, DEEPSET_WORKSPACE")
        sys.exit(1)

    # Construct Deepset Cloud API URL
    workspace_url = f"https://api.cloud.deepset.ai/api/v1/workspaces/{workspace}"

    # Auto-generate output directory if not provided
    if args.output is None:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        # Simplify pipeline name for folder (remove long prefixes)
        pipeline_folder_name = args.pipeline.replace('_bm25_cosine_reranker_with_original_input_json', '')
        args.output = f"results/{pipeline_folder_name}_{timestamp}"

    print("="*80)
    print("PIPELINE BENCHMARKING TOOL")
    print("="*80)
    print(f"Pipeline: {args.pipeline}")
    print(f"Test data: {args.test_data}")
    print(f"Output: {args.output}")
    print(f"Workers: {args.workers}")
    print(f"="*80)
    print()

    # Load test cases
    print("Loading test cases...")
    test_cases = load_test_cases(args.test_data)
    print(f"Loaded {len(test_cases)} test cases\n")

    if not test_cases:
        print("Error: No test cases loaded!")
        sys.exit(1)

    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create pipeline config
    pipeline_config = PipelineConfig(
        name=args.pipeline,
        pipeline_name=args.pipeline,
        workspace_url=workspace_url,
        api_key=api_key,
        input_format=args.input_format,
        endpoint=args.endpoint
    )

    # Create comparison config (reusing for single pipeline)
    comparison_config = ComparisonConfig(
        new_pipeline=pipeline_config,  # Using "new" as the single pipeline
        old_pipeline=pipeline_config,  # Dummy, won't be used
        test_data_path=args.test_data,
        output_dir=str(output_dir),
        parallel_workers=args.workers,
        rate_limit_per_minute=args.rate_limit,
        checkpoint_interval=args.checkpoint_interval
    )

    # Create executor
    credentials = {'deepset_api_key': api_key}
    executor = DeepsetPipelineExecutor(pipeline_config, credentials)

    # Create checkpoint manager
    checkpoint_dir = output_dir / 'checkpoints'
    checkpoint_dir.mkdir(exist_ok=True)
    run_id = f"{args.pipeline}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    checkpoint_manager = CheckpointManager(str(checkpoint_dir), run_id)

    # Create runner
    runner = SinglePipelineRunner(
        executor=executor,
        config=comparison_config,
        checkpoint_manager=checkpoint_manager
    )

    # Run benchmarking
    print("Starting benchmarking...")
    print()

    results = runner.run(test_cases)

    print()
    print("="*80)
    print("GENERATING REPORTS")
    print("="*80)

    # Generate reports
    report_generator = SinglePipelineReportGenerator(str(output_dir))

    csv_path = report_generator.generate_csv(results, args.pipeline)
    excel_path = report_generator.generate_excel(results, args.pipeline)
    summary_path = report_generator.generate_summary(results, args.pipeline)

    print(f"✓ CSV report: {csv_path}")
    print(f"✓ Excel report: {excel_path}")
    print(f"✓ Summary: {summary_path}")

    print()
    print("="*80)
    print("SUMMARY STATISTICS")
    print("="*80)

    # Quick summary
    total_quotations = sum(r.metadata.get('total_quotations', 0) for r in results)
    total_matching = sum(r.metadata.get('matching_quotations', 0) for r in results)
    total_errors = sum(1 for r in results if r.error)

    print(f"Total test cases: {len(results)}")
    print(f"Total quotations returned: {total_quotations}")
    print(f"Total matching quotations: {total_matching}")
    if total_quotations > 0:
        print(f"Match rate: {total_matching/total_quotations*100:.1f}%")
    print(f"Errors: {total_errors}")
    print()
    print(f"Average quotations per test case: {total_quotations/len(results):.1f}")
    print(f"Average matches per test case: {total_matching/len(results):.1f}")

    print()
    print("="*80)
    print("BENCHMARKING COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
