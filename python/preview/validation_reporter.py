"""
V4 Snapshot Validation — Validation Reporter

Reads expected.hex and rtl_output.hex for a run, computes the diff,
and produces:
  - diff_map.png           : per-pixel error visualized (grey=match, hot=mismatch)
  - board.png              : full comparison board (input | python | rtl | diff)
  - report.json            : structured metrics for programmatic use
  - report.txt             : human-readable summary

The board is designed to be self-contained and portfolio-presentable:
it shows every relevant fact about the run without requiring any other file.
"""

import json
import os
import sys

import cv2
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS_DIR, "..", "common"))

from hex_io import read_hex_file                    # noqa: E402
from conversions import int8_to_uint8_display       # noqa: E402

# Alias used internally
_read_hex     = read_hex_file
_int8_to_uint8 = int8_to_uint8_display


# ---------------------------------------------------------------------------
# Diff map
# ---------------------------------------------------------------------------

def _make_diff_map(expected: np.ndarray, rtl_out: np.ndarray) -> np.ndarray:
    """
    Build a per-pixel difference visualization (BGR uint8).

    Matching pixels: mid-gray (128, 128, 128).
    Mismatching pixels: colormap-scaled by |error| magnitude.
    """
    diff = expected.astype(np.int32) - rtl_out.astype(np.int32)  # range [-255, 255]
    abs_diff = np.abs(diff).astype(np.uint8)                       # range [0, 255]

    # Apply colormap (COLORMAP_HOT: black→red→yellow→white)
    heatmap = cv2.applyColorMap(abs_diff, cv2.COLORMAP_HOT)

    # Where diff == 0, force mid-gray so matching pixels are clearly neutral
    match_mask = (diff == 0)
    heatmap[match_mask] = [100, 100, 100]

    return heatmap  # BGR uint8


# ---------------------------------------------------------------------------
# Board
# ---------------------------------------------------------------------------

