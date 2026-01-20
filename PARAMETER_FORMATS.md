# Pipeline Parameter Formats Guide

## Overview

The benchmarking tool now supports multiple parameter formats to accommodate different pipeline configurations in Deepset Cloud.

## Supported Formats

### 1. `oed_quotations` Format

**Used by**: `oed-quotations` pipeline

**Parameter structure**:
```json
{
  "queries": ["entry_ref"],
  "params": {
    "formatter": {
      "sense": "sense_id"
    },
    "quotations": {
      "part_of_speech": "pos"
    }
  }
}
```

**How it works**:
- `formatter.sense` is a single input that automatically routes to BOTH:
  - `sense_extractor.sense_id` (for fetching the definition)
  - `formatter.sense` (for counting matches)
- This uses nested input routing in the pipeline YAML

**Pipeline YAML inputs section**:
```yaml
inputs:
  query:
  - oed_senses.entry_ref
  formatter.sense:
  - sense_extractor.sense_id
  - formatter.sense
  quotations.part_of_speech:
  - quotations.part_of_speech
```

### 2. `hybrid_prod_ready` Format

**Used by**: `rare_senses_hybrid_prod_ready` pipeline

**Parameter structure**:
```json
{
  "queries": ["entry_ref"],
  "params": {
    "sense_extractor": {
      "sense_id": "sense_id"
    },
    "formatter": {
      "sense": "sense_id"
    },
    "quotations": {
      "part_of_speech": "pos"
    }
  }
}
```

**How it works**:
- Each component receives its parameters explicitly
- `sense_extractor.sense_id` goes directly to the sense extractor component
- `formatter.sense` goes directly to the formatter component
- No automatic routing

**Pipeline YAML inputs section**:
```yaml
inputs:
  query:
  - oed_senses.entry_ref
  sense_id:
  - sense_extractor.sense_id
  - formatter.sense
  part_of_speech:
  - quotations.part_of_speech
```

### 3. `legacy` Format (Default Fallback)

**Used by**: Any pipeline not matching the above patterns

**Parameter structure**:
```json
{
  "queries": ["entry_ref"],
  "params": {
    "formatter": {
      "sense": "sense_id"
    },
    "quotations": {
      "part_of_speech": "pos"
    }
  }
}
```

## Auto-Detection

By default, the benchmarking tool uses `param_format="auto"` which automatically detects the correct format based on the pipeline name:

- Pipeline name contains `oed-quotations` or `oed_quotations` → `oed_quotations` format
- Pipeline name contains `hybrid_prod_ready` or `rare_senses_hybrid_prod_ready` → `hybrid_prod_ready` format
- Otherwise → `legacy` format

## Manual Override

You can manually specify the format in your code:

```python
config = PipelineConfig(
    name="my_pipeline",
    pipeline_name="custom_pipeline_name",
    workspace_url=workspace_url,
    api_key=api_key,
    param_format="oed_quotations"  # Manually specify format
)
```

## Command Line Usage

The command line tool uses auto-detection by default:

```bash
# Automatically uses oed_quotations format
python benchmark_pipeline.py \
  --pipeline oed-quotations \
  --test-data test_cases/sample.csv

# Automatically uses hybrid_prod_ready format
python benchmark_pipeline.py \
  --pipeline rare_senses_hybrid_prod_ready \
  --test-data test_cases/sample.csv
```

## Testing Your Format

Run the test script to verify both formats work:

```bash
cd pipeline_benchmarking
./test_both_formats.sh
```

This will test both pipelines and show the debug output with the actual parameters being sent.

## Adding New Formats

To add a new format:

1. **Update the auto-detection logic** in `pipeline_executor.py`:
```python
elif "your_pipeline_name" in pipeline_lower:
    param_format = "your_custom_format"
```

2. **Add the format handler**:
```python
elif param_format == "your_custom_format":
    params = {
        # Your custom parameter structure
    }
```

3. **Document it** in this file

## Troubleshooting

### Check which format is being used

The debug output (first request only) shows:
```
================================================================================
DEBUG: First API Request
================================================================================
Pipeline: oed-quotations
Param Format: oed_quotations
URL: https://api.cloud.deepset.ai/...
Payload: {...}
================================================================================
```

### Pipeline returns error "Input sense not found"

This means the parameter format doesn't match the pipeline's expected inputs. Check:
1. The pipeline's YAML `inputs:` section
2. Which components expect which parameters
3. Verify you're using the correct format

### How do I know which format my pipeline needs?

1. Look at your pipeline YAML `inputs:` section
2. If it has `formatter.sense:` (nested) → use `oed_quotations` format
3. If it has flat inputs like `sense_id:` → use `hybrid_prod_ready` format
4. Check the connections to see where parameters flow

## Format Comparison Table

| Feature | oed_quotations | hybrid_prod_ready | legacy |
|---------|---------------|-------------------|--------|
| sense_extractor param | `formatter.sense` (routed) | `sense_extractor.sense_id` | `formatter.sense` (routed) |
| formatter param | `formatter.sense` (routed) | `formatter.sense` | `formatter.sense` |
| quotations param | `quotations.part_of_speech` | `quotations.part_of_speech` | `quotations.part_of_speech` |
| Auto-detected | Yes (by name) | Yes (by name) | Yes (fallback) |
| Use case | Nested input routing | Explicit flat inputs | Older pipelines |
