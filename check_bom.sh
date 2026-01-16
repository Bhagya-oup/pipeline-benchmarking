#!/bin/bash

# Script to check all CSV files for BOM (Byte Order Mark)
# BOM causes CSV parsing failures - always check before running tests!

echo "================================================================================"
echo "BOM (Byte Order Mark) Checker"
echo "================================================================================"
echo ""
echo "Checking all CSV files in test_cases/ for BOM..."
echo ""

HAS_BOM=0
TOTAL_FILES=0

# Check if test_cases directory exists
if [ ! -d "test_cases" ]; then
    echo "⚠️  test_cases/ directory not found"
    exit 1
fi

# Check all CSV files
for file in test_cases/*.csv; do
    # Skip if no CSV files found
    if [ ! -f "$file" ]; then
        continue
    fi

    TOTAL_FILES=$((TOTAL_FILES + 1))

    # Check first 3 bytes for BOM (EF BB BF)
    BOM=$(head -c 3 "$file" | od -An -tx1 | tr -d ' ')

    if [ "$BOM" = "efbbbf" ]; then
        echo "❌ HAS BOM:  $(basename "$file")"
        HAS_BOM=$((HAS_BOM + 1))
    else
        echo "✅ No BOM:   $(basename "$file")"
    fi
done

echo ""
echo "================================================================================"
echo "SUMMARY"
echo "================================================================================"
echo ""
echo "Total CSV files checked: $TOTAL_FILES"
echo "Files with BOM: $HAS_BOM"
echo "Files without BOM: $((TOTAL_FILES - HAS_BOM))"
echo ""

if [ $TOTAL_FILES -eq 0 ]; then
    echo "ℹ️  No CSV files found in test_cases/"
    echo ""
    exit 0
elif [ $HAS_BOM -eq 0 ]; then
    echo "✅ All CSV files are BOM-free!"
    echo ""
    echo "You're ready to run tests safely."
    exit 0
else
    echo "❌ Found $HAS_BOM file(s) with BOM"
    echo ""
    echo "BOM causes CSV parsing failures!"
    echo ""
    echo "To fix these files, run:"
    echo "────────────────────────────────────────────────────────────────"
    for file in test_cases/*.csv; do
        if [ -f "$file" ]; then
            BOM=$(head -c 3 "$file" | od -An -tx1 | tr -d ' ')
            if [ "$BOM" = "efbbbf" ]; then
                BASENAME=$(basename "$file" .csv)
                echo "tail -c +4 test_cases/$BASENAME.csv > test_cases/${BASENAME}_fixed.csv"
            fi
        fi
    done
    echo ""
    echo "Or use this one-liner to fix all files:"
    echo "────────────────────────────────────────────────────────────────"
    echo "for f in test_cases/*.csv; do tail -c +4 \"\$f\" > \"\${f%.csv}_fixed.csv\"; done"
    echo ""
    echo "See BOM_PREVENTION_GUIDE.md for detailed help."
    echo ""
    exit 1
fi