def _labeled(img_bgr: np.ndarray, text: str, height: int = 22) -> np.ndarray:
    """Add a dark label strip above a BGR image."""
    w = img_bgr.shape[1]
    strip = np.zeros((height, w, 3), dtype=np.uint8)
    cv2.putText(strip, text, (4, height - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, (200, 200, 200), 1, cv2.LINE_AA)
    return np.vstack([strip, img_bgr])


def _status_bar(width: int, metrics: dict) -> np.ndarray:
    """Build a single-line status strip at the bottom of the board."""
    h = 28
    bar = np.zeros((h, width, 3), dtype=np.uint8)
    status = metrics["status"].upper()
    color  = (0, 220, 0) if status == "PASS" else (0, 0, 220)
    n      = metrics["total_pixels"]
    m      = metrics["mismatches"]
    sat    = metrics["saturated_pct"]
    text   = (f"{status}  |  {n - m}/{n} match  |  {m} mismatch"
              f"  |  sat {sat:.1f}%"
              f"  |  {metrics['img_h']}x{metrics['img_w']} → {metrics['out_h']}x{metrics['out_w']}"
              f"  |  kernel: {metrics['kernel_name']}")
    cv2.putText(bar, text, (6, h - 8),
                cv2.FONT_HERSHEY_SIMPLEX, 0.38, color, 1, cv2.LINE_AA)
    return bar


def _scale_to(img: np.ndarray, target_h: int) -> np.ndarray:
    """Resize an image to target_h rows, preserving aspect ratio."""
    h, w = img.shape[:2]
    if h == target_h:
        return img
    scale = target_h / h
    new_w = max(1, int(w * scale))
    return cv2.resize(img, (new_w, target_h), interpolation=cv2.INTER_NEAREST)


def make_board(
    source_uint8: np.ndarray,
    expected:     np.ndarray,
    rtl_out:      np.ndarray,
    diff_map:     np.ndarray,
    kernel_name:  str,
    metrics:      dict,
) -> np.ndarray:
    """
    Assemble the four-panel comparison board:
      [ Input crop | Python golden | RTL output | Diff map ]
    + status bar at the bottom.
    """
    H_src, W_src = source_uint8.shape
    # Crop source to output size (remove 1-pixel border per side)
    src_crop = source_uint8[1:H_src-1, 1:W_src-1]

    # Convert each panel to BGR
    p_input  = cv2.cvtColor(src_crop,                cv2.COLOR_GRAY2BGR)
    p_python = cv2.cvtColor(_int8_to_uint8(expected), cv2.COLOR_GRAY2BGR)
    p_rtl    = cv2.cvtColor(_int8_to_uint8(rtl_out),  cv2.COLOR_GRAY2BGR)
    p_diff   = diff_map  # already BGR

    # Scale all to same height (use python output height as reference)
    target_h = p_python.shape[0]
    p_input  = _scale_to(p_input,  target_h)
    p_rtl    = _scale_to(p_rtl,    target_h)
    p_diff   = _scale_to(p_diff,   target_h)

    # Add labels
    p_input  = _labeled(p_input,  "Input (cropped)")
    p_python = _labeled(p_python, "Python golden")
    p_rtl    = _labeled(p_rtl,    "RTL output")
    p_diff   = _labeled(p_diff,   "Diff  (grey=match, hot=error)")

    # Dividers
    div = np.full((p_input.shape[0], 1, 3), 60, dtype=np.uint8)
    row = np.hstack([p_input, div, p_python, div, p_rtl, div, p_diff])

    # Status bar
    bar = _status_bar(row.shape[1], metrics)

    return np.vstack([row, bar])


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def generate_report(run_info: dict, rtl_hex_path: str, sim_log: str,
                    source_uint8: np.ndarray) -> dict:
    """
    Generate all artifacts for a completed validation run.

    Args:
        run_info:      Dict from snapshot_exporter.export_snapshot.
        rtl_hex_path:  Path to rtl_output.hex in the run sim/ dir.
        sim_log:       Captured simulation stdout/stderr.
        source_uint8:  Original uint8 source frame (pre-INT8 conversion).

    Writes into run_info["run_dir"]:
        diff_map.png, board.png, report.json, report.txt

    Returns:
        metrics dict (same content as report.json).
    """
    run_dir    = run_info["run_dir"]
    sim_dir    = run_info["sim_dir"]
    out_h      = run_info["out_h"]
    out_w      = run_info["out_w"]
    total      = out_h * out_w
    kernel_name = run_info["kernel_name"]

    # --- Load expected and RTL outputs ---
    expected = _read_hex(os.path.join(sim_dir, "expected.hex"), total).reshape(out_h, out_w)
    rtl_out  = _read_hex(rtl_hex_path,                          total).reshape(out_h, out_w)

    # --- Compute metrics ---
    mismatches = int(np.sum(expected != rtl_out))
    sat_pos    = int(np.sum(expected == 127))
    sat_neg    = int(np.sum(expected == -128))
    sat_total  = sat_pos + sat_neg

    metrics = {
        "run_id":        run_info["run_id"],
        "kernel_name":   kernel_name,
        "img_h":         run_info["img_h"],
        "img_w":         run_info["img_w"],
        "out_h":         out_h,
        "out_w":         out_w,
        "total_pixels":  total,
        "matches":       total - mismatches,
        "mismatches":    mismatches,
        "status":        "pass" if mismatches == 0 else "fail",
        "output_min":    int(expected.min()),
        "output_max":    int(expected.max()),
        "output_mean":   round(float(expected.astype(np.float32).mean()), 3),
        "saturated_pos": sat_pos,
        "saturated_neg": sat_neg,
        "saturated_pct": round(100 * sat_total / total, 1),
        "has_roi":       run_info["has_roi"],
        "roi":           run_info["roi"],
    }

    # --- Diff map ---
    diff_map = _make_diff_map(expected, rtl_out)
    cv2.imwrite(os.path.join(run_dir, "diff_map.png"), diff_map)

    # --- Board ---
    board = make_board(source_uint8, expected, rtl_out, diff_map, kernel_name, metrics)
    cv2.imwrite(os.path.join(run_dir, "board.png"), board)

    # --- report.json ---
    with open(os.path.join(run_dir, "report.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # --- report.txt ---
    status_str = metrics["status"].upper()
    with open(os.path.join(run_dir, "report.txt"), "w") as f:
        f.write("EdgeVision Accelerator — Snapshot Validation Report\n")
        f.write("=" * 52 + "\n")
        f.write(f"Run ID:          {metrics['run_id']}\n")
        f.write(f"Kernel:          {kernel_name}\n")
        f.write(f"Input:           {metrics['img_h']}x{metrics['img_w']}"
                + (f"  [ROI {run_info['roi']}]" if run_info["has_roi"] else "") + "\n")
        f.write(f"Output:          {out_h}x{out_w}  ({total} pixels)\n")
        f.write("-" * 52 + "\n")
        f.write(f"Matches:         {metrics['matches']}\n")
        f.write(f"Mismatches:      {mismatches}\n")
        f.write(f"Status:          {status_str}\n")
        f.write("-" * 52 + "\n")
        f.write(f"Output min/max:  {metrics['output_min']} / {metrics['output_max']}\n")
        f.write(f"Output mean:     {metrics['output_mean']}\n")
        f.write(f"Saturated:       {sat_total}/{total}  ({metrics['saturated_pct']}%)\n")
        if mismatches > 0:
            f.write("-" * 52 + "\n")
            f.write("First mismatches:\n")
            coords = np.argwhere(expected != rtl_out)
            for r, c in coords[:10]:
                f.write(f"  ({r:3d},{c:3d})  expected={int(expected[r,c]):4d}"
                        f"  rtl={int(rtl_out[r,c]):4d}\n")
        f.write("-" * 52 + "\n")
        f.write("Simulation log:\n")
        for line in sim_log.strip().splitlines():
            f.write(f"  {line}\n")

    return metrics
