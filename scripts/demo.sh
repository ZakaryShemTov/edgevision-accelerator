#!/usr/bin/env bash
# EdgeVision Accelerator — full end-to-end demonstration pipeline.
#
# Runs every stage in sequence:
#   1. Generate test vectors (Python golden reference → hex files)
#   2. RTL simulation        (iverilog + vvp → rtl_output.hex)
#   3. Verify + visualize    (compare RTL vs golden, write report + figure)
#
# Must be called from the project root:
#   bash scripts/demo.sh
#   bash scripts/demo.sh --image data/cameraman.png --kernel sobel_x
#   bash scripts/demo.sh --kernel laplacian
#
# Options:
#   --image   PATH     Input PNG (default: data/cameraman.png)
#   --kernel  NAME     Kernel: sobel_x | sobel_y | laplacian | gaussian
#                      (default: sobel_x)
#   --random           Use random 8x8 test vectors instead of an image
#   --seed    N        Random seed, only used with --random (default: 0)
#
# Outputs (all written to results/):
#   <stem>_input.png          Input image
#   <stem>_<kernel>_python.png  Python golden reference output
#   <stem>_<kernel>_comparison.png  Side-by-side visual comparison
#   validation_report.txt     Numerical verification summary

set -euo pipefail

# --------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------
IMAGE="data/cameraman.png"
KERNEL="sobel_x"
RANDOM_MODE=0
SEED=0

# --------------------------------------------------------------------------
# Parse arguments
# --------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --image)   IMAGE="$2";  shift 2 ;;
        --kernel)  KERNEL="$2"; shift 2 ;;
        --random)  RANDOM_MODE=1; shift ;;
        --seed)    SEED="$2";   shift 2 ;;
        *) echo "Unknown argument: $1"; exit 1 ;;
    esac
done

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
echo "========================================"
echo "  EdgeVision Accelerator — Demo Pipeline"
echo "========================================"
if [ "$RANDOM_MODE" -eq 1 ]; then
    echo "  Mode:   random (seed=${SEED}, 8x8)"
else
    echo "  Image:  ${IMAGE}"
    echo "  Kernel: ${KERNEL}"
fi
echo ""

# --------------------------------------------------------------------------
# Step 1 — Generate test vectors
# --------------------------------------------------------------------------
echo "[1/3] Generating test vectors..."
if [ "$RANDOM_MODE" -eq 1 ]; then
    python3 python/codegen/gen_test_vectors.py --seed "$SEED" --height 8 --width 8
else
    python3 python/codegen/gen_test_vectors.py --image "$IMAGE" --kernel "$KERNEL"
fi
echo ""

# --------------------------------------------------------------------------
# Step 2 — RTL simulation
# --------------------------------------------------------------------------
if ! command -v iverilog &>/dev/null; then
    echo "[2/3] Skipping RTL simulation (iverilog not found)."
    echo "      Install with: brew install icarus-verilog"
    echo "      Then re-run this script to include the RTL verification step."
    SIM_SKIPPED=1
else
    echo "[2/3] Running RTL simulation..."
    bash sim/run_sim.sh
    SIM_SKIPPED=0
fi
echo ""

# --------------------------------------------------------------------------
# Step 3 — Verify and visualize
# --------------------------------------------------------------------------
if [ "${SIM_SKIPPED:-0}" -eq 1 ]; then
    echo "[3/3] Skipping verification (no RTL output available)."
    echo "      Running visual filter (Python only)..."
    if [ "$RANDOM_MODE" -eq 0 ]; then
        python3 python/visualize/run_filter.py --image "$IMAGE" --kernel "$KERNEL"
    fi
else
    echo "[3/3] Verifying RTL output and generating comparison..."
    python3 python/verify/compare_outputs.py
fi
echo ""

# --------------------------------------------------------------------------
# Summary
# --------------------------------------------------------------------------
echo "========================================"
echo "  Done. Outputs in results/"
ls results/ | sed 's/^/    /'
echo "========================================"
