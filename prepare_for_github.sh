#!/bin/bash

# Script to prepare the repository for GitHub release
# This removes all test results, debug files, and sensitive data

set -e  # Exit on error

echo "================================================================================"
echo "PIPELINE BENCHMARKING - GitHub Release Preparation"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Remove all test results and checkpoints"
echo "  2. Remove debug and temporary scripts"
echo "  3. Clean Python cache files"
echo "  4. Remove environment files (.env)"
echo "  5. Keep only sample test data"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""
echo "Starting cleanup..."
echo ""

# 1. Clean all test results
echo "[1/6] Cleaning test results..."
rm -rf results/checkpoints/* 2>/dev/null || true
rm -rf results/raw_results/* 2>/dev/null || true
rm -rf results/reports/* 2>/dev/null || true
rm -f results/*.csv results/*.xlsx results/*.txt 2>/dev/null || true
rm -rf results/*/
find results/ -mindepth 1 -type f ! -name '.gitkeep' -delete 2>/dev/null || true
echo "  ✓ Test results cleaned"

# 2. Clean test data (keep only sample)
echo "[2/6] Cleaning test data (keeping sample_test_cases.csv)..."
find test_cases/ -name "*.csv" ! -name "sample_test_cases.csv" -delete 2>/dev/null || true
find test_cases/ -name "*.json" -delete 2>/dev/null || true
find test_cases/ -name "*.txt" -delete 2>/dev/null || true
echo "  ✓ Test data cleaned"

# 3. Remove debug scripts
echo "[3/6] Removing debug scripts..."
rm -f debug_*.py 2>/dev/null || true
rm -f test_counting.py test_matching.py 2>/dev/null || true
rm -f validate_framework.py verify_pipelines.py 2>/dev/null || true
rm -f inspect_response.py 2>/dev/null || true
echo "  ✓ Debug scripts removed"

# 4. Clean Python cache
echo "[4/6] Cleaning Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type f -name "*.egg-info" -delete 2>/dev/null || true
echo "  ✓ Python cache cleaned"

# 5. Remove environment file
echo "[5/6] Removing .env file (credentials)..."
if [ -f .env ]; then
    rm -f .env
    echo "  ✓ .env removed"
else
    echo "  ℹ .env not found (already clean)"
fi

# 6. Remove IDE and OS files
echo "[6/6] Cleaning IDE and OS files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
find . -name "Thumbs.db" -delete 2>/dev/null || true
find . -name "*.swp" -delete 2>/dev/null || true
find . -name "*.swo" -delete 2>/dev/null || true
echo "  ✓ IDE/OS files cleaned"

echo ""
echo "================================================================================"
echo "✅ Cleanup Complete!"
echo "================================================================================"
echo ""
echo "Repository is ready for GitHub. Next steps:"
echo ""
echo "1. Review what will be committed:"
echo "   git status"
echo ""
echo "2. Add all files:"
echo "   git add -A"
echo ""
echo "3. Check staged files:"
echo "   git status"
echo ""
echo "4. Create initial commit:"
echo "   git commit -m 'Initial commit: Pipeline benchmarking framework v1.0.0'"
echo ""
echo "5. Push to GitHub:"
echo "   git remote add origin https://github.com/yourusername/your-repo.git"
echo "   git push -u origin main"
echo ""
echo "================================================================================"
