#!/bin/bash
# Progress monitoring script for pipeline benchmarks

echo "================================================================================"
echo "PIPELINE BENCHMARK PROGRESS"
echo "================================================================================"
echo ""

# Check if processes are running
BASE_RUNNING=$(ps aux | grep "oed-quotations" | grep "sample_test_1000" | grep -v grep | wc -l)
HYBRID_RUNNING=$(ps aux | grep "hybrid_bm25" | grep "sample_test_1000" | grep -v grep | wc -l)

echo "Process Status:"
if [ $BASE_RUNNING -gt 0 ]; then
    echo "  ✓ Base Pipeline (oed-quotations): RUNNING"
else
    echo "  ✗ Base Pipeline (oed-quotations): NOT RUNNING"
fi

if [ $HYBRID_RUNNING -gt 0 ]; then
    echo "  ✓ Hybrid Pipeline: RUNNING"
else
    echo "  ✗ Hybrid Pipeline: NOT RUNNING"
fi

echo ""
echo "================================================================================"
echo "CHECKPOINT PROGRESS"
echo "================================================================================"
echo ""

# Check base pipeline progress
if [ -d "results/base_1000/checkpoints" ]; then
    BASE_CHECKPOINT=$(ls -t results/base_1000/checkpoints/*.pkl 2>/dev/null | head -1)
    if [ -n "$BASE_CHECKPOINT" ]; then
        BASE_COUNT=$(python3 -c "import pickle; results = pickle.load(open('$BASE_CHECKPOINT', 'rb')); print(len(results))" 2>/dev/null)
        if [ -n "$BASE_COUNT" ]; then
            BASE_PERCENT=$(echo "scale=1; $BASE_COUNT * 100 / 999" | bc)
            echo "Base Pipeline Progress: $BASE_COUNT/999 cases (${BASE_PERCENT}%)"
        else
            echo "Base Pipeline Progress: Checkpoint found but couldn't read count"
        fi
    else
        echo "Base Pipeline Progress: No checkpoint yet"
    fi
else
    echo "Base Pipeline Progress: Not started yet"
fi

# Check hybrid pipeline progress
if [ -d "results/hybrid_1000/checkpoints" ]; then
    HYBRID_CHECKPOINT=$(ls -t results/hybrid_1000/checkpoints/*.pkl 2>/dev/null | head -1)
    if [ -n "$HYBRID_CHECKPOINT" ]; then
        HYBRID_COUNT=$(python3 -c "import pickle; results = pickle.load(open('$HYBRID_CHECKPOINT', 'rb')); print(len(results))" 2>/dev/null)
        if [ -n "$HYBRID_COUNT" ]; then
            HYBRID_PERCENT=$(echo "scale=1; $HYBRID_COUNT * 100 / 999" | bc)
            echo "Hybrid Pipeline Progress: $HYBRID_COUNT/999 cases (${HYBRID_PERCENT}%)"
        else
            echo "Hybrid Pipeline Progress: Checkpoint found but couldn't read count"
        fi
    else
        echo "Hybrid Pipeline Progress: No checkpoint yet"
    fi
else
    echo "Hybrid Pipeline Progress: Not started yet"
fi

echo ""
echo "================================================================================"
echo "Run this script again to update progress: ./check_progress.sh"
echo "================================================================================"
