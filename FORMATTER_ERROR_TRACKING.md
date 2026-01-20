# Formatter Error Tracking

## Overview

The benchmarking tool now tracks **formatter errors** separately from genuine zero matches and excludes them from match statistics.

## What is a Formatter Error?

A formatter error occurs when the LLM (Language Model) fails to return classification results for ALL quotations it receives. This happens when:

1. The number of JSON entries in the LLM response doesn't match the number of quotations sent
2. The LLM returns incomplete classifications (e.g., 9 entries for 10 quotations)
3. The formatter cannot map quotation metadata due to missing classifications

### Example Error Messages:
- `"The number of selections in the JSON does not match the number of quotations"`
- `"int() argument must be a string, a bytes-like object or a real number, not 'list'"`

## Why Track Separately?

**Formatter errors are NOT retrieval failures.** They indicate:
- ✅ Quotations were successfully retrieved
- ✅ Semantic search worked correctly
- ❌ LLM failed to process all quotations consistently

**Genuine zero matches** indicate:
- ✅ Quotations were successfully retrieved
- ✅ LLM processed all quotations correctly
- ❌ No quotations matched the target sense

Including formatter errors in match statistics would:
- ❌ Artificially inflate zero-match rates
- ❌ Mask actual retrieval performance
- ❌ Make it harder to identify LLM reliability issues

## How It Works

### 1. Error Detection (pipeline_executor.py)

The executor detects formatter errors by checking response errors:

```python
if 'errors' in result_data and result_data['errors']:
    error_text = str(result_data['errors'])
    if 'number of selections in the JSON does not match' in error_text.lower():
        is_formatter_error = True
    elif 'int() argument must be a string' in error_text:
        is_formatter_error = True
```

### 2. Error Classification

All errors are tagged with an `error_type`:
- `formatter_error` - LLM failed to return all classifications
- `http_error` - API/network error
- `pipeline_error` - Other pipeline failures

### 3. Statistics Exclusion

All reports exclude formatter errors from match statistics:

**Excluded from:**
- Zero match counts
- Match rate calculations
- Average matches per case
- Match distribution statistics
- "At least 1 match" counts

**Tracked separately:**
- Total formatter errors count
- List of affected test cases
- Separate Excel sheet
- Separate error section in reports

## Report Changes

### CSV Output

New `error_type` column added:

```csv
entry_ref,sense_id,word,pos,total_quotations,matching_quotations,response_time,error_type,error
baby_n,30781637,baby,noun,0,0,56.25,formatter_error,FORMATTER_ERROR: ...
witty_adj,14209250,witty,adjective,10,0,53.33,,
```

### Summary Report

```
OVERALL STATISTICS
==================

Total test cases: 44
Valid test cases (excluding ALL errors): 43
  - Pipeline errors: 0
  - Formatter errors: 1 (excluded from match stats)
Total quotations returned: 430
Total matching quotations: 183
Overall match rate: 42.6%

NOTE: Match statistics exclude 1 formatter error(s)
      (LLM failed to return classifications for all quotations)

...

ERRORS
======

Total pipeline errors: 0
Total formatter errors (LLM failures): 1
  NOTE: Formatter errors are excluded from match statistics

Formatter error cases (LLM did not return all quotation classifications):
  - baby_n (30781637)
```

### Excel Report

**New Sheets:**
1. **Summary** - Shows formatter errors as a separate metric
2. **Formatter Errors** - Lists all formatter error cases
3. **Zero Matches** - NOW only shows genuine zero matches (excludes formatter errors)
4. **Pipeline Errors** - Other errors (HTTP, timeout, etc.)

## Console Output

When running benchmarks, you'll see:

```
==============================================================================
SUMMARY STATISTICS
==============================================================================
Total test cases: 44
Valid cases (excluding all errors): 43
Formatter errors (LLM failures): 1 - EXCLUDED from match stats
Pipeline errors: 0

Total quotations returned: 430
Total matching quotations: 183
Match rate: 42.6%

Average quotations per test case: 10.0
Average matches per test case: 4.3
```

## Impact on Previous Results

### Example: Your 44 Test Case Run

**Before (including formatter errors):**
- Zero matches: 11/44 (25.0%)
- Match rate: ~40%

**After (excluding formatter errors):**
- Genuine zero matches: 10/43 (23.3%)
- Formatter errors: 1/44 (2.3%)
- Match rate: 42.6% (calculated from 43 valid cases)

