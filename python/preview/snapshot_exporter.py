"""
V4 Snapshot Validation — Snapshot Exporter

Converts a captured frame (or ROI crop) into the hex files and metadata
that the existing RTL simulation pipeline expects.

Output (written to a run-specific directory under results/runs/):
    <run_dir>/sim/input.hex
    <run_dir>/sim/kernel.hex
    <run_dir>/sim/expected.hex
    <run_dir>/sim/meta.json
    <run_dir>/source.png        ← the uint8 source frame or ROI saved for reference

This is a thin wrapper around the V1 hex-writing logic. The contractual
INT8 conversion (uint8 - 128) and hex format are unchanged.

A ROI is just a rectangular crop applied to the frame before export.
The pipeline sees a normal image — it has no concept of ROI.
"""

import json
import os
import time

import cv2
import numpy as np

import sys
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS_DIR, "..", "golden"))
sys.path.insert(0, os.path.join(_THIS_DIR, "..", "common"))

from conv_reference import conv2d_int8        # noqa: E402
from kernels import KERNELS                   # noqa: E402
from hex_io import write_hex_file             # noqa: E402
from conversions import uint8_to_int8         # noqa: E402


def export_snapshot(
    frame_uint8:  np.ndarray,
    kernel_name:  str,
    results_root: str,
    roi:          tuple[int, int, int, int] | None = None,
    run_id:       str | None = None,
) -> dict:
    """
    Export a frame (or ROI crop) as RTL simulation inputs.

    Args:
        frame_uint8:  Grayscale uint8 array (H, W).
        kernel_name:  One of the named kernels in common/kernels.py.
        results_root: Root results directory (e.g. results/).
        roi:          Optional (x, y, w, h) crop in pixel coordinates.
                      Applied before conversion. Must be at least 3×3.
        run_id:       Optional run identifier string. Defaults to timestamp.

    Returns:
        dict with keys: run_dir, img_h, img_w, out_h, out_w, kernel_name,
                        has_roi, roi, run_id.
    """
    # --- Apply ROI if given ---
    if roi is not None:
        rx, ry, rw, rh = roi
        crop = frame_uint8[ry:ry+rh, rx:rx+rw]
        if crop.shape[0] < 3 or crop.shape[1] < 3:
            raise ValueError(f"ROI is too small for 3×3 convolution: {crop.shape}")
        source = crop
    else:
        source = frame_uint8

    H, W = source.shape

    # --- Convert to INT8 (V1 contract) ---
    image_int8  = uint8_to_int8(source)
    kernel      = KERNELS[kernel_name]
    expected    = conv2d_int8(image_int8, kernel)

    # --- Build run directory ---
    if run_id is None:
        run_id = time.strftime("%Y%m%d_%H%M%S") + f"_{kernel_name}"
        if roi is not None:
            run_id += "_roi"

    run_dir = os.path.join(results_root, "runs", run_id)
    sim_dir = os.path.join(run_dir, "sim")
    os.makedirs(sim_dir, exist_ok=True)

    # --- Write hex files ---
    write_hex_file(os.path.join(sim_dir, "input.hex"),    image_int8)
    write_hex_file(os.path.join(sim_dir, "kernel.hex"),   kernel)
    write_hex_file(os.path.join(sim_dir, "expected.hex"), expected)

    # --- Write meta.json ---
    meta = {
        "mode":        "snapshot",
        "source":      "preview_capture",
        "kernel_name": kernel_name,
        "img_h":       H,
        "img_w":       W,
        "out_h":       H - 2,
        "out_w":       W - 2,
        "seed":        None,
        "run_id":      run_id,
        "has_roi":     roi is not None,
        "roi":         list(roi) if roi is not None else None,
    }
    with open(os.path.join(sim_dir, "meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # --- Save source PNG ---
    cv2.imwrite(os.path.join(run_dir, "source.png"), source)

    return {**meta, "run_dir": run_dir, "sim_dir": sim_dir}
