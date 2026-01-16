# BOM (Byte Order Mark) Prevention Guide

## ⚠️ Why This Matters

BOM errors are the **#1 cause of test failures** in this framework. A tiny 3-byte prefix in your CSV file can cause:
- Parsing failures
- Silent errors
- Wasted time (1000-case tests failing after 10+ minutes)

**Always check for BOM before running tests!**

---

## What is BOM?

BOM (Byte Order Mark) is a hidden 3-byte sequence (`EF BB BF`) that some text editors add to the beginning of UTF-8 files. It's invisible in most editors but breaks CSV parsing.

**Example:**
```
Without BOM: entry_ref,sense_id,word,pos
With BOM:    ﻿entry_ref,sense_id,word,pos  (← invisible \ufeff character)
```

---

## Quick Detection

### Method 1: Hexdump (Recommended)

```bash
# Check first 4 bytes of your CSV
head -c 4 test_cases/your_file.csv | od -An -tx1

# If output is "65 6e 74 72" → No BOM ✅ (good!)
# If output is "ef bb bf 65" → Has BOM ❌ (fix it!)
```

### Method 2: Visual Check (Less Reliable)

```bash
# Display first characters
cat test_cases/your_file.csv | head -1

# If you see weird spacing or invisible character before "entry_ref", you have BOM
```

### Method 3: File Command

```bash
file test_cases/your_file.csv

# With BOM:    UTF-8 Unicode (with BOM) text
# Without BOM: ASCII text or UTF-8 Unicode text
```

---

## Quick Fix

### Option 1: Remove BOM (Recommended)

```bash
# Remove BOM and create fixed file
tail -c +4 test_cases/your_file.csv > test_cases/your_file_fixed.csv

# Verify it's fixed
head -c 4 test_cases/your_file_fixed.csv | od -An -tx1
# Should show: 65 6e 74 72 (starts with "entr")

# Use the fixed file
python benchmark_pipeline.py --test-data test_cases/your_file_fixed.csv ...
```

### Option 2: Fix In-Place

```bash
# Remove BOM from original file (WARNING: overwrites original)
tail -c +4 test_cases/your_file.csv > /tmp/temp.csv && mv /tmp/temp.csv test_cases/your_file.csv
```

### Option 3: Using sed (Alternative)

```bash
# Remove BOM using sed
sed '1s/^\xEF\xBB\xBF//' test_cases/your_file.csv > test_cases/your_file_fixed.csv
```

---

## Prevention Strategies

### If Using Excel

**WRONG** ❌:
- File → Save As → CSV (Comma delimited)
- This adds BOM!

**CORRECT** ✅:
- File → Save As → CSV UTF-8 (Comma delimited)
- Or use Google Sheets instead

**Best**: Don't use Excel for CSV editing. Use:
- Google Sheets (Download as CSV)
- Python pandas (no BOM by default)
- VS Code or Notepad++

### If Using Text Editors

**WRONG** ❌:
- Windows Notepad (adds BOM by default)

**CORRECT** ✅:
- VS Code
- Notepad++
- Sublime Text
- Any editor with "UTF-8 without BOM" option

### If Using Python

When creating CSV files in Python:

```python
import pandas as pd

# Good - no BOM
df.to_csv('test_cases/data.csv', index=False, encoding='utf-8')

# Also good - explicitly removes BOM if present
df.to_csv('test_cases/data.csv', index=False, encoding='utf-8-sig')
```

### If Using Google Sheets

Google Sheets **never** adds BOM when downloading as CSV. ✅

```
File → Download → Comma Separated Values (.csv)
```

This is the **safest** way to create CSV files!

---

## Automated BOM Check Script

Create this script to check all CSV files at once:

```bash
#!/bin/bash
# check_bom.sh - Check all CSV files for BOM

echo "Checking for BOM in CSV files..."
echo ""

HAS_BOM=0

for file in test_cases/*.csv; do
    if [ -f "$file" ]; then
        # Check first 3 bytes
        BOM=$(head -c 3 "$file" | od -An -tx1 | tr -d ' ')

        if [ "$BOM" = "efbbbf" ]; then
            echo "❌ HAS BOM: $file"
            HAS_BOM=$((HAS_BOM + 1))
        else
            echo "✅ No BOM:  $file"
        fi
    fi
done

echo ""
if [ $HAS_BOM -eq 0 ]; then
    echo "✅ All CSV files are BOM-free!"
    exit 0
else
    echo "❌ Found $HAS_BOM file(s) with BOM. Fix with:"
    echo "   tail -c +4 <file>.csv > <file>_fixed.csv"
    exit 1
fi
```

