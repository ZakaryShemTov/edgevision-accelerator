#!/usr/bin/env bash
# RTL simulation runner for EdgeVision Accelerator.
#
# Must be called from the project root:
#   bash sim/run_sim.sh
#
# Image dimensions are read automatically from sim/meta.json (written by
# gen_test_vectors.py) and passed to iverilog via -P parameter override.
# There is no need to manually edit conv_tb.v when changing image sizes.
#
# Prerequisites:
#   1. Icarus Verilog:  brew install icarus-verilog
#   2. Test vectors:    python3 python/codegen/gen_test_vectors.py [options]

set -euo pipefail

# --- Check simulator ---
if ! command -v iverilog &>/dev/null; then
    echo "Error: iverilog not found."
    echo "Install with: brew install icarus-verilog"
    exit 1
fi

# --- Check that hex files and metadata exist ---
for f in sim/input.hex sim/kernel.hex sim/expected.hex sim/meta.json; do
    if [ ! -f "$f" ]; then
        echo "Error: $f not found."
        echo "Generate test vectors first:"
        echo "  python3 python/codegen/gen_test_vectors.py"
        exit 1
    fi
done

# --- Read image dimensions from meta.json ---
# Passes them to iverilog as parameter overrides so conv_tb.v never needs
# manual editing when switching between image sizes.
IMG_H=$(python3 -c "import json; print(json.load(open('sim/meta.json'))['img_h'])")
IMG_W=$(python3 -c "import json; print(json.load(open('sim/meta.json'))['img_w'])")
echo "Image dimensions: ${IMG_H}x${IMG_W} (from sim/meta.json)"

# --- Compile ---
echo "Compiling RTL..."
iverilog -g2001 -Wall \
    -P "conv_tb.IMG_H=${IMG_H}" \
    -P "conv_tb.IMG_W=${IMG_W}" \
    -o sim/conv_sim \
    rtl/src/mac.v \
    rtl/src/conv3x3.v \
    rtl/tb/conv_tb.v

# --- Simulate ---
echo "Running simulation..."
vvp sim/conv_sim

echo ""
echo "RTL output written to sim/rtl_output.hex"
