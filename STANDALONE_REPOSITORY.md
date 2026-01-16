# Standalone Repository Setup

This guide ensures that ONLY the `pipeline_benchmarking` folder is included in the GitHub repository, keeping it completely separate from the parent `rare_senses` project.

## ✅ Current Status

- ✅ No git repository in `pipeline_benchmarking/`
- ✅ No git repository in parent `rare_senses/`
- ✅ Ready to create standalone repository

## 🎯 Goal

Create a git repository that includes ONLY:
```
pipeline_benchmarking/
├── src/
├── test_cases/
├── results/
├── *.py
├── *.md
└── requirements.txt
```

**NOT the parent directory:**
```
rare_senses/                    ← NOT INCLUDED
├── scripts/                    ← NOT INCLUDED
├── dc_custom_component/        ← NOT INCLUDED
└── pipeline_benchmarking/      ← ONLY THIS FOLDER
```

## 📋 Step-by-Step Setup

### Step 1: Clean the Repository

```bash
# Make sure you're in the pipeline_benchmarking folder
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking

# Verify current directory
pwd
# Should output: /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking

# Run cleanup script
./prepare_for_github.sh
```

### Step 2: Initialize Git (ONLY in this folder)

```bash
# Initialize git repository in THIS folder only
git init

# Verify git was initialized in the correct location
git rev-parse --show-toplevel
# Should output: /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking
```

### Step 3: Verify Git Scope

```bash
# Check git status - should show files ONLY from pipeline_benchmarking
git status

# You should see:
# - src/*.py
# - *.py (compare_pipelines.py, etc.)
# - *.md (README.md, etc.)
# - requirements.txt
# - .gitignore
# - .env.template

# You should NOT see:
# - ../scripts/
# - ../dc_custom_component/
# - ../pipelines/
```

### Step 4: Review What Will Be Committed

```bash
# Stage all files
git add -A

# Check what's staged (IMPORTANT!)
git status

# Review file list
git ls-files
```

**Verify the output includes ONLY pipeline_benchmarking files:**
- ✅ Should include: `src/config.py`, `compare_pipelines.py`, `README.md`
- ❌ Should NOT include: `../scripts/`, `../dc_custom_component/`

### Step 5: Create Initial Commit

```bash
git commit -m "Initial commit: Pipeline benchmarking framework v1.0.0

Features:
- Parallel pipeline comparison with 4-8 workers
- Checkpoint-based resumability
- CSV/Excel/TXT comprehensive reporting
- Fixed type mismatch bug in match counting
- Validated framework with 3-way comparison tests"
```

### Step 6: Connect to GitHub

```bash
# Create a NEW repository on GitHub first, then:
git remote add origin https://github.com/yourusername/pipeline-benchmarking.git

# Verify remote
git remote -v

# Push to GitHub
git push -u origin main

# Or if main branch doesn't exist:
git branch -M main
git push -u origin main
```

## 🔒 Safety Checks

### Before Pushing to GitHub

Run these commands to ensure only pipeline_benchmarking files are included:

```bash
# 1. Check git root directory
git rev-parse --show-toplevel
# ✅ Should be: /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking
# ❌ Should NOT be: /Users/bhagya.kakkanatshibu/rare_senses

# 2. List all files that will be committed
git ls-files | head -20
# ✅ Should show: src/config.py, README.md, compare_pipelines.py
# ❌ Should NOT show: scripts/, dc_custom_component/

# 3. Check for sensitive files
git ls-files | grep -E '\.env$|credentials|api.*key'
# ✅ Should show: .env.template (OK)
# ❌ Should NOT show: .env (actual credentials)

# 4. Verify parent directory is not tracked
ls -la ../.git
# ✅ Should show: "No such file or directory"
# ❌ If .git exists in parent, you initialized git in wrong location!
```

## ⚠️ Common Mistakes to Avoid

### ❌ MISTAKE 1: Initializing git in parent directory
```bash
# WRONG! Don't do this:
cd /Users/bhagya.kakkanatshibu/rare_senses
git init  # ❌ This would include everything!
```

### ❌ MISTAKE 2: Adding parent directory files
```bash
# WRONG! Don't do this:
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking
git init
git add ..  # ❌ This adds parent directory!
```

### ✅ CORRECT WAY
```bash
# CORRECT! Do this:
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking
git init   # ✅ Only this folder
git add -A # ✅ Only adds files in THIS folder
```

## 🧪 Test Your Setup