Save as `check_bom.sh`, make executable, and run:
```bash
chmod +x check_bom.sh
./check_bom.sh
```

---

## Common Error Messages

### Error 1: UnicodeDecodeError

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xef in position 0
```

**Cause**: BOM at start of file
**Fix**: Remove BOM using `tail -c +4`

### Error 2: Unexpected Character

```
Error: Expected 'entry_ref' but got '\ufeff entry_ref'
```

**Cause**: BOM interpreted as character
**Fix**: Remove BOM using `tail -c +4`

### Error 3: CSV Parsing Failed

```
ParserError: Error tokenizing data. C error: Expected 4 fields, saw 0
```

**Cause**: BOM confusing CSV parser
**Fix**: Remove BOM using `tail -c +4`

---

## Integration with Framework

### Manual Check Before Running

```bash
# ALWAYS do this first!
head -c 4 test_cases/my_data.csv | od -An -tx1

# If clean, proceed
python benchmark_pipeline.py --test-data test_cases/my_data.csv ...
```

### Automated Fix Script

Add this to your workflow:

```bash
#!/bin/bash
# run_benchmark_safe.sh - Check BOM before running

TEST_FILE=$1

# Check for BOM
BOM=$(head -c 3 "$TEST_FILE" | od -An -tx1 | tr -d ' ')

if [ "$BOM" = "efbbbf" ]; then
    echo "⚠️  BOM detected! Removing..."
    FIXED_FILE="${TEST_FILE%.csv}_fixed.csv"
    tail -c +4 "$TEST_FILE" > "$FIXED_FILE"
    echo "✅ Using fixed file: $FIXED_FILE"
    TEST_FILE="$FIXED_FILE"
else
    echo "✅ No BOM detected"
fi

# Run benchmark
python benchmark_pipeline.py --test-data "$TEST_FILE" "$@"
```

Usage:
```bash
./run_benchmark_safe.sh test_cases/my_data.csv --pipeline oed-quotations --workers 8
```

---

## Real-World Example

### The Problem

```bash
# User creates test data in Excel, saves as "CSV (Comma delimited)"
# Excel silently adds BOM

# User runs test
python benchmark_pipeline.py \
    --test-data test_cases/1000_cases.csv \
    --pipeline oed-quotations \
    --workers 8

# Output:
# Error: No test cases loaded
# Or: UnicodeDecodeError
# Result: 20 minutes wasted!
```

### The Solution

```bash
# ALWAYS check first!
head -c 4 test_cases/1000_cases.csv | od -An -tx1
# Output: ef bb bf 65  (HAS BOM!)

# Fix it
tail -c +4 test_cases/1000_cases.csv > test_cases/1000_cases_fixed.csv

# Verify fix
head -c 4 test_cases/1000_cases_fixed.csv | od -An -tx1
# Output: 65 6e 74 72  (NO BOM!)

# Now run successfully
python benchmark_pipeline.py \
    --test-data test_cases/1000_cases_fixed.csv \
    --pipeline oed-quotations \
    --workers 8

# Output: ✅ Success!
```

---

## Summary Checklist

Before running any test:

- [ ] Check for BOM: `head -c 4 <file>.csv | od -An -tx1`
- [ ] If BOM found: `tail -c +4 <file>.csv > <file>_fixed.csv`
- [ ] Verify fix: `head -c 4 <file>_fixed.csv | od -An -tx1`
- [ ] Run test with fixed file

**Time saved**: 10-30 minutes per test run!

---

## Quick Reference Card

```
═══════════════════════════════════════════════════════════
              BOM PREVENTION QUICK REFERENCE
═══════════════════════════════════════════════════════════

CHECK:
  head -c 4 file.csv | od -An -tx1

GOOD OUTPUT (no BOM):
  65 6e 74 72

BAD OUTPUT (has BOM):
  ef bb bf 65

FIX:
  tail -c +4 file.csv > file_fixed.csv

VERIFY:
  head -c 4 file_fixed.csv | od -An -tx1
  (should show: 65 6e 74 72)

PREVENT:
  ✅ Use Google Sheets
  ✅ Use VS Code / Notepad++
  ❌ Don't use Excel CSV export
  ❌ Don't use Windows Notepad

═══════════════════════════════════════════════════════════
```

Print this and keep it next to your workstation! 📋
