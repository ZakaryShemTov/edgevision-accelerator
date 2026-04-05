"""
Golden reference implementation of single-channel 2D convolution.

Implements the fixed-point arithmetic contract defined in docs/fixed_point.md:
  - Input pixels:   signed INT8
  - Kernel weights: signed INT8
  - Accumulator:    signed INT32 (matches RTL accumulator width)
  - Output pixels:  signed INT8, saturated to [-128, 127]
  - No padding, stride 1
  - Output shape: (H-2, W-2) for an H x W input

This function is the oracle for RTL verification. The RTL output must match
this function exactly for all test inputs.
"""

import numpy as np


def conv2d_int8(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """
    Single-channel 3x3 convolution with saturated INT8 output.

    Args:
        image:  2D numpy array, dtype int8, shape (H, W), H >= 3, W >= 3
        kernel: 2D numpy array, dtype int8, shape (3, 3)

    Returns:
        2D numpy array, dtype int8, shape (H-2, W-2)
    """
    if image.ndim != 2:
        raise ValueError(f"image must be 2D, got shape {image.shape}")
    if kernel.shape != (3, 3):
        raise ValueError(f"kernel must be shape (3, 3), got {kernel.shape}")
    if image.dtype != np.int8:
        raise TypeError(f"image must be dtype int8, got {image.dtype}")
    if kernel.dtype != np.int8:
        raise TypeError(f"kernel must be dtype int8, got {kernel.dtype}")

    H, W = image.shape
    if H < 3 or W < 3:
        raise ValueError(f"image must be at least 3x3, got {H}x{W}")

    out_h = H - 2
    out_w = W - 2

    # Accumulate in INT32 to match RTL accumulator width.
    # Cast to int32 before arithmetic to prevent numpy from silently
    # overflowing during the multiply-accumulate step.
    output = np.zeros((out_h, out_w), dtype=np.int32)
    k = kernel.astype(np.int32)

    for r in range(out_h):
        for c in range(out_w):
            patch = image[r:r+3, c:c+3].astype(np.int32)
            output[r, c] = np.sum(patch * k)

    # Saturate INT32 accumulator to INT8 range [-128, 127].
    # np.clip implements saturation (no wraparound).
    output = np.clip(output, -128, 127)

    return output.astype(np.int8)
