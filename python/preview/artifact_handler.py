"""
V4 Preview — Artifact Handler

Saves snapshots and contractual outputs captured during a preview session.

Two artifact types per snapshot:
  1. Display frame  — PNG (what was shown on screen, uint8 BGR panel)
  2. Contractual    — .npy (raw INT8 output from conv2d_int8)

The .npy file is the contractual artifact: it contains the same data that
would go into sim/expected.hex if this frame were passed to gen_test_vectors.py.
This makes it clear that the visual preview and the verifiable hardware
output are distinct but derived from the same computation.

Output naming:
  preview/snapshot_<kernel>_<timestamp>.png
  preview/snapshot_<kernel>_<timestamp>_int8.npy
"""

import os
import time

import cv2
import numpy as np


def save_snapshot(
    panel_bgr:   np.ndarray,
    result_int8: np.ndarray,
    kernel_name: str,
    artifact_dir: str,
) -> None:
    """
    Save the current display panel and the contractual INT8 output.

    Args:
        panel_bgr:    BGR uint8 image (the side-by-side display frame).
        result_int8:  INT8 array from conv2d_int8 (contractual output).
        kernel_name:  Name of the kernel used (for filename).
        artifact_dir: Directory to write artifacts into.
    """
    ts = time.strftime("%Y%m%d_%H%M%S")
    stem = f"snapshot_{kernel_name}_{ts}"

    preview_dir = os.path.join(artifact_dir, "preview")
    os.makedirs(preview_dir, exist_ok=True)

    png_path = os.path.join(preview_dir, f"{stem}.png")
    npy_path = os.path.join(preview_dir, f"{stem}_int8.npy")

    cv2.imwrite(png_path, panel_bgr)
    np.save(npy_path, result_int8)

    print(f"[snapshot] {png_path}")
    print(f"[snapshot] {npy_path}  (contractual INT8 output, shape {result_int8.shape})")
