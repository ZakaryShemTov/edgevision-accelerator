"""
V4 Preview — Preview Engine

Applies the INT8 filter and manages the OpenCV display loop.

Responsibilities:
  - apply_filter: wraps conv2d_int8, returns the contractual INT8 output
  - make_panel:   builds the side-by-side display frame (uint8, display-only)
  - run_image_preview: single-image interactive display
  - run_video_preview: frame-by-frame video display loop

Separation of concerns:
  - "Contractual output"  = raw int8 array from conv2d_int8.
                            This is what would go into sim/expected.hex.
  - "Display output"      = uint8 panel shown on screen.
                            Derived via int8 + 128 for visualization only.
                            Never used for verification.

Keyboard controls (shown in window title):
  Q / Esc   — quit
  S         — save snapshot (display panel + contractual int8 .npy)
  1         — switch to sobel_x
  2         — switch to sobel_y
  3         — switch to laplacian
"""

import os
import sys
import time

import cv2
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS_DIR, "..", "golden"))
sys.path.insert(0, os.path.join(_THIS_DIR, "..", "common"))

from conv_reference import conv2d_int8  # noqa: E402
from kernels import KERNELS, KERNEL_NAMES  # noqa: E402
from input_handler import (  # noqa: E402
    uint8_to_int8,
    int8_to_uint8_display,
    resize_for_preview,
    read_frame_gray,
    video_fps,
)

# Kernel shortcut keys: '1' → sobel_x, '2' → sobel_y, '3' → laplacian
_KEY_KERNEL_MAP = {
    ord("1"): "sobel_x",
    ord("2"): "sobel_y",
    ord("3"): "laplacian",
}

_PANEL_LABEL_COLOR = (200, 200, 200)  # light gray text on dark background
_LABEL_HEIGHT = 20                     # pixels reserved for label strip


def apply_filter(frame_uint8: np.ndarray, kernel_name: str) -> np.ndarray:
    """
    Apply the named kernel to a uint8 grayscale frame.

    Returns the contractual INT8 output from conv2d_int8.
    The caller is responsible for display conversion if needed.
    """
    frame_int8 = uint8_to_int8(frame_uint8)
    kernel = KERNELS[kernel_name]
    return conv2d_int8(frame_int8, kernel)  # dtype int8


def make_panel(
    original_uint8: np.ndarray,
    filtered_int8:  np.ndarray,
    kernel_name:    str,
) -> np.ndarray:
    """
    Build a side-by-side display panel:
      [  Original (cropped)  |  Filtered (int8+128)  ]

    The original is cropped by 1 pixel on each side to match the output
    dimensions (no-padding convolution shrinks by 2 in each axis).

    Both panels have a thin label strip at the top. Returns a uint8 BGR
    image suitable for cv2.imshow.
    """
    H_orig, W_orig = original_uint8.shape
    # Crop original to match output size
    orig_crop = original_uint8[1:H_orig-1, 1:W_orig-1]

    filtered_disp = int8_to_uint8_display(filtered_int8)

    # Convert both to BGR for cv2 (grayscale → 3-channel)
    left  = cv2.cvtColor(orig_crop,      cv2.COLOR_GRAY2BGR)
    right = cv2.cvtColor(filtered_disp,  cv2.COLOR_GRAY2BGR)

    # Add label strips
    left  = _add_label(left,  "Input")
    right = _add_label(right, f"{kernel_name}  [INT8+128]")

    # Divider line (1px wide, white)
    divider = np.full((left.shape[0], 1, 3), 180, dtype=np.uint8)

    return np.hstack([left, divider, right])


def _add_label(img_bgr: np.ndarray, text: str) -> np.ndarray:
    """Prepend a dark label strip above a BGR image."""
    h, w = img_bgr.shape[:2]
    strip = np.zeros((_LABEL_HEIGHT, w, 3), dtype=np.uint8)
    cv2.putText(
        strip, text, (4, _LABEL_HEIGHT - 5),
        cv2.FONT_HERSHEY_SIMPLEX, 0.38, _PANEL_LABEL_COLOR, 1, cv2.LINE_AA
    )
    return np.vstack([strip, img_bgr])


def _build_title(kernel_name: str, extra: str = "") -> str:
    base = "EdgeVision Preview  |  1:sobel_x  2:sobel_y  3:laplacian  S:save  V:validate  Q:quit"
    if extra:
        base += f"  |  {extra}"
    return base


