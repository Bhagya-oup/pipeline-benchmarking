# GitHub Release Checklist

This document lists all files that should be included in the GitHub repository.

## ✅ Files to Include

### Core Source Code (`src/`)
- [x] `src/__init__.py`
- [x] `src/config.py` - Configuration dataclasses
- [x] `src/test_case_loader.py` - CSV/JSON/TXT parsers
- [x] `src/pipeline_executor.py` - Pipeline invocation (FIXED: type mismatch bug)
- [x] `src/checkpoint_manager.py` - Resumability support
- [x] `src/parallel_runner.py` - Multiprocessing engine
- [x] `src/single_pipeline_runner.py` - Single pipeline benchmarking
- [x] `src/metrics_calculator.py` - Accuracy metrics
- [x] `src/report_generator.py` - CSV/Excel/TXT report generation
- [x] `src/single_pipeline_report.py` - Single pipeline reports
- [x] `src/fetch_from_hero_quotations.py` - API integration (if applicable)

### Main CLI Scripts
- [x] `compare_pipelines.py` - Main comparison tool
- [x] `benchmark_pipeline.py` - Single pipeline benchmarking
- [x] `analyze_results.py` - Result analysis utilities
- [x] `compare_results.py` - Compare multiple test runs

### Documentation
- [x] `README.md` - Main documentation (UPDATE FOR GITHUB)
- [x] `GETTING_STARTED.md` - Quick start guide
- [x] `MIGRATION_GUIDE.md` - Migration instructions
- [x] `README_SINGLE_PIPELINE.md` - Single pipeline docs
- [x] `CHANGELOG.md` - Version history
- [x] `requirements.txt` - Python dependencies

### Configuration & Setup
- [x] `.gitignore` - Git ignore rules
- [x] `.env.template` - Environment variable template (CREATE IF MISSING)
- [x] `test_cases/.gitkeep` - Preserve empty directory
- [x] `test_cases/sample_test_cases.csv` - Example test data
- [x] `results/.gitkeep` - Preserve empty directory

### Tests (Optional but Recommended)
- [ ] `tests/__init__.py`
- [ ] Unit tests for each component (if they exist)

## ❌ Files to Exclude

### Results and Outputs
- All files in `results/` except `.gitkeep`
- All checkpoint files
- All generated CSV/Excel/TXT reports

### Test Data
- All actual test data CSV files (users provide their own)
- Any files containing proprietary sense IDs or quotations

### Credentials and Environment
- `.env` file with actual credentials
- Any files containing API keys or passwords

### Python Generated Files
- `__pycache__/` directories
- `*.pyc`, `*.pyo` files
- Virtual environment directories (`venv/`, `env/`)

### IDE and OS Files
- `.vscode/`, `.idea/` directories
- `.DS_Store`, `Thumbs.db`
- `*.swp`, `*.swo` files

### Debug and Temporary Files
- `debug_*.py` scripts (unless generic utilities)
- `test_*.py` scripts (unless actual unit tests)
- `inspect_*.py`, `validate_*.py` (temporary debugging scripts)

## 📝 Files to Create/Update Before Release

### 1. `.env.template`
Create a template for environment variables:
```bash
# Deepset Cloud API Configuration
DEEPSET_API_KEY=your_deepset_api_key_here
DEEPSET_WORKSPACE_URL=https://your-workspace.deepset.cloud

# Optional: Additional API Keys
# HERO_API_KEY=your_hero_api_key
# SOLR_URL=https://your-solr-instance
```

### 2. `README.md`
Update the main README to:
- Remove internal references to specific pipelines
- Add clear installation instructions
- Add usage examples with generic pipeline names
- Include troubleshooting section
- Add link to issues for bug reports
- Add license information

### 3. `CONTRIBUTING.md` (Optional)
- Guidelines for contributing
- Code style requirements
- How to report bugs
- Pull request process

### 4. `LICENSE`
- Choose appropriate license (MIT, Apache 2.0, etc.)
- Add license file

## 🚀 Pre-Release Commands

```bash
# 1. Clean all test results
rm -rf results/checkpoints/*
rm -rf results/raw_results/*
rm -rf results/reports/*
rm -f results/*.csv results/*.xlsx results/*.txt

# 2. Clean test data (keep only sample)
find test_cases/ -name "*.csv" ! -name "sample_test_cases.csv" -delete
find test_cases/ -name "*.json" -delete
find test_cases/ -name "*.txt" -delete

# 3. Remove debug scripts
rm -f debug_*.py test_counting.py test_matching.py validate_framework.py verify_pipelines.py inspect_response.py

# 4. Clean Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete

# 5. Remove environment file
rm -f .env

# 6. Check what will be committed
git status
git add -A
git status
```

## 📦 Recommended GitHub Repository Structure

```
pipeline-benchmarking/
├── .github/
│   └── workflows/          # (Optional) CI/CD workflows
├── src/                    # Core source code
├── test_cases/             # Example test data only
│   ├── .gitkeep
│   └── sample_test_cases.csv
├── results/                # Empty (users generate their own)
│   └── .gitkeep
├── tests/                  # Unit tests (if any)
├── .gitignore
├── .env.template
├── README.md
├── GETTING_STARTED.md
├── CHANGELOG.md
├── LICENSE
├── requirements.txt
├── compare_pipelines.py
└── benchmark_pipeline.py
```

## 🔍 Final Checklist

Before pushing to GitHub:

- [ ] All sensitive data removed
- [ ] All API keys removed
- [ ] All proprietary test data removed
- [ ] README updated with generic examples
- [ ] .env.template created
- [ ] .gitignore covers all sensitive files
- [ ] License file added
- [ ] Version number set (e.g., v1.0.0)
- [ ] CHANGELOG updated
- [ ] All tests pass (if applicable)
- [ ] Documentation reviewed for clarity

## 📋 Post-Release

After pushing to GitHub:

1. Create a GitHub Release (v1.0.0)
2. Add release notes highlighting:
   - Main features
   - Fixed bugs (e.g., type mismatch bug fix)
   - Known limitations
   - Future roadmap
3. Tag the release
4. Update any external documentation

## 🎯 Repository Description

Suggested GitHub repository description:

**Title:** Pipeline Benchmarking Framework for Deepset Cloud

**Description:**
A comprehensive benchmarking framework for comparing Deepset Cloud pipelines with parallel execution, checkpoint-based resumability, and detailed reporting. Supports automated testing across thousands of test cases with CSV/Excel output.

**Topics/Tags:**
- deepset
- haystack
- nlp
- benchmarking
- pipeline-testing
- semantic-search
- automation
- testing-framework