After initializing git, run this test:

```bash
# Test script to verify isolation
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking

echo "=== Git Repository Test ==="
echo ""

# Test 1: Git root location
echo "1. Git root directory:"
git rev-parse --show-toplevel
echo "   Expected: /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking"
echo ""

# Test 2: File count
echo "2. Number of tracked files:"
git ls-files | wc -l
echo "   Expected: 30-50 files (only from pipeline_benchmarking)"
echo ""

# Test 3: Check for parent files
echo "3. Checking for parent directory files (should be empty):"
git ls-files | grep -E '^\.\./|^scripts/|^dc_custom_component/' || echo "   ✅ No parent files found!"
echo ""

# Test 4: Check for sensitive files
echo "4. Checking for sensitive files (should only show .env.template):"
git ls-files | grep -E '\.env|credential|api.*key'
echo "   Expected: .env.template only"
echo ""

# Test 5: Verify .gitignore is working
echo "5. Verifying .gitignore (should be empty):"
git status --porcelain | grep -E 'results/.*\.csv|\.env$|__pycache__' || echo "   ✅ .gitignore working correctly!"
echo ""

echo "=== Test Complete ==="
```

Save this as `test_git_isolation.sh` and run it:
```bash
chmod +x test_git_isolation.sh
./test_git_isolation.sh
```

## 📊 Expected Output

After running `git ls-files`, you should see approximately 30-50 files like:

```
.env.template
.gitignore
CHANGELOG.md
GETTING_STARTED.md
GITHUB_RELEASE.md
MIGRATION_GUIDE.md
README.md
README_SINGLE_PIPELINE.md
RELEASE_SUMMARY.md
STANDALONE_REPOSITORY.md
analyze_results.py
benchmark_pipeline.py
compare_pipelines.py
compare_results.py
prepare_for_github.sh
requirements.txt
src/__init__.py
src/checkpoint_manager.py
src/config.py
src/fetch_from_hero_quotations.py
src/metrics_calculator.py
src/parallel_runner.py
src/pipeline_executor.py
src/report_generator.py
src/single_pipeline_report.py
src/single_pipeline_runner.py
src/test_case_loader.py
test_cases/.gitkeep
test_cases/sample_test_cases.csv
results/.gitkeep
```

**You should NOT see:**
- `../scripts/`
- `../dc_custom_component/`
- `../pipelines/`
- Any files from parent directory

## 🎯 Quick Verification Checklist

Before pushing to GitHub, confirm:

- [ ] `git rev-parse --show-toplevel` shows `/Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking`
- [ ] `git ls-files | grep '\.\./`' returns nothing (no parent files)
- [ ] `git ls-files | grep '\.env$'` returns nothing (no credentials)
- [ ] `git status` shows no files from parent directory
- [ ] `ls -la ../.git` shows "No such file or directory"
- [ ] All files in `git ls-files` are from pipeline_benchmarking only

## 💡 Why This Matters

**Correct Setup (Standalone):**
```
rare_senses/                           (no .git here)
└── pipeline_benchmarking/             (.git initialized HERE)
    ├── .git/                          ✅ Repository root
    ├── src/                           ✅ Included
    ├── README.md                      ✅ Included
    └── ...                            ✅ Included
```

**Wrong Setup (Would include parent):**
```
rare_senses/                           (.git here - WRONG!)
├── .git/                              ❌ Would include everything!
├── scripts/                           ❌ Would be included
├── dc_custom_component/               ❌ Would be included
└── pipeline_benchmarking/             ❌ Just one of many folders
    └── ...
```

## 🔄 If You Made a Mistake

If you accidentally initialized git in the wrong location:

```bash
# Remove git repository
rm -rf .git

# Navigate to correct folder
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking

# Verify you're in the right place
pwd

# Initialize git again in correct location
git init
```

## ✅ Final Confirmation

Run this one-liner to confirm everything is correct:

```bash
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking && \
git rev-parse --show-toplevel 2>/dev/null | grep -q "pipeline_benchmarking$" && \
! ls -la ../.git 2>/dev/null >/dev/null && \
echo "✅ Git is correctly initialized in pipeline_benchmarking folder only!" || \
echo "❌ WARNING: Git configuration needs review!"
```

Expected output: `✅ Git is correctly initialized in pipeline_benchmarking folder only!`

---

## 📞 Need Help?

If you see parent directory files in `git ls-files`, STOP and review this guide before pushing to GitHub.
