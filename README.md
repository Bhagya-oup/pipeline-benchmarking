# Pipeline Benchmarking Tool

Automated benchmarking framework for Deepset Cloud pipelines with parallel execution, checkpoint-based resumability, and comprehensive reporting.

## Overview

This tool benchmarks a Deepset Cloud pipeline across multiple test cases, measuring:
- **Retrieval accuracy**: Number of matching quotations per sense
- **Performance**: Response time per query
- **Success rate**: How often the pipeline succeeds
- **Match distribution**: Perfect matches, partial matches, zero matches

## Features

✅ **Parallel Execution**: Run 4-8 workers for optimal speed (~1.5 hours for 1000 test cases with 8 workers)
✅ **Checkpoint-based Resumability**: Never lose progress if interrupted
✅ **Comprehensive Reporting**: CSV, Excel (multi-sheet), and text summary
✅ **Real API Testing**: Tests against actual Deepset Cloud pipeline APIs (~42-52 seconds per test case)
✅ **Error Handling**: Automatic retry with exponential backoff
✅ **Rate Limiting**: Prevents exceeding API quotas

## Installation

```bash
cd pipeline_benchmarking
pip install -r requirements.txt
```

## Prerequisites

**Environment Variables** (set in parent project's `.env`):
```bash
HERO_API_KEY=your_hero_api_key
DEEPSET_API_KEY=your_deepset_api_key
DEEPSET_WORKSPACE=your_deepset_workspace
```

**Note**: The tool now uses the **Hero Quotations API** (matching your production pipeline), which expects full POS names like `"noun"`, `"verb"`, `"adjective"` in your test data CSV.

## Quick Start

### 1. Prepare Test Data

Create a CSV file with your test cases:

```csv
entry_ref,sense_id,word,pos
insinuate_v,353637,insinuate,verb
know_v,40025845,know,verb
anatheme_n1,4073595,anatheme,noun
dough-baked_adj,6185578,dough-baked,adjective
self-slaughter_n,23517073,self-slaughter,noun
```

**Important**: Use full POS names (`noun`, `verb`, `adjective`, `adverb`) not codes (`n`, `v`, `adj`).

Save to `test_cases/my_test_cases.csv`

### 2. Run Benchmark

```bash
cd pipeline_benchmarking

python benchmark_pipeline.py \
  --pipeline your_pipeline_name \
  --test-data test_cases/my_test_cases.csv \
  --output results/my_pipeline_test \
  --workers 8
```

### 3. View Results

```bash
# Text summary
cat results/my_pipeline_test/your_pipeline_name_TIMESTAMP_summary.txt

# CSV report
open results/my_pipeline_test/your_pipeline_name_TIMESTAMP.csv

# Excel report (multi-sheet analysis)
open results/my_pipeline_test/your_pipeline_name_TIMESTAMP.xlsx
```

## Usage

### Basic Benchmark
```bash
python benchmark_pipeline.py \
  --pipeline oed-quotations \
  --test-data test_cases/data.csv
```

### Resume from Checkpoint
```bash
python benchmark_pipeline.py \
  --pipeline oed-quotations \
  --test-data test_cases/data.csv \
  --resume
```

### Clear Checkpoint and Start Fresh
```bash
python benchmark_pipeline.py \
  --pipeline oed-quotations \
  --test-data test_cases/data.csv \
  --clear-checkpoint
```

### More Workers (Faster)
```bash
python benchmark_pipeline.py \
  --pipeline oed-quotations \
  --test-data test_cases/data.csv \
  --workers 8
```

### Custom Output Directory
```bash
python benchmark_pipeline.py \
  --pipeline oed-quotations \
  --test-data test_cases/data.csv \
  --output results/experiment_001
```

### Compare Multiple Pipeline Runs

To compare different pipelines, run each separately and use the comparison script:

```bash
# Test pipeline A
python benchmark_pipeline.py --pipeline pipeline_a --test-data test_cases/data.csv --output results/pipeline_a

# Test pipeline B
python benchmark_pipeline.py --pipeline pipeline_b --test-data test_cases/data.csv --output results/pipeline_b

# Compare results
python compare_results.py results/pipeline_a/*.csv results/pipeline_b/*.csv
```

## Test Data Formats

### CSV Format
```csv
entry_ref,sense_id,word,pos
insinuate_v,353637,insinuate,verb
nough_adv,34306144,'nough,adverb
know_v,40025845,know,verb
anatheme_n1,4073595,anatheme,noun
dough-baked_adj,6185578,dough-baked,adjective
```

**Important**: Use **full POS names** (`noun`, `verb`, `adjective`, `adverb`, etc.), not short codes (`n`, `v`, `adj`), as this matches the Hero Quotations API format.

### JSON Format
```json
[
  {
    "entry_ref": "insinuate_v",
    "sense_id": "353637",
    "word": "insinuate",
    "pos": "verb"
  },
  {
    "entry_ref": "anatheme_n1",
    "sense_id": "4073595",
    "word": "anatheme",
    "pos": "noun"
  },
  {
    "entry_ref": "dough-baked_adj",
    "sense_id": "6185578",
    "word": "dough-baked",
    "pos": "adjective"
  }
]
```

### TXT Format (space-separated)
```
insinuate_v 353637 insinuate verb
anatheme_n1 4073595 anatheme noun
dough-baked_adj 6185578 dough-baked adjective
```

## Output Reports

### 1. CSV Report (`pipeline_name_TIMESTAMP.csv`)
Simple table with all results:
```
entry_ref,sense_id,word,pos,total_quotations,matching_quotations,response_time,error
insinuate_v,353637,insinuate,verb,10,8,45.2,
know_v,40025845,know,verb,10,10,42.8,
anatheme_n1,4073595,anatheme,noun,10,7,48.1,
```

### 2. Excel Report (`pipeline_name_TIMESTAMP.xlsx`)
Multi-sheet workbook:
- **Results**: Full detailed results for all test cases
- **Summary**: Overall statistics (match rate, success rate, etc.)
- **Top Matches**: Cases with highest match counts
- **Zero Matches**: Cases that need investigation
- **Errors**: Failed test cases with error messages

### 3. Text Summary (`pipeline_name_TIMESTAMP_summary.txt`)
Human-readable summary:
```
Pipeline: oed-quotations
Total Test Cases: 1000
Success Rate: 984/1000 (98.4%)
Total Matching Quotations: 6,547
Average Matches per Case: 6.5
Perfect Matches (10/10): 324 cases
Zero Matches: 142 cases
```

## Architecture

```
pipeline_benchmarking/
├── benchmark_pipeline.py          # Main CLI for single pipeline testing
├── compare_results.py             # Compare results from multiple runs
├── src/
│   ├── config.py                  # Configuration dataclasses
│   ├── test_case_loader.py        # CSV/JSON/TXT parsers
│   ├── pipeline_executor.py       # Pipeline invocation
│   ├── single_pipeline_runner.py  # Single pipeline execution engine
│   ├── checkpoint_manager.py      # Resumability
│   ├── metrics_calculator.py      # Accuracy metrics
│   └── report_generator.py        # CSV/Excel/text output
├── test_cases/                    # Your test data (gitignored)
└── results/                       # Output reports (gitignored)
    ├── checkpoints/
    └── pipeline_name_TIMESTAMP.{csv,xlsx,txt}
```

## Performance

**For 1000 Test Cases:**
- **8 workers**: ~1.5 hours (90 minutes)
- **4 workers**: ~3 hours (180 minutes)

**For 100 Test Cases:**
- **8 workers**: ~9 minutes
- **4 workers**: ~18 minutes

**Actual Response Time per Test Case:**
- Average: **~42-52 seconds per case** (based on real test data)
- Each test case processes 10 quotations with LLM analysis
- Times include full pipeline processing (retrieval + reranking + LLM verification)

## Troubleshooting

### BOM (Byte Order Mark) Errors ⚠️ IMPORTANT

**Problem**: CSV files with UTF-8 BOM cause parsing errors like:
```
Error: UnicodeDecodeError or unexpected character '\ufeff'
Expected: entry_ref,sense_id,word,pos
Got: ﻿entry_ref,sense_id,word,pos
```

**Cause**: Some text editors (Excel, Windows Notepad) save CSV files with a UTF-8 BOM (Byte Order Mark), which is a hidden 3-byte prefix that causes parsing failures.

**Detection**:
```bash
# Check if your CSV has BOM
head -c 4 test_cases/your_file.csv | od -An -tx1
# If output shows "ef bb bf 65", file has BOM (bad)
# If output shows "65 6e 74 72", no BOM (good)
```

**Solution 1 - Remove BOM** (Recommended):
```bash
# Remove BOM from existing file
tail -c +4 test_cases/your_file.csv > test_cases/your_file_fixed.csv

# Or use this one-liner to fix in place
tail -c +4 test_cases/your_file.csv > /tmp/temp.csv && mv /tmp/temp.csv test_cases/your_file.csv
```

**Solution 2 - Prevent BOM in the first place**:
- **If using Excel**: Save as "CSV UTF-8" NOT "CSV (Comma delimited)"
- **If using Notepad**: Use Notepad++ or VS Code instead
- **If using Python**: Use `encoding='utf-8-sig'` when reading CSV
- **If using Google Sheets**: Download as CSV (automatically BOM-free)

**Verification**:
```bash
# After fixing, verify no BOM
head -c 4 test_cases/your_file.csv | od -An -tx1
# Should start with "65 6e 74 72" (the letters "entr")
```

**Best Practice**: ALWAYS check for BOM before running large tests to avoid wasting time.

### "Missing environment variables"
Set the required variables in your `.env` file in the parent project directory.

### "Checkpoint found"
Use `--clear-checkpoint` to start fresh, or `--resume` to continue from checkpoint.

### API Rate Limiting
Reduce workers: `--workers 2` or increase rate limit interval in code.

### Import Errors
Ensure you're in the `pipeline_benchmarking/` directory when running the tool.

## Examples

### Test Baseline Pipeline on 1000 Cases
```bash
python benchmark_pipeline.py \
  --pipeline oed-quotations \
  --test-data test_cases/1000_words.csv \
  --output results/baseline_test \
  --workers 8
```

### Test Hybrid Pipeline on Same Cases
```bash
python benchmark_pipeline.py \
  --pipeline rare_senses_hybrid_cosine_similarity_and_BM25_plus_reranking \
  --test-data test_cases/1000_words.csv \
  --output results/hybrid_test \
  --workers 8
```

### Compare Results from Both Runs
```bash
python compare_results.py \
  results/baseline_test/*.csv \
  results/hybrid_test/*.csv
```

### Progressive Testing (Start Small)
```bash
# Start with 10 cases to verify setup
python benchmark_pipeline.py --pipeline your_pipeline --test-data test_cases/10_cases.csv --workers 4

# Scale to 100 cases
python benchmark_pipeline.py --pipeline your_pipeline --test-data test_cases/100_cases.csv --workers 8

# Full 1000 case test
python benchmark_pipeline.py --pipeline your_pipeline --test-data test_cases/1000_cases.csv --workers 8
```

## Contributing

This is a standalone tool for benchmarking Deepset Cloud pipelines. To add features:
1. Modify modules in `src/`
2. Update CLI in `benchmark_pipeline.py` or `compare_results.py`
3. Update this README

## License

Part of the Rare Senses Retrieval System project.
