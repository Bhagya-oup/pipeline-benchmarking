# How to Release to GitHub

## 🚀 Quick Release (Recommended)

The easiest way to prepare your repository for GitHub:

```bash
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking

# Run the automated setup script
./quick_start_github.sh
```

This script will:
1. ✅ Verify you're in the correct directory
2. ✅ Clean all test results and sensitive data
3. ✅ Initialize git ONLY in pipeline_benchmarking folder
4. ✅ Stage all appropriate files
5. ✅ Run safety tests to ensure no parent files are included
6. ✅ Show you exactly what will be committed

Then just follow the on-screen instructions to commit and push!

---

## 📋 Manual Release (Step by Step)

If you prefer to do it manually:

### Step 1: Clean Repository

```bash
cd pipeline_benchmarking
./prepare_for_github.sh
```

### Step 2: Initialize Git

```bash
# Initialize git in THIS folder only
git init

# Verify correct location
git rev-parse --show-toplevel
# Should show: .../rare_senses/pipeline_benchmarking
```

### Step 3: Check for BOM in CSV Files

```bash
# Check all CSV files for BOM (can cause parsing errors)
./check_bom.sh

# If any files have BOM, fix them before committing
```

**Why**: BOM (Byte Order Mark) in CSV files causes parsing failures for users. Make sure sample files are BOM-free!

### Step 4: Test Isolation

```bash
# Run safety tests
./test_git_isolation.sh
```

This verifies:
- ✅ Git is initialized in pipeline_benchmarking only
- ✅ No parent directory files will be included
- ✅ No sensitive files (.env) will be committed
- ✅ All essential files are staged

### Step 5: Stage Files

```bash
git add -A
git status  # Review what will be committed
```

### Step 6: Create Commit

```bash
git commit -m "Initial commit: Pipeline benchmarking framework v1.0.0

Features:
- Parallel pipeline comparison with 4-8 workers
- Checkpoint-based resumability
- CSV/Excel/TXT comprehensive reporting
- Fixed type mismatch bug in match counting
- Validated framework with 3-way comparison tests"
```

### Step 7: Push to GitHub

```bash
# Create repository on GitHub first, then:
git remote add origin https://github.com/yourusername/pipeline-benchmarking.git
git branch -M main
git push -u origin main
```

---

## 🔒 Safety Guarantees

### What Will Be Included ✅

- All source code (`src/*.py`)
- CLI tools (`compare_pipelines.py`, etc.)
- Documentation (all `*.md` files)
- Configuration templates (`.env.template`)
- Sample test data (`sample_test_cases.csv`)
- Requirements file

### What Will Be Excluded ❌

- All test results in `results/`
- Your actual test data in `test_cases/`
- `.env` file with credentials
- Python cache files
- Debug scripts
- **ALL files from parent `rare_senses/` directory**

---

## 🧪 Verification Commands

After running the setup, verify everything is correct:

```bash
# 1. Check git root
git rev-parse --show-toplevel
# Should be: /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking

# 2. Verify no parent files
git ls-files | grep '\.\.\/'
# Should return nothing

# 3. Check for sensitive files
git ls-files | grep '\.env$'
# Should return nothing (only .env.template is OK)

# 4. Count files
git ls-files | wc -l
# Should be 30-50 files
```

---

## ⚠️ Important Notes

### Git Scope

**CORRECT** ✅ - Git initialized in pipeline_benchmarking:
```
rare_senses/
└── pipeline_benchmarking/
    ├── .git/              ← Git repository HERE
    ├── src/
    └── README.md
```

**WRONG** ❌ - Git initialized in parent:
```
rare_senses/
├── .git/                  ← Git repository HERE (wrong!)
├── scripts/               ← Would be included!
└── pipeline_benchmarking/
```

### If You Make a Mistake

If you accidentally initialized git in the wrong place:

```bash
# Remove git
rm -rf .git

# Navigate to correct folder
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking

# Run quick start again
./quick_start_github.sh
```

---

## 📚 Additional Documentation

- **`STANDALONE_REPOSITORY.md`** - Detailed isolation guide
- **`GITHUB_RELEASE.md`** - Complete release checklist
- **`RELEASE_SUMMARY.md`** - Executive summary and features
- **`test_git_isolation.sh`** - Automated safety tests
- **`prepare_for_github.sh`** - Cleanup script

---

## ✅ Final Checklist

Before pushing to GitHub:

- [ ] Ran `./quick_start_github.sh` OR manual steps above
- [ ] All tests passed (no errors from `test_git_isolation.sh`)
- [ ] Reviewed `git status` output
- [ ] No parent directory files in `git ls-files`
- [ ] No `.env` file in `git ls-files`
- [ ] Git root is in `pipeline_benchmarking` folder
- [ ] Created initial commit
- [ ] GitHub repository created
- [ ] Ready to push!

---

## 🎯 One-Line Release (Advanced)

If you're confident and want to do everything in one go:

```bash
cd /Users/bhagya.kakkanatshibu/rare_senses/pipeline_benchmarking && \
./quick_start_github.sh && \
git commit -m "Initial commit: Pipeline benchmarking framework v1.0.0" && \
echo "✅ Ready to push! Run: git remote add origin <your-repo-url> && git push -u origin main"
```

---

## 🆘 Troubleshooting

**Problem**: Test script shows parent directory files

**Solution**:
```bash
rm -rf .git
./quick_start_github.sh
```

**Problem**: `.env` file is staged

**Solution**:
```bash
git rm --cached .env
echo ".env" >> .gitignore
git add .gitignore
```

**Problem**: Too many files (100+)

**Solution**: You likely included parent directory
```bash
rm -rf .git
./quick_start_github.sh
```

---

## 🎉 After Release

Once pushed to GitHub:

1. **Create a Release**
   - Go to your repository → Releases → Create new release
   - Tag: `v1.0.0`
   - Title: "Pipeline Benchmarking Framework v1.0.0"
   - Copy description from `RELEASE_SUMMARY.md`

2. **Add Topics** (helps discoverability)
   - deepset-cloud
   - haystack
   - benchmarking
   - nlp
   - testing-framework

3. **Update README Badge** (optional)
   - Add build status
   - Add license badge
   - Add version badge

4. **Share**
   - Deepset community forum
   - LinkedIn/Twitter
   - Internal team channels

---

## 📞 Questions?

If you encounter any issues during release, refer to:
- `STANDALONE_REPOSITORY.md` for detailed troubleshooting
- Run `./test_git_isolation.sh` to diagnose problems
- Check git status with `git status` and `git ls-files`
