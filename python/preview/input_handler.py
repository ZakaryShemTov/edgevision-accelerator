"""
V4 Preview — Input Handler

Responsible for loading and normalizing input to the preview engine.
Handles two source types:
  - Static image (PNG or any OpenCV-readable format)
  - Video file (MP4, AVI, etc.)

All outputs are uint8 grayscale numpy arrays.
INT8 conversion (V1 contract: int8 = uint8 - 128) is done here so the
rest of the pipeline always works in the contractual domain.
"""

import os
import sys

import cv2
import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS_DIR, "..", "common"))

from conversions import uint8_to_int8, int8_to_uint8_display  # noqa: E402


def load_image(path: str) -> np.ndarray:
    """
    Load an image file as a uint8 grayscale array.
    Raises FileNotFoundError if the path does not exist.
    Raises ValueError if OpenCV cannot decode the file.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Image not found: {path}")
    frame = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if frame is None:
        raise ValueError(f"Could not decode image: {path}")
    return frame  # dtype uint8, shape (H, W)


def open_video(path: str) -> cv2.VideoCapture:
    """
    Open a video file and return a VideoCapture handle.
    Raises FileNotFoundError if the path does not exist.
    Raises RuntimeError if OpenCV cannot open the file.
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Video not found: {path}")
    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {path}")
    return cap


def read_frame_gray(cap: cv2.VideoCapture) -> np.ndarray | None:
    """
    Read the next grayscale frame from a VideoCapture.
    Returns None when the video is exhausted.
    """
    ok, frame = cap.read()
    if not ok:
        return None
    if frame.ndim == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return frame  # dtype uint8


def resize_for_preview(frame: np.ndarray, max_dim: int = 320) -> np.ndarray:
    """
    Resize a frame so its largest dimension does not exceed max_dim.
    Aspect ratio is preserved. Returns the frame unchanged if already small enough.

    Used for video mode to keep per-frame conv2d_int8 (pure Python loops)
    fast enough for interactive preview.
    """
    h, w = frame.shape[:2]
    if max(h, w) <= max_dim:
        return frame
    scale = max_dim / max(h, w)
    new_w = max(3, int(w * scale))
    new_h = max(3, int(h * scale))
    return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_AREA)



def video_fps(cap: cv2.VideoCapture) -> float:
    """Return the FPS of an open VideoCapture, defaulting to 25.0."""
    fps = cap.get(cv2.CAP_PROP_FPS)
    return fps if fps > 0 else 25.0
