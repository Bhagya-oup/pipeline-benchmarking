# Getting Started with Pipeline Benchmarking

## What This Tool Does

This tool runs a **single Deepset pipeline** against test cases and counts how many returned quotations match the input sense_id. You can run it multiple times with different pipelines to compare their performance.

## New Workflow (Simplified)

### Old Approach ❌
- Ran both pipelines simultaneously in a comparison mode
- Complex setup with "new vs old" terminology
- Single output with side-by-side comparison

### New Approach ✅
- Run **one pipeline at a time**
- Generate independent CSV reports
- Compare results afterward using simple scripts
- Test as many pipelines as you want

---

## Quick Start Guide

### Step 1: Prepare Your Test Data

Create a CSV file with test cases:

```csv
entry_ref,sense_id,word,pos
aaron_n2,12884176,aaron,noun
aaronical_adj,10285653,aaronical,adjective
aaronite_n,12148161,aaronite,noun
```

Save as `test_cases/my_test.csv`

### Step 2: Run Your First Pipeline

```bash
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/my_test.csv \
    --output results/base_pipeline \
    --workers 8
```

**Output:**
```
[1/3] 12884176: 0/10 matching
[2/3] 10285653: 10/10 matching
[3/3] 12148161: 9/8 matching

✓ CSV report: results/base_pipeline/oed-quotations_20260113.csv
✓ Excel report: results/base_pipeline/oed-quotations_20260113.xlsx
✓ Summary: results/base_pipeline/oed-quotations_20260113_summary.txt

Total matching quotations: 19
Match rate: 67.9%
```

### Step 3: Run Your Second Pipeline

```bash
python benchmark_pipeline.py \
    --pipeline hybrid_bm25_cosine_reranker_with_original_input_json \
    --test-data test_cases/my_test.csv \
    --output results/hybrid_pipeline \
    --workers 8
```

**Output:**
```
[1/3] 12884176: 10/10 matching
[2/3] 10285653: 10/10 matching
[3/3] 12148161: 10/10 matching

✓ CSV report: results/hybrid_pipeline/hybrid_20260113.csv

Total matching quotations: 30
Match rate: 100.0%
```

### Step 4: Compare Results

```bash
python compare_results.py \
    results/base_pipeline/*.csv \
    results/hybrid_pipeline/*.csv
```

**Output:**
```
OVERALL STATISTICS
      Pipeline  Total Quotations  Matching Quotations  Match Rate (%)
oed-quotations                28                   19           67.9%
        hybrid                30                   30          100.0%

WIN/LOSS SUMMARY
oed-quotations: 0 cases where it has the most matches
hybrid: 2 cases where it has the most matches

✓ Hybrid pipeline performs better!
```

---

## Real-World Example: Testing 1000 Words

### 1. Run Base Pipeline (20 minutes)

```bash
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/1000_words.csv \
    --output results/base_1000 \
    --workers 8
```

### 2. Run Hybrid Pipeline (20 minutes)

```bash
python benchmark_pipeline.py \
    --pipeline hybrid_bm25_cosine_reranker_with_original_input_json \
    --test-data test_cases/1000_words.csv \
    --output results/hybrid_1000 \
    --workers 8
```

### 3. Run Third Pipeline (optional, 20 minutes)

```bash
python benchmark_pipeline.py \
    --pipeline some_experimental_pipeline \
    --test-data test_cases/1000_words.csv \
    --output results/experimental_1000 \
    --workers 8
```

### 4. Compare All Three

```bash
python compare_results.py \
    results/base_1000/*.csv \
    results/hybrid_1000/*.csv \
    results/experimental_1000/*.csv
```

---

## Understanding the Output

### CSV Report Format

```csv
entry_ref,sense_id,word,pos,total_quotations,matching_quotations,response_time,error
aaron_n2,12884176,aaron,noun,10,10,42.79,
```

**Columns:**
- `entry_ref`: Entry reference (e.g., "aaron_n2")
- `sense_id`: Sense ID to match (e.g., "12884176")
- `word`: Word being searched (e.g., "aaron")
- `pos`: Part of speech (e.g., "noun")
- `total_quotations`: Total quotations returned by pipeline
- `matching_quotations`: How many have `primary_sense == sense_id`
- `response_time`: API response time in seconds
- `error`: Error message if any

### Excel Report Sheets

1. **Results**: Full results table
2. **Summary**: Overall statistics
3. **Top Matches**: Cases with highest match counts
4. **Zero Matches**: Cases that need investigation
5. **Errors**: Failed cases

### Summary File

Text file with:
- Overall match rate
- Perfect matches count
- Zero matches count
- Error summary

---

## Advanced Usage

### Resume Interrupted Run

If your run gets interrupted, resume from checkpoint:

```bash
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/1000_words.csv \
    --output results/base_1000 \
    --workers 8 \
    --resume
```

### Adjust Rate Limiting

Control API calls per minute:

```bash
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/1000_words.csv \
    --output results/base_1000 \
    --rate-limit 120  # 120 calls/minute instead of default 60
```

### Change Checkpoint Frequency

Save progress more/less frequently:

```bash
python benchmark_pipeline.py \
    --pipeline oed-quotations \
    --test-data test_cases/1000_words.csv \
    --output results/base_1000 \
    --checkpoint-interval 50  # Save every 50 cases instead of 10
```

---

## Benefits of Single Pipeline Approach

✅ **Simpler**: No confusion about "new vs old"
✅ **Flexible**: Test unlimited pipelines
✅ **Independent**: Each run is isolated
✅ **Resumable**: Checkpoint every N cases
✅ **Clear**: One CSV per pipeline
✅ **Debuggable**: Easier to troubleshoot issues

---

## Common Workflows

### Workflow 1: A/B Testing Two Pipelines

```bash
# Test baseline
python benchmark_pipeline.py --pipeline baseline --test-data cases.csv --output results/baseline

# Test improved version
python benchmark_pipeline.py --pipeline improved --test-data cases.csv --output results/improved

# Compare
python compare_results.py results/baseline/*.csv results/improved/*.csv
```

### Workflow 2: Testing Multiple Configurations

```bash
# Test with different parameters
python benchmark_pipeline.py --pipeline config_a --test-data cases.csv --output results/config_a
python benchmark_pipeline.py --pipeline config_b --test-data cases.csv --output results/config_b
python benchmark_pipeline.py --pipeline config_c --test-data cases.csv --output results/config_c

# Compare all
python compare_results.py results/config_*/*.csv
```

### Workflow 3: Progressive Testing

```bash
# Start small
python benchmark_pipeline.py --pipeline new_model --test-data test_cases/10_cases.csv --output results/small_test

# If good, scale up
python benchmark_pipeline.py --pipeline new_model --test-data test_cases/100_cases.csv --output results/medium_test

# Final validation
python benchmark_pipeline.py --pipeline new_model --test-data test_cases/1000_cases.csv --output results/full_test
```

---

## Troubleshooting

### Issue: BOM (Byte Order Mark) in CSV File ⚠️ CRITICAL

**This is the most common issue!** Always check for BOM before running tests.

**Symptoms:**
- Error: `UnicodeDecodeError` or `unexpected character '\ufeff'`
- CSV parsing fails on first row
- Header shows: `﻿entry_ref` instead of `entry_ref`

**Quick Check:**
```bash
# Check if your CSV has BOM (do this FIRST!)
head -c 4 test_cases/your_file.csv | od -An -tx1

# Good (no BOM): "65 6e 74 72" - starts with "entr"
# Bad (has BOM): "ef bb bf 65" - starts with BOM marker
```

**Quick Fix:**
```bash
# Remove BOM from file
tail -c +4 test_cases/your_file.csv > test_cases/your_file_fixed.csv

# Use the fixed file
python benchmark_pipeline.py --test-data test_cases/your_file_fixed.csv ...
```

**Prevention:**
- **Excel users**: Save as "CSV UTF-8" NOT "CSV (Comma delimited)"
- **Google Sheets**: Download as CSV (automatically BOM-free)
- **Text editors**: Use VS Code or Notepad++ (not Windows Notepad)

**Why it matters**: BOM causes the framework to fail silently or throw confusing errors. A 1000-case test could fail after 10 minutes because of BOM!

### Issue: "No test cases loaded"
- Check CSV file format (must have header: `entry_ref,sense_id,word,pos`)
- Run BOM check (see above) - this is usually the cause
- Verify file exists: `ls -l test_cases/your_file.csv`

### Issue: "Pipeline returned 0 matches"
- Verify pipeline name is correct in Deepset Cloud
- Check if pipeline is returning quotations with `primary_sense` metadata
- Use debug script: `python debug_both_pipelines.py` to inspect

### Issue: Slow performance
- Increase `--workers` (try 8-16 for faster machines)
- Check API rate limits
- Ensure Deepset Cloud pipelines are responding quickly

### Issue: Checkpoint not resuming
- Ensure you're using same `--output` directory
- Check that checkpoint file exists in `{output}/checkpoints/`

---

## Next Steps

1. **Start small**: Test with 10-20 cases first
2. **Validate results**: Check CSV output makes sense
3. **Scale up**: Run full 1000-case benchmark
4. **Compare pipelines**: Use comparison script
5. **Analyze**: Check Excel reports for detailed insights

## Questions?

- Check `README_SINGLE_PIPELINE.md` for detailed documentation
- Review example outputs in `results/` directory
- Run `python benchmark_pipeline.py --help` for all options
