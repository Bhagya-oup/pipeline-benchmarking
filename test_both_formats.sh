#!/bin/bash
# Test script to verify both pipeline formats work correctly

echo "========================================"
echo "Testing Pipeline Parameter Formats"
echo "========================================"
echo ""

# Test 1: OED Quotations pipeline
echo "Test 1: Testing oed-quotations pipeline..."
echo "Expected format: formatter.sense + quotations.part_of_speech"
echo ""
python benchmark_pipeline.py \
  --pipeline oed-quotations \
  --test-data test_cases/test_create_v.csv \
  --workers 1 \
  --output results/test_oed_format

echo ""
echo "========================================"
echo ""

# Test 2: Hybrid Prod Ready pipeline
echo "Test 2: Testing rare_senses_hybrid_prod_ready pipeline..."
echo "Expected format: sense_extractor.sense_id + formatter.sense + quotations.part_of_speech"
echo ""
python benchmark_pipeline.py \
  --pipeline rare_senses_hybrid_prod_ready \
  --test-data test_cases/test_create_v.csv \
  --workers 1 \
  --output results/test_hybrid_format

echo ""
echo "========================================"
echo "Tests Complete!"
echo "Check the debug output above to verify correct parameter formats were used."
echo "========================================"
