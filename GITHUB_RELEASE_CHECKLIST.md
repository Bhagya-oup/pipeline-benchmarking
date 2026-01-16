# GitHub Release Checklist

Use this checklist to ensure a clean, error-free release to GitHub.

## ✅ Pre-Release Checklist

### 1. Documentation Review
- [ ] README.md is up to date with correct examples
- [ ] GETTING_STARTED.md has clear instructions
- [ ] All pipeline names in examples are generic (not project-specific)
- [ ] License information is included (if applicable)

### 2. Code Review
- [ ] No hardcoded credentials in any files
- [ ] No API keys or tokens in code
- [ ] All debug scripts removed or properly documented
- [ ] Type mismatch bug fix is documented (lines 194-213 in pipeline_executor.py)

### 3. Test Data Review
- [ ] **CRITICAL: Check all CSV files for BOM**
  ```bash
  ./check_bom.sh
  ```
- [ ] Only sample test data included (not actual project data)
- [ ] Sample CSV files are properly formatted
- [ ] No proprietary sense IDs in sample data

### 4. Environment Configuration
- [ ] `.env` file is NOT present (deleted)
- [ ] `.env.template` exists and is correct
- [ ] All required environment variables documented in template
- [ ] No secrets in .env.template (only placeholders)

### 5. Results and Checkpoints
- [ ] All test results cleaned from `results/`
- [ ] All checkpoints removed
- [ ] Only `.gitkeep` files remain in results/
- [ ] No CSV/Excel files in results/

### 6. Dependencies
- [ ] `requirements.txt` is complete and up to date
- [ ] No unnecessary dependencies included
- [ ] Version numbers specified where needed

---

## 🚀 Release Steps

### Step 1: Clean Repository
```bash
cd pipeline_benchmarking
./prepare_for_github.sh
```
- [ ] Script completed without errors
- [ ] Verified `.env` is deleted
- [ ] Verified results/ is empty

### Step 2: Check for BOM (CRITICAL!)
```bash
./check_bom.sh
```
- [ ] All CSV files are BOM-free
- [ ] If BOM found, fixed with: `tail -c +4 <file>.csv > <file>_fixed.csv`
- [ ] Re-ran check to verify fix

**Why this matters**: BOM causes parsing failures for users. This is the #1 issue!

### Step 3: Initialize Git
```bash
git init
```
- [ ] Git initialized in `pipeline_benchmarking/` folder ONLY
- [ ] Verified with: `git rev-parse --show-toplevel`
- [ ] Output ends with `/pipeline_benchmarking`

### Step 4: Verify No Parent Files
```bash
git rev-parse --show-toplevel
# Should be: .../pipeline_benchmarking (NOT .../rare_senses)
```
- [ ] Git root is correct location
- [ ] No `.git` folder in parent directory

### Step 5: Stage Files
```bash
git add -A
git status
```
- [ ] Review staged files carefully
- [ ] No `.env` file staged
- [ ] No `results/*.csv` files staged
- [ ] No parent directory files staged (no `../` paths)

### Step 6: Run Safety Tests
```bash
./test_git_isolation.sh
```
- [ ] All tests passed
- [ ] No parent directory files found
- [ ] No sensitive files found
- [ ] File count is 30-50 files

### Step 7: Final Manual Verification
```bash
# Check for parent files
git ls-files | grep '\.\.\/' || echo "✅ No parent files"

# Check for sensitive files
git ls-files | grep '\.env$' || echo "✅ No .env file"

# Check file count
git ls-files | wc -l
# Should be 30-50 files
```
- [ ] No parent files (`../`)
- [ ] No `.env` file
- [ ] Reasonable file count (30-50)

### Step 8: Create Commit
```bash
git commit -m "Initial commit: Pipeline benchmarking framework v1.0.0

Features:
- Parallel pipeline comparison with 4-8 workers
- Checkpoint-based resumability
- CSV/Excel/TXT comprehensive reporting
- Fixed type mismatch bug in match counting
- Validated framework with 3-way comparison tests
- BOM prevention documentation and tools"
```
- [ ] Commit created successfully
- [ ] Commit message is descriptive

### Step 9: Create GitHub Repository
On GitHub:
- [ ] Created new repository
- [ ] Named: `pipeline-benchmarking` or similar
- [ ] Description added
- [ ] Public or Private selected
- [ ] **NOT** initialized with README (we have one)

### Step 10: Push to GitHub
```bash
git remote add origin https://github.com/yourusername/pipeline-benchmarking.git
git branch -M main
git push -u origin main
```
- [ ] Remote added successfully
- [ ] Branch renamed to main
- [ ] Pushed successfully
- [ ] Verified on GitHub web interface

---

## 🔍 Post-Release Verification

### On GitHub Web Interface
- [ ] All files visible and correct
- [ ] README renders properly
- [ ] No `.env` file visible
- [ ] No `results/` CSV files visible
- [ ] Sample test data is present
- [ ] Documentation files are all present

### Test Clone
```bash
cd /tmp
git clone https://github.com/yourusername/pipeline-benchmarking.git
cd pipeline-benchmarking
ls -la
```
- [ ] Clone works
- [ ] All necessary files present
- [ ] No sensitive data included
- [ ] Sample CSV is BOM-free

