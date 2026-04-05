"""
RTL output verification and visual comparison.

Reads sim/expected.hex (Python golden reference) and sim/rtl_output.hex
(written by the Verilog testbench), checks they match exactly, and generates
a side-by-side visual comparison figure.

Usage:
    python3 compare_outputs.py
    python3 compare_outputs.py --sim-dir path/to/sim --output-dir results/

This script is the final stage of the V1 verification pipeline:

    gen_test_vectors.py  →  RTL simulation  →  compare_outputs.py

It relies on sim/meta.json (written by gen_test_vectors.py) for image
dimensions. Make sure gen_test_vectors.py has been run and the RTL simulation
has produced sim/rtl_output.hex before running this script.
"""

import argparse
import json
import os
import sys

import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS_DIR, "..", "common"))

from hex_io import read_hex_file                    # noqa: E402
from conversions import int8_to_uint8_display       # noqa: E402

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False

try:
    from PIL import Image as PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify RTL output against golden reference and generate comparison figure."
    )
    parser.add_argument(
        "--sim-dir", type=str, default=None,
        help="Directory containing hex files and meta.json (default: <project-root>/sim/)."
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Directory for output figures (default: <project-root>/results/)."
    )
    args = parser.parse_args()

    _THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
    _PROJECT_ROOT = os.path.join(_THIS_DIR, "..", "..")

    sim_dir = os.path.abspath(args.sim_dir) if args.sim_dir \
              else os.path.abspath(os.path.join(_PROJECT_ROOT, "sim"))
    out_dir = os.path.abspath(args.output_dir) if args.output_dir \
              else os.path.abspath(os.path.join(_PROJECT_ROOT, "results"))
    os.makedirs(out_dir, exist_ok=True)

    # --- Load metadata ---
    meta_path = os.path.join(sim_dir, "meta.json")
    if not os.path.isfile(meta_path):
        print(f"Error: meta.json not found at {meta_path}", file=sys.stderr)
        print("Run gen_test_vectors.py first.", file=sys.stderr)
        sys.exit(1)

    with open(meta_path) as f:
        meta = json.load(f)

    out_h = meta["out_h"]
    out_w = meta["out_w"]
    img_h = meta["img_h"]
    img_w = meta["img_w"]
    total = out_h * out_w

    print(f"Image:    {img_h}x{img_w}    Output: {out_h}x{out_w}  ({total} pixels)")
    print(f"Mode:     {meta['mode']}    Kernel: {meta['kernel_name']}")

    # --- Check rtl_output.hex exists ---
    rtl_path = os.path.join(sim_dir, "rtl_output.hex")
    if not os.path.isfile(rtl_path):
        print(f"\nError: rtl_output.hex not found at {rtl_path}", file=sys.stderr)
        print("Run the RTL simulation first:  bash sim/run_sim.sh", file=sys.stderr)
        sys.exit(1)

    # --- Load expected and RTL outputs ---
    expected_path = os.path.join(sim_dir, "expected.hex")
    expected = read_hex_file(expected_path, total).reshape(out_h, out_w)
    rtl_out  = read_hex_file(rtl_path,      total).reshape(out_h, out_w)

    # --- Numerical comparison ---
    mismatches = np.sum(expected != rtl_out)
    print(f"\n--- Verification ---")
    print(f"Total pixels:  {total}")
    print(f"Matches:       {total - mismatches}")
    print(f"Mismatches:    {mismatches}")

    if mismatches > 0:
        print("\nMismatch details (first 10):")
        coords = np.argwhere(expected != rtl_out)
        for r, c in coords[:10]:
            print(f"  ({r:3d},{c:3d})  expected={int(expected[r,c]):4d}  rtl={int(rtl_out[r,c]):4d}")
        print("\nRESULT: FAILED")
        status = "FAILED"
    else:
        print("\nRESULT: ALL PASS — RTL output matches golden reference exactly.")
        status = "PASS"

    # --- Saturation stats on expected output ---
    sat_pos = int(np.sum(expected == 127))
    sat_neg = int(np.sum(expected == -128))
    sat_total = sat_pos + sat_neg

    # --- Write validation report ---
    import datetime
    report_path = os.path.join(out_dir, "validation_report.txt")
    with open(report_path, "w") as rpt:
        rpt.write("EdgeVision Accelerator — Validation Report\n")
        rpt.write("=" * 50 + "\n")
        rpt.write(f"Date:             {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        rpt.write(f"Mode:             {meta['mode']}\n")
        rpt.write(f"Kernel:           {meta['kernel_name']}\n")
        rpt.write(f"Input image:      {img_h}x{img_w}  ({img_h * img_w} pixels)\n")
        rpt.write(f"Output size:      {out_h}x{out_w}  ({total} pixels)\n")
        rpt.write("-" * 50 + "\n")
        rpt.write(f"Total pixels:     {total}\n")
        rpt.write(f"Matches:          {total - mismatches}\n")
        rpt.write(f"Mismatches:       {mismatches}\n")
        rpt.write(f"Result:           {status}\n")
        rpt.write("-" * 50 + "\n")
        rpt.write(f"Saturated (+127): {sat_pos}  ({100*sat_pos/total:.1f}%)\n")
        rpt.write(f"Saturated (-128): {sat_neg}  ({100*sat_neg/total:.1f}%)\n")
        rpt.write(f"Saturated total:  {sat_total}  ({100*sat_total/total:.1f}%)\n")
        rpt.write(f"Output min:       {int(expected.min())}\n")
        rpt.write(f"Output max:       {int(expected.max())}\n")
        rpt.write(f"Output mean:      {float(expected.astype(np.float32).mean()):.2f}\n")
        if mismatches > 0:
            rpt.write("-" * 50 + "\n")
            rpt.write("Mismatch details (first 10):\n")
            coords = np.argwhere(expected != rtl_out)
            for r, c in coords[:10]:
                rpt.write(f"  ({r:3d},{c:3d})  expected={int(expected[r,c]):4d}  rtl={int(rtl_out[r,c]):4d}\n")
    print(f"Validation report: {report_path}")

    # --- Visual comparison ---
    if not _MPL_AVAILABLE:
        print("\nmatplotlib not installed — skipping visual comparison.")
        print("Install with: pip3 install matplotlib")
        return

    # Build panel list: [original input (if available), python output, rtl output]
    panels = []

    # Try to load the original input image for context
    input_hex_path = os.path.join(sim_dir, "input.hex")
    if os.path.isfile(input_hex_path):
        raw_input = read_hex_file(input_hex_path, img_h * img_w).reshape(img_h, img_w)
        # Crop to output size for alignment
        input_display = int8_to_uint8_display(raw_input[1:img_h-1, 1:img_w-1])
        panels.append((input_display, "Input (cropped to output region)"))

    panels.append((int8_to_uint8_display(expected), "Python golden reference"))
    panels.append((int8_to_uint8_display(rtl_out),  f"RTL output  [{status}]"))

    n = len(panels)
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 5))
    if n == 1:
        axes = [axes]

    kernel_label = meta['kernel_name']
    fig.suptitle(
        f"EdgeVision Accelerator — {kernel_label}  |  {img_h}×{img_w} image  |  {status}",
        fontsize=11
    )

    for ax, (img, title) in zip(axes, panels):
        ax.imshow(img, cmap="gray", vmin=0, vmax=255)
        ax.set_title(title, fontsize=9)
        ax.axis("off")

    plt.tight_layout()

    fig_stem = f"comparison_{kernel_label}"
    fig_path = os.path.join(out_dir, f"{fig_stem}.png")
    plt.savefig(fig_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"\nComparison figure saved: {fig_path}")


if __name__ == "__main__":
    main()
