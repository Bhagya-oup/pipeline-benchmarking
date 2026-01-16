#!/bin/bash

# Test script to verify git is correctly isolated to pipeline_benchmarking folder only

echo "================================================================================"
echo "GIT ISOLATION TEST"
echo "================================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0

# Test 1: Check if git is initialized
echo "Test 1: Git Repository Initialization"
echo "--------------------------------------"
if git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Git repository is initialized${NC}"

    # Get git root
    GIT_ROOT=$(git rev-parse --show-toplevel)
    echo "   Git root: $GIT_ROOT"

    # Check if it's in the correct location
    if [[ "$GIT_ROOT" == *"/pipeline_benchmarking" ]]; then
        echo -e "   ${GREEN}✅ Git root is in pipeline_benchmarking folder${NC}"
    else
        echo -e "   ${RED}❌ ERROR: Git root is NOT in pipeline_benchmarking folder!${NC}"
        echo "   Current root: $GIT_ROOT"
        echo "   Expected: .../rare_senses/pipeline_benchmarking"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}⚠️  Git is not initialized yet${NC}"
    echo "   Run 'git init' in the pipeline_benchmarking folder"
    exit 0
fi
echo ""

# Test 2: Check parent directory doesn't have git
echo "Test 2: Parent Directory Check"
echo "--------------------------------------"
if [ -d "../.git" ]; then
    echo -e "${RED}❌ ERROR: Parent directory has a .git folder!${NC}"
    echo "   This means git was initialized in the wrong location"
    echo "   Remove ../. git and initialize only in pipeline_benchmarking"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ Parent directory has no .git folder${NC}"
fi
echo ""

# Test 3: Check file count
echo "Test 3: Tracked Files Count"
echo "--------------------------------------"
FILE_COUNT=$(git ls-files | wc -l | tr -d ' ')
echo "   Files tracked by git: $FILE_COUNT"

if [ "$FILE_COUNT" -lt 20 ]; then
    echo -e "   ${YELLOW}⚠️  Warning: Very few files tracked (expected 30-50)${NC}"
    echo "   Run 'git add -A' to stage all files"
elif [ "$FILE_COUNT" -gt 100 ]; then
    echo -e "   ${RED}❌ ERROR: Too many files tracked!${NC}"
    echo "   This might include parent directory files"
    ERRORS=$((ERRORS + 1))
else
    echo -e "   ${GREEN}✅ File count looks reasonable (30-50 expected)${NC}"
fi
echo ""

# Test 4: Check for parent directory files
echo "Test 4: Parent Directory Files Check"
echo "--------------------------------------"
PARENT_FILES=$(git ls-files | grep -E '^\.\./|^scripts/|^dc_custom_component/|^pipelines/' | wc -l | tr -d ' ')

if [ "$PARENT_FILES" -gt 0 ]; then
    echo -e "${RED}❌ ERROR: Found files from parent directory!${NC}"
    echo "   Number of parent files: $PARENT_FILES"
    echo ""
    echo "   Sample parent files found:"
    git ls-files | grep -E '^\.\./|^scripts/|^dc_custom_component/|^pipelines/' | head -10
    echo ""
    echo "   ACTION REQUIRED:"
    echo "   1. Remove git: rm -rf .git"
    echo "   2. Reinitialize in correct folder: git init"
    echo "   3. Stage only current folder: git add -A"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ No parent directory files found${NC}"
fi
echo ""

# Test 5: Check for sensitive files
echo "Test 5: Sensitive Files Check"
echo "--------------------------------------"
SENSITIVE_FILES=$(git ls-files | grep -E '\.env$|credential|secret|password' | grep -v '.env.template')

if [ -z "$SENSITIVE_FILES" ]; then
    echo -e "${GREEN}✅ No sensitive files found (.env.template is OK)${NC}"
else
    echo -e "${RED}❌ ERROR: Found sensitive files!${NC}"
    echo "$SENSITIVE_FILES"
    echo ""
    echo "   ACTION REQUIRED:"
    echo "   1. Remove from git: git rm --cached .env"
    echo "   2. Update .gitignore to exclude .env"
    ERRORS=$((ERRORS + 1))
fi
echo ""

# Test 6: Check .gitignore is working
echo "Test 6: .gitignore Effectiveness"
echo "--------------------------------------"
UNTRACKED_SENSITIVE=$(git status --porcelain | grep -E 'results/.*\.(csv|xlsx)|\.env$|__pycache__')

if [ -z "$UNTRACKED_SENSITIVE" ]; then
    echo -e "${GREEN}✅ .gitignore is working correctly${NC}"
    echo "   No results files or .env in untracked files"
else
    echo -e "${YELLOW}⚠️  Warning: Found sensitive untracked files:${NC}"
    echo "$UNTRACKED_SENSITIVE"
    echo "   These files should be in .gitignore"
fi
echo ""

# Test 7: Verify key files are included
echo "Test 7: Essential Files Check"
echo "--------------------------------------"
ESSENTIAL_FILES=(
    "README.md"
    "requirements.txt"
    ".gitignore"
    ".env.template"
    "compare_pipelines.py"
    "src/config.py"
    "src/pipeline_executor.py"
)

MISSING_FILES=0
for file in "${ESSENTIAL_FILES[@]}"; do
    if git ls-files | grep -q "^$file$"; then
        echo -e "   ${GREEN}✅${NC} $file"
    else
        echo -e "   ${RED}❌${NC} $file (missing - run 'git add $file')"
        MISSING_FILES=$((MISSING_FILES + 1))
    fi
done

if [ "$MISSING_FILES" -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Warning: $MISSING_FILES essential files not staged${NC}"
    echo "   Run 'git add -A' to stage all files"
fi
echo ""

# Test 8: Sample of tracked files
echo "Test 8: Sample Tracked Files"
echo "--------------------------------------"
echo "First 15 tracked files:"
git ls-files | head -15 | while read file; do
    echo "   - $file"
done
echo "   ..."
echo ""

# Final summary
echo "================================================================================"
echo "TEST SUMMARY"
echo "================================================================================"
echo ""

if [ "$ERRORS" -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED!${NC}"
    echo ""
    echo "Your git repository is correctly isolated to pipeline_benchmarking folder."
    echo "It's safe to push to GitHub."
    echo ""
    echo "Next steps:"
    echo "  1. Review staged files: git status"
    echo "  2. Create commit: git commit -m 'Initial commit'"
    echo "  3. Push to GitHub: git push -u origin main"
else
    echo -e "${RED}❌ ERRORS FOUND: $ERRORS${NC}"
    echo ""
    echo "Please fix the errors above before pushing to GitHub."
    echo "See STANDALONE_REPOSITORY.md for detailed instructions."
fi

echo ""
echo "================================================================================"

exit $ERRORS