### Documentation Check
- [ ] README displays correctly on GitHub
- [ ] Links work (if any)
- [ ] Code blocks render properly
- [ ] Images display (if any)

---

## 📋 Release Deliverables

Verify these files are in the repository:

### Core Files
- [ ] `compare_pipelines.py` - Main CLI
- [ ] `benchmark_pipeline.py` - Single pipeline tool
- [ ] `requirements.txt` - Dependencies

### Source Code
- [ ] `src/config.py`
- [ ] `src/test_case_loader.py`
- [ ] `src/pipeline_executor.py` (with bug fix)
- [ ] `src/checkpoint_manager.py`
- [ ] `src/parallel_runner.py`
- [ ] `src/metrics_calculator.py`
- [ ] `src/report_generator.py`
- [ ] `src/single_pipeline_runner.py`
- [ ] `src/single_pipeline_report.py`

### Documentation
- [ ] `README.md` (with BOM section)
- [ ] `GETTING_STARTED.md` (with BOM section)
- [ ] `BOM_PREVENTION_GUIDE.md` (comprehensive)
- [ ] `CHANGELOG.md`
- [ ] `HOW_TO_RELEASE.md`
- [ ] `STANDALONE_REPOSITORY.md`

### Configuration
- [ ] `.gitignore` (updated)
- [ ] `.env.template` (no secrets)

### Scripts
- [ ] `prepare_for_github.sh`
- [ ] `quick_start_github.sh`
- [ ] `test_git_isolation.sh`
- [ ] `check_bom.sh` (BOM checker)

### Sample Data
- [ ] `test_cases/sample_test_cases.csv` (BOM-free!)
- [ ] `test_cases/.gitkeep`
- [ ] `results/.gitkeep`

---

## ⚠️ Common Mistakes to Avoid

### Mistake 1: Including .env file
❌ `.env` file in repository
✅ Only `.env.template` included

### Mistake 2: Including test results
❌ CSV/Excel files in `results/`
✅ Only `.gitkeep` in `results/`

### Mistake 3: Including parent directory
❌ Git initialized in `rare_senses/`
✅ Git initialized in `pipeline_benchmarking/` only

### Mistake 4: BOM in sample CSV
❌ Sample CSV has BOM (causes user errors)
✅ Sample CSV is BOM-free (verified with `check_bom.sh`)

### Mistake 5: Hardcoded credentials
❌ API keys or URLs in code
✅ All credentials from environment variables

---

## 🎯 Success Criteria

Your release is successful if:
- ✅ Repository clones without errors
- ✅ No sensitive data exposed
- ✅ Documentation is clear and complete
- ✅ Sample data works without BOM errors
- ✅ No parent directory files included
- ✅ All essential files present
- ✅ Framework validated message in commit/README

---

## 📝 After Release

### Create GitHub Release
1. Go to repository → Releases → Create new release
2. Tag: `v1.0.0`
3. Title: "Pipeline Benchmarking Framework v1.0.0"
4. Description: Copy from RELEASE_SUMMARY.md
5. Publish release

### Add Topics
Add these topics to help discoverability:
- deepset-cloud
- haystack
- benchmarking
- nlp
- testing-framework
- pipeline-testing
- python

### Update Repository Settings
- [ ] Description set
- [ ] Website/documentation link added (if any)
- [ ] Issues enabled
- [ ] Wiki enabled (optional)

### Share Release
- [ ] Post in Deepset community forum
- [ ] Share on LinkedIn/Twitter (optional)
- [ ] Notify team members

---

## 🆘 If Something Goes Wrong

### If you pushed sensitive data:
1. **DO NOT** just delete the file and commit
2. Use GitHub's "Remove sensitive data" guide
3. Or delete repository and start over

### If you pushed BOM files:
1. Fix locally: `tail -c +4 file.csv > file_fixed.csv`
2. Replace file: `mv file_fixed.csv file.csv`
3. Commit: `git add file.csv && git commit -m "Fix BOM in CSV"`
4. Push: `git push`

### If you pushed parent directory files:
1. Delete repository on GitHub
2. Remove local .git: `rm -rf .git`
3. Run `./quick_start_github.sh` again
4. Verify with `./test_git_isolation.sh`
5. Push to new repository

---

## ✅ Final Sign-Off

Before considering the release complete:

- [ ] All items in this checklist completed
- [ ] Repository verified on GitHub
- [ ] Test clone performed successfully
- [ ] Documentation reviewed
- [ ] Sample data verified (BOM-free!)
- [ ] No sensitive data exposed
- [ ] Release notes published
- [ ] Team/community notified

**Date Released**: _______________
**Released By**: _______________
**GitHub URL**: https://github.com/_______________/pipeline-benchmarking

---

## 📚 Related Documentation

- `README.md` - Main documentation with BOM troubleshooting
- `GETTING_STARTED.md` - Quick start with BOM prevention
- `BOM_PREVENTION_GUIDE.md` - Comprehensive BOM guide
- `HOW_TO_RELEASE.md` - Detailed release instructions
- `STANDALONE_REPOSITORY.md` - Isolation guide
- `RELEASE_SUMMARY.md` - Executive summary

---

**Remember**: BOM checking is CRITICAL! It's the #1 cause of user errors. Always run `./check_bom.sh` before release.
