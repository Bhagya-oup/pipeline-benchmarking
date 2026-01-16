# Single Pipeline Benchmarking Tool

## Overview

This tool runs **one pipeline** at a time against test cases and reports how many quotations match the input sense_id. You can run it multiple times with different pipelines and compare the results.

## Quick Start

### 1. Run First Pipeline (e.g., Base Pipeline)

```bash
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/sample.csv \
    --output results/base_run \
    --workers 8
```

### 2. Run Second Pipeline (e.g., Hybrid Pipeline)

```bash
python benchmark_pipeline.py \
    --pipeline hybrid_bm25_cosine_reranker_with_original_input_json \
    --test-data test_cases/sample.csv \
    --output results/hybrid_run \
    --workers 8
```

### 3. Compare Results

Compare the CSV files manually or use a simple comparison script:

```bash
# View results side by side
diff results/base_run/oed-quotations_*.csv results/hybrid_run/hybrid_*.csv

# Or use pandas for analysis
python compare_csv_results.py results/base_run/*.csv results/hybrid_run/*.csv
```

## Output Files

Each run generates:

1. **CSV Report** (`{pipeline_name}_{timestamp}.csv`)
   - Columns: `entry_ref`, `sense_id`, `word`, `pos`, `total_quotations`, `matching_quotations`, `response_time`, `error`
   - One row per test case

2. **Excel Report** (`{pipeline_name}_{timestamp}.xlsx`)
   - Sheet 1: All results
   - Sheet 2: Summary statistics
   - Sheet 3: Top matches (highest match counts)
   - Sheet 4: Zero matches (cases needing investigation)
   - Sheet 5: Errors

3. **Text Summary** (`{pipeline_name}_{timestamp}_summary.txt`)
   - Overall statistics
   - Match quality breakdown
   - Error summary

## Command Line Options

```
--pipeline PIPELINE_NAME         Required. Pipeline name in Deepset Cloud
--test-data PATH                 Required. Path to test cases CSV file
--output DIR                     Required. Output directory for results
--workers N                      Optional. Number of parallel workers (default: 4)
--rate-limit N                   Optional. API calls per minute (default: 60)
--checkpoint-interval N          Optional. Save checkpoint every N cases (default: 10)
--resume                         Optional. Resume from checkpoint if exists
```

## Test Data Format

CSV file with columns:
```csv
entry_ref,sense_id,word,pos
aaron_n2,12884176,aaron,noun
aaronical_adj,10285653,aaronical,adjective
```

## Examples

### Run with 1000 test cases (parallel)

```bash
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/1000_words.csv \
    --output results/base_1000 \
    --workers 8
```

**Expected time:** ~15-20 minutes with 8 workers

### Resume interrupted run

```bash
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/1000_words.csv \
    --output results/base_1000 \
    --workers 8 \
    --resume
```

### Test different pipelines

```bash
# Pipeline 1
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/sample.csv \
    --output results/pipeline_1

# Pipeline 2
python benchmark_pipeline.py \
    --pipeline hybrid_bm25_cosine_reranker_with_original_input_json \
    --test-data test_cases/sample.csv \
    --output results/pipeline_2

# Pipeline 3
python benchmark_pipeline.py \
    --pipeline some_other_pipeline \
    --test-data test_cases/sample.csv \
    --output results/pipeline_3
```

Then compare:
```bash
ls -lh results/*/pipeline*.csv
```

## Performance

- **4 workers**: ~20-25 minutes for 1000 test cases
- **8 workers**: ~10-15 minutes for 1000 test cases
- Each test case takes ~5-6 seconds (API calls + processing)
- Checkpoint every 10 cases (resumable if interrupted)

## Workflow

1. **Run each pipeline separately** → generates its own CSV report
2. **Compare CSV files** → see which pipeline has more matches per sense_id
3. **Analyze Excel reports** → detailed breakdown with statistics
4. **Check summary files** → quick overview of performance

## Benefits vs Comparison Tool

✅ **Simpler**: Run one pipeline at a time
✅ **More flexible**: Test any number of pipelines
✅ **Easier to debug**: Each run is independent
✅ **Clearer results**: One CSV per pipeline, easy to compare
✅ **Resume capability**: Checkpoint after every N cases

## Example Output

```
================================================================================
SUMMARY STATISTICS
================================================================================
Total test cases: 1000
Total quotations returned: 9234
Total matching quotations: 7891
Match rate: 85.5%
Errors: 3

Average quotations per test case: 9.2
Average matches per test case: 7.9
```

## Comparing Multiple Pipeline Runs

Create a simple comparison script:

```python
import pandas as pd

# Load results
base = pd.read_csv('results/base_run/oed-quotations_*.csv')
hybrid = pd.read_csv('results/hybrid_run/hybrid_*.csv')

# Compare
print(f"Base total matches: {base['matching_quotations'].sum()}")
print(f"Hybrid total matches: {hybrid['matching_quotations'].sum()}")

# Show differences
merged = base.merge(hybrid, on='sense_id', suffixes=('_base', '_hybrid'))
diff = merged[merged['matching_quotations_base'] != merged['matching_quotations_hybrid']]
print(f"\\nCases where pipelines differ: {len(diff)}")
```
