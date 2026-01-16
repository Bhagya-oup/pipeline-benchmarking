# Changelog

## v1.1.0 - 2026-01-13

### Changed
- **BREAKING**: Updated to use Hero Quotations API instead of direct Sketch Engine
  - Matches production pipeline architecture exactly
  - POS format changed from short codes (`n`, `v`) to full names (`noun`, `verb`)
  - Requires `HERO_API_KEY` instead of `SKETCH_ENGINE_USERNAME/PASSWORD`

### Added
- `fetch_from_hero_quotations.py` - Hero API wrapper
- Support for full POS names in test data

### Migration Guide
If you have existing test data:
1. Update your `.env`: Replace `SKETCH_ENGINE_*` with `HERO_API_KEY`
2. Update your CSV: Change POS column from `n` → `noun`, `v` → `verb`, `adj` → `adjective`, etc.

## v1.0.0 - 2026-01-13

### Added
- Initial release with 7 core modules
- Parallel execution with checkpoint resumability
- CSV/Excel/text reporting
- Direct Sketch Engine integration (deprecated in v1.1.0)