**Key Insight:**
- baby_n (30781637) showing 0/0 is NOT a retrieval failure
- It's an LLM error - quotations were retrieved but LLM didn't classify them
- True zero match rate for rare senses: 10/22 = 45.5% (not 11/22 = 50%)

## Best Practices

### 1. Monitoring Formatter Errors

Track formatter error rate over time:
- **< 5%**: Acceptable (LLM occasional failures)
- **5-10%**: Concerning (investigate LLM configuration)
- **> 10%**: Critical (LLM reliability issue)

### 2. Fixing Formatter Errors

If formatter error rate is high:
- Set LLM `temperature=0` for deterministic outputs
- Add retry logic with exponential backoff
- Use structured outputs (JSON mode) if available
- Make formatter more tolerant (accept N±1 entries with warning)
- Add validation in LLM prompt: "You MUST return exactly {N} entries"

### 3. Interpreting Results

When analyzing zero matches:
1. Check "Zero Matches" sheet (genuine failures only)
2. Check "Formatter Errors" sheet separately
3. Focus improvement efforts on genuine zeros
4. Address formatter errors as LLM reliability issue

## Migration Guide

### If You Have Existing Results

Old results without `error_type` field will:
- Be treated as genuine errors (not formatter errors)
- Still be excluded from statistics
- Not break existing code

### To Reprocess Old Results

1. Re-run benchmarks with updated code
2. Old CSV files won't have `error_type` column
3. New runs will properly classify formatter errors
4. Compare old vs new to identify which "zeros" were formatter errors

## Example Use Cases

### Case 1: Finding LLM Reliability Issues

```bash
# Run benchmark
python benchmark_pipeline.py --pipeline hybrid --test-data test.csv --workers 8

# Check results
cat results/hybrid_*/hybrid_*_summary.txt | grep "formatter errors"
# Output: Total formatter errors (LLM failures): 3

# Investigate
# → 3/44 = 6.8% formatter error rate
# → Check LLM configuration
# → Consider adding retry logic
```

### Case 2: Analyzing Genuine Retrieval Failures

```bash
# Check genuine zero matches (excludes formatter errors)
# Open: results/hybrid_*/hybrid_*.xlsx
# Sheet: "Zero Matches" (not "Formatter Errors")

# These are real retrieval challenges:
# - sentence_n (23609960): 0/10
# - render_v (26061805): 0/10
# etc.
```

### Case 3: Comparing Pipelines

When comparing two pipelines:
- Both will exclude formatter errors from match statistics
- Formatter errors are tracked separately for each pipeline
- Fair comparison of actual retrieval performance
- Can compare LLM reliability as separate metric

## Technical Details

### Error Type Values

| error_type | Meaning | Excluded from Stats? |
|------------|---------|---------------------|
| `formatter_error` | LLM didn't return all classifications | ✅ YES |
| `http_error` | Network/API error | ✅ YES |
| `pipeline_error` | Other pipeline failure | ✅ YES |
| `null` / empty | No error (success) | ❌ NO - included in stats |

### Code Locations

- **Detection**: `src/pipeline_executor.py` (lines 180-193)
- **CSV output**: `src/single_pipeline_report.py` (lines 42-68)
- **Statistics**: `src/single_pipeline_report.py` (lines 177-188, 225-290)
- **Console**: `benchmark_pipeline.py` (lines 223-244)

## FAQ

**Q: Will this break my existing workflows?**
A: No. Old results will still work. New runs will have better error tracking.

**Q: What if I want to include formatter errors in stats?**
A: You can modify the code, but it's not recommended. Formatter errors don't represent retrieval failures.

**Q: How do I fix formatter errors?**
A: Fix the LLM configuration (temperature=0, retries, structured outputs) or make the formatter more tolerant.

**Q: Can I see both genuine zeros and formatter errors together?**
A: Yes, in the Excel "Results" sheet (Sheet 1) with all data. Use `error_type` column to filter.

**Q: What about the comparison reports?**
A: Comparison reports will also exclude formatter errors from both pipelines' statistics.

## Summary

✅ **Formatter errors are now tracked separately**
✅ **Match statistics exclude formatter errors**
✅ **All reports updated to show this clearly**
✅ **Backwards compatible with old data**
✅ **Helps distinguish LLM reliability from retrieval quality**

This gives you:
- Accurate match rate metrics
- Clear visibility into LLM reliability
- Better insights for debugging and improvement
- Fair pipeline comparisons