def _run_validation_async(image_uint8: np.ndarray, kernel_name: str,
                          artifact_dir: str) -> None:
    """
    Launch validate_snapshot pipeline in a background thread so the
    preview window stays responsive during RTL simulation.
    """
    import threading

    def _worker():
        try:
            from snapshot_exporter   import export_snapshot
            from rtl_runner          import run_rtl_simulation
            from validation_reporter import generate_report

            _PROJECT_ROOT = os.path.abspath(
                os.path.join(_THIS_DIR, "..", "..")
            )
            print("[validate] Exporting test vectors...")
            run_info = export_snapshot(image_uint8, kernel_name, artifact_dir)
            print(f"[validate] Run dir: {run_info['run_dir']}")

            print("[validate] Running RTL simulation...")
            rtl_result = run_rtl_simulation(run_info, _PROJECT_ROOT)

            if rtl_result.status == "no_simulator":
                print(f"[validate] Skipped — {rtl_result.sim_log}")
                return
            if rtl_result.status == "error":
                print(f"[validate] Simulation error:\n{rtl_result.sim_log}")
                return

            print("[validate] Generating report...")
            metrics = generate_report(
                run_info     = run_info,
                rtl_hex_path = rtl_result.rtl_hex_path,
                sim_log      = rtl_result.sim_log,
                source_uint8 = image_uint8,
            )
            status = metrics["status"].upper()
            print(f"[validate] {status}  "
                  f"{metrics['matches']}/{metrics['total_pixels']} match  "
                  f"board → {run_info['run_dir']}/board.png")
        except Exception as exc:
            print(f"[validate] ERROR: {exc}")

    threading.Thread(target=_worker, daemon=True).start()


# ---------------------------------------------------------------------------
# Image preview
# ---------------------------------------------------------------------------

def run_image_preview(
    image_uint8:  np.ndarray,
    kernel_name:  str,
    artifact_dir: str,
) -> None:
    """
    Display a static image with the selected filter.
    Recomputes on kernel switch (instantaneous for images).
    """
    from artifact_handler import save_snapshot

    current_kernel = kernel_name
    panel = None

    def _refresh():
        nonlocal panel
        result_int8 = apply_filter(image_uint8, current_kernel)
        panel = make_panel(image_uint8, result_int8, current_kernel)

    _refresh()
    window = "EdgeVision Preview"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)
    cv2.setWindowTitle(window, _build_title(current_kernel))
    cv2.imshow(window, panel)

    while True:
        key = cv2.waitKey(50) & 0xFF

        if key in (ord("q"), ord("Q"), 27):   # Q or Esc
            break

        if key in _KEY_KERNEL_MAP:
            new_kernel = _KEY_KERNEL_MAP[key]
            if new_kernel != current_kernel:
                current_kernel = new_kernel
                _refresh()
                cv2.setWindowTitle(window, _build_title(current_kernel))
                cv2.imshow(window, panel)

        if key in (ord("s"), ord("S")):
            result_int8 = apply_filter(image_uint8, current_kernel)
            save_snapshot(panel, result_int8, current_kernel, artifact_dir)

        if key in (ord("v"), ord("V")):
            print(f"[V] Launching validation for current frame + kernel={current_kernel}")
            _run_validation_async(image_uint8, current_kernel, artifact_dir)

        # Close button
        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            break

    cv2.destroyAllWindows()


# ---------------------------------------------------------------------------
# Video preview
# ---------------------------------------------------------------------------

def run_video_preview(
    cap,
    kernel_name:  str,
    max_dim:      int,
    artifact_dir: str,
) -> None:
    """
    Display a video file frame-by-frame with the selected filter.
    Loops back to the beginning when the video ends.

    Frames are resized to max_dim before processing to keep conv2d_int8
    fast enough for interactive preview. The resize is applied to the
    preview only — contractual snapshots use the resized frame dimensions
    (the same data the preview engine sees).
    """
    from artifact_handler import save_snapshot

    current_kernel = kernel_name
    fps = video_fps(cap)
    frame_delay_ms = max(1, int(1000 / fps))

    window = "EdgeVision Preview"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)

    while True:
        frame_raw = read_frame_gray(cap)
        if frame_raw is None:
            # End of video — loop
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        frame = resize_for_preview(frame_raw, max_dim)
        result_int8 = apply_filter(frame, current_kernel)
        panel = make_panel(frame, result_int8, current_kernel)

        cv2.setWindowTitle(window, _build_title(current_kernel))
        cv2.imshow(window, panel)

        key = cv2.waitKey(frame_delay_ms) & 0xFF

        if key in (ord("q"), ord("Q"), 27):
            break

        if key in _KEY_KERNEL_MAP:
            current_kernel = _KEY_KERNEL_MAP[key]

        if key in (ord("s"), ord("S")):
            save_snapshot(panel, result_int8, current_kernel, artifact_dir)

        if key in (ord("v"), ord("V")):
            print(f"[V] Launching validation for current frame + kernel={current_kernel}")
            _run_validation_async(frame, current_kernel, artifact_dir)

        if cv2.getWindowProperty(window, cv2.WND_PROP_VISIBLE) < 1:
            break

    cap.release()
    cv2.destroyAllWindows()
