# Pipeline Benchmarking Tool

Automated comparison framework for Deepset pipelines with parallel execution, checkpoint-based resumability, and comprehensive reporting.

## Overview

This tool compares two Deepset Cloud pipelines (e.g., "new" vs "old") across multiple test cases, measuring:
- **Retrieval accuracy**: Number of matches found
- **Performance**: Response time per query
- **Success rate**: How often each pipeline succeeds
- **Head-to-head comparison**: Which pipeline performs better

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
SOLR_URL=https://your-solr-url.com/solr
SOLR_USERNAME=optional
SOLR_PASSWORD=optional
HERO_API_KEY=your_hero_api_key
DEEPSET_API_KEY=your_deepset_api_key
DEEPSET_WORKSPACE_URL=https://your-workspace.deepset.cloud
```

**Note**: The tool now uses the **Hero Quotations API** (matching your production pipeline), which expects full POS names like `"noun"`, `"verb"`, `"adjective"` in your test data CSV.

## Quick Start

### 1. Prepare Test Data

Create a CSV file with your test cases:

```csv
entry_ref,sense_id,word,pos
fine_n,fine_n01_1,fine,noun
fair_n,fair_n02_3,fair,noun
sausage_n,sausage_n01_1,sausage,noun
```

**Important**: Use full POS names (`noun`, `verb`, `adjective`) not codes (`n`, `v`, `adj`).

Save to `test_cases/my_test_cases.csv`

### 2. Run Comparison

```bash
cd pipeline_benchmarking

python compare_pipelines.py \
  --test-data test_cases/my_test_cases.csv \
  --new-pipeline unified_simple \
  --old-pipeline sense_retrieval_no_custom \
  --output results/comparison_2026-01-13 \
  --workers 4
```

### 3. View Results

```bash
# Text summary
cat results/comparison_2026-01-13/summary_TIMESTAMP.txt

# Excel report (multi-sheet analysis)
open results/comparison_2026-01-13/comparison_TIMESTAMP.xlsx
```

## Usage

### Basic Comparison
```bash
python compare_pipelines.py \
  --test-data test_cases/data.csv \
  --new-pipeline unified_simple \
  --old-pipeline sense_retrieval_no_custom
```

### Resume from Checkpoint
```bash
python compare_pipelines.py \
  --test-data test_cases/data.csv \
  --new-pipeline unified_simple \
  --old-pipeline sense_retrieval_no_custom \
  --resume
```

### Clear Checkpoint and Start Fresh
```bash
python compare_pipelines.py \
  --test-data test_cases/data.csv \
  --new-pipeline unified_simple \
  --old-pipeline sense_retrieval_no_custom \
  --clear-checkpoint
```

### More Workers (Faster)
```bash
python compare_pipelines.py \
  --test-data test_cases/data.csv \
  --new-pipeline unified_simple \
  --old-pipeline sense_retrieval_no_custom \
  --workers 8
```

### Custom Output Directory
```bash
python compare_pipelines.py \
  --test-data test_cases/data.csv \
  --new-pipeline unified_simple \
  --old-pipeline sense_retrieval_no_custom \
  --output results/experiment_001
```

## Test Data Formats

### CSV Format
```csv
entry_ref,sense_id,word,pos
fine_n,fine_n01_1,fine,noun
fair_n,fair_n02_3,fair,noun
flowery_adj1,flowery_adj_4165862,flowery,adjective
```

**Important**: Use **full POS names** (`noun`, `verb`, `adjective`, `adverb`, etc.), not short codes (`n`, `v`, `adj`), as this matches the Hero Quotations API format.

### JSON Format
```json
[
  {
    "entry_ref": "fine_n",
    "sense_id": "fine_n01_1",
    "word": "fine",
    "pos": "noun"
  },
  {
    "entry_ref": "fair_n",
    "sense_id": "fair_n02_3",
    "word": "fair",
    "pos": "noun"
  }
]
```

### TXT Format (space-separated)
```
fine_n fine_n01_1 fine noun
fair_n fair_n02_3 fair noun
```

## Output Reports

### 1. CSV Report (`comparison_TIMESTAMP.csv`)
Simple table with all results:
```
entry_ref,sense_id,word,pos,new_matches,old_matches,improvement,winner
fine_n,fine_n01_1,fine,n,15,8,+87.5%,new
```

### 2. Excel Report (`comparison_TIMESTAMP.xlsx`)
Multi-sheet workbook:
- **Summary**: Overall statistics
- **Detailed Results**: All test cases
- **Top Improvements**: Biggest wins for new pipeline
- **Failures**: Cases where both pipelines failed
- **New Pipeline Wins**: All cases where new pipeline outperformed

### 3. Text Summary (`summary_TIMESTAMP.txt`)
Human-readable summary:
```
Total Test Cases: 1000
New Pipeline: 847/1000 (84.7%) success
Old Pipeline: 612/1000 (61.2%) success
New Wins: 312
Old Wins: 89
Ties: 599
```

## Architecture

```
pipeline_benchmarking/
├── compare_pipelines.py           # Main CLI
├── src/
│   ├── config.py                  # Configuration dataclasses
│   ├── test_case_loader.py        # CSV/JSON/TXT parsers
│   ├── pipeline_executor.py       # Pipeline invocation
│   ├── parallel_runner.py         # Multiprocessing engine
│   ├── checkpoint_manager.py      # Resumability
│   ├── metrics_calculator.py      # Comparison metrics
│   └── report_generator.py        # CSV/Excel/text output
├── test_cases/                    # Your test data (gitignored)
└── results/                       # Output reports (gitignored)
    ├── checkpoints/
    └── comparison_TIMESTAMP.{csv,xlsx,txt}
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
- This is for running a single pipeline on one test case
- Each test case processes 10 quotations with LLM analysis
- If comparing two pipelines, multiply time estimates by 2

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

### Compare On-the-Fly vs Pre-Indexed
```bash
python compare_pipelines.py \
  --test-data test_cases/rare_senses_1000.csv \
  --new-pipeline unified_simple \
  --old-pipeline sense_retrieval_no_custom \
  --output results/onthefly_vs_preindexed
```

### Compare Different Top-K Values
(Requires separate pipeline configurations in Deepset Cloud)
```bash
python compare_pipelines.py \
  --test-data test_cases/test.csv \
  --new-pipeline pipeline_topk_20 \
  --old-pipeline pipeline_topk_50 \
  --output results/topk_comparison
```

## Contributing

This is a standalone tool within the Rare Senses project. To add features:
1. Modify modules in `src/`
2. Update CLI in `compare_pipelines.py`
3. Update this README

## License

Part of the Rare Senses Retrieval System project.
