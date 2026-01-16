#!/bin/bash

# Quick start script to prepare and initialize git for GitHub release
# This script does everything needed to get ready for GitHub

set -e  # Exit on error

echo "================================================================================"
echo "QUICK START: GitHub Repository Setup"
echo "================================================================================"
echo ""
echo "This script will:"
echo "  1. Verify you're in the correct directory"
echo "  2. Clean all test results and sensitive data"
echo "  3. Check CSV files for BOM (prevents user errors)"
echo "  4. Initialize git repository (ONLY in pipeline_benchmarking)"
echo "  5. Stage all files"
echo "  6. Run isolation tests"
echo "  7. Show you what will be committed"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

echo ""

# Step 1: Verify directory
echo "[1/6] Verifying directory..."
CURRENT_DIR=$(pwd)
if [[ "$CURRENT_DIR" != *"/pipeline_benchmarking" ]]; then
    echo "❌ ERROR: You must run this script from the pipeline_benchmarking folder"
    echo "   Current: $CURRENT_DIR"
    echo "   Expected: .../rare_senses/pipeline_benchmarking"
    exit 1
fi
echo "  ✓ Correct directory: $CURRENT_DIR"
echo ""

# Step 2: Run cleanup
echo "[2/7] Running cleanup script..."
if [ -f "prepare_for_github.sh" ]; then
    # Run cleanup without prompts
    echo "y" | ./prepare_for_github.sh > /dev/null 2>&1 || true
    echo "  ✓ Cleanup complete"
else
    echo "  ⚠️  prepare_for_github.sh not found, skipping cleanup"
fi
echo ""

# Step 3: Check for BOM in CSV files
echo "[3/7] Checking CSV files for BOM..."
if [ -f "check_bom.sh" ]; then
    if ./check_bom.sh > /dev/null 2>&1; then
        echo "  ✓ All CSV files are BOM-free"
    else
        echo "  ⚠️  WARNING: Some CSV files have BOM!"
        echo "     BOM causes parsing errors for users."
        echo "     Fix with: tail -c +4 <file>.csv > <file>_fixed.csv"
        echo ""
        read -p "  Continue anyway? (y/n) " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "  Aborted. Fix BOM issues and run again."
            exit 1
        fi
    fi
else
    echo "  ⚠️  check_bom.sh not found, skipping BOM check"
fi
echo ""

# Step 4: Check if git is already initialized
echo "[4/7] Checking git status..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    GIT_ROOT=$(git rev-parse --show-toplevel)
    echo "  ℹ️  Git already initialized"
    echo "     Git root: $GIT_ROOT"

    # Verify it's in the correct location
    if [[ "$GIT_ROOT" != *"/pipeline_benchmarking" ]]; then
        echo ""
        echo "  ❌ ERROR: Git is initialized in the WRONG location!"
        echo "     Current: $GIT_ROOT"
        echo "     Expected: .../pipeline_benchmarking"
        echo ""
        read -p "  Remove .git and reinitialize here? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf .git
            echo "  ✓ Removed incorrect .git folder"
        else
            echo "  Aborted. Please fix git initialization manually."
            exit 1
        fi
    else
        echo "  ✓ Git is in correct location"
    fi
else
    echo "  ℹ️  Git not initialized yet"
fi
echo ""

# Step 5: Initialize git if needed
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "[5/7] Initializing git repository..."
    git init
    GIT_ROOT=$(git rev-parse --show-toplevel)
    echo "  ✓ Git initialized in: $GIT_ROOT"
else
    echo "[5/7] Git already initialized, skipping..."
fi
echo ""

# Step 6: Stage all files
echo "[6/7] Staging files..."
git add -A
FILE_COUNT=$(git diff --cached --numstat | wc -l | tr -d ' ')
echo "  ✓ Staged $FILE_COUNT files"
echo ""

# Step 7: Run isolation tests
echo "[7/7] Running isolation tests..."
if [ -f "test_git_isolation.sh" ]; then
    ./test_git_isolation.sh
    TEST_RESULT=$?

    if [ $TEST_RESULT -eq 0 ]; then
        echo ""
        echo "================================================================================"
        echo "✅ SUCCESS! Repository is ready for GitHub"
        echo "================================================================================"
        echo ""
        echo "Files staged for commit:"
        echo "────────────────────────────────────────────────────────────────"
        git diff --cached --name-only | head -20
        TOTAL_FILES=$(git diff --cached --name-only | wc -l | tr -d ' ')
        if [ "$TOTAL_FILES" -gt 20 ]; then
            echo "   ... and $((TOTAL_FILES - 20)) more files"
        fi
        echo ""
        echo "Next steps:"
        echo "────────────────────────────────────────────────────────────────"
        echo ""
        echo "1. Review what will be committed:"
        echo "   git status"
        echo ""
        echo "2. Create initial commit:"
        echo "   git commit -m 'Initial commit: Pipeline benchmarking framework v1.0.0'"
        echo ""
        echo "3. Create GitHub repository (if not already done):"
        echo "   - Go to github.com/new"
        echo "   - Name: pipeline-benchmarking"
        echo "   - Description: Automated benchmarking for Deepset pipelines"
        echo "   - Make it public or private"
        echo "   - Do NOT initialize with README (we have one)"
        echo ""
        echo "4. Connect to GitHub:"
        echo "   git remote add origin https://github.com/yourusername/pipeline-benchmarking.git"
        echo ""
        echo "5. Push to GitHub:"
        echo "   git branch -M main"
        echo "   git push -u origin main"
        echo ""
        echo "================================================================================"
    else
        echo ""
        echo "================================================================================"
        echo "❌ TESTS FAILED"
        echo "================================================================================"
        echo ""
        echo "Please review the errors above and fix them before proceeding."
        echo "See STANDALONE_REPOSITORY.md for detailed troubleshooting."
        echo ""
        exit 1
    fi
else
    echo "  ⚠️  test_git_isolation.sh not found, skipping tests"
    echo ""
    echo "Next steps:"
    echo "  1. Review staged files: git status"
    echo "  2. Create commit: git commit -m 'Initial commit'"
fi
