# Migration Guide: Sketch Engine → Hero API

## What Changed in v1.1.0

The benchmarking tool now uses the **Hero Quotations API** instead of direct Sketch Engine access. This matches your production pipeline architecture exactly.

## Required Changes

### 1. Update Environment Variables

**Remove:**
```bash
SKETCH_ENGINE_USERNAME=...
SKETCH_ENGINE_PASSWORD=...
```

**Add:**
```bash
HERO_API_KEY=your_hero_api_key
```

### 2. Update Test Data Format

**POS Column - Old Format (Short Codes):**
```csv
entry_ref,sense_id,word,pos
aaron_n1,11836839,aaron,n
aaron_n2,12884176,aaron,n
flowery_adj1,4165862,flowery,adj
```

**POS Column - New Format (Full Names):**
```csv
entry_ref,sense_id,word,pos
aaron_n1,11836839,aaron,noun
aaron_n2,12884176,aaron,noun
flowery_adj1,4165862,flowery,adjective
```

### Excel Formula to Convert POS Tags

If you have existing data with short codes in column A (entry_ref), use this formula in the POS column:

```excel
=LET(
  tag, TEXTAFTER(A2,"_",-1),
  base, TEXTBEFORE(tag&"0","0"),
  SWITCH(base,
    "n", "noun",
    "v", "verb",
    "adj", "adjective",
    "adv", "adverb",
    "pron", "pronoun",
    "det", "determiner",
    "prep", "preposition",
    "conj", "conjunction",
    "num", "number",
    "int", "interjection",
    base
  )
)
```

### 3. Supported POS Values

| Short Code (Old) | Full Name (New) |
|------------------|-----------------|
| n | noun |
| v | verb |
| adj | adjective |
| adv | adverb |
| pron | pronoun |
| det | determiner |
| prep | preposition |
| conj | conjunction |
| num | number |
| int | interjection |

## Why This Change?

✅ **Exact Production Match**: Tool now uses identical API as your production pipelines
✅ **Simplified Auth**: Single Hero API key instead of Sketch Engine credentials
✅ **Consistency**: Same data flow as `unified_hybrid_pipeline.yaml`

## Verification

Test with a small dataset first:

```bash
python compare_pipelines.py \
  --test-data test_cases/sample_5_cases.csv \
  --new-pipeline unified_simple \
  --old-pipeline sense_retrieval_no_custom \
  --output results/test_migration
```

Expected output: No API errors, quotations fetched successfully.
