"""
Shared INT8 ↔ uint8 conversion utilities for the EdgeVision pipeline.

Used by: run_filter.py, input_handler.py,
         compare_outputs.py, validation_reporter.py.

Convention (V1 contract):
    int8  = uint8 - 128      maps  0 → -128,  128 → 0,   255 → +127
    uint8 = int8  + 128      maps -128 → 0,    0 → 128,  +127 → 255

The uint8 → int8 direction is the contractual conversion applied to
all input images before convolution.

The int8 → uint8 direction is used only for display and PNG export;
it is never used as input to conv2d_int8.
"""

import numpy as np


def uint8_to_int8(arr: np.ndarray) -> np.ndarray:
    """
    Convert uint8 [0, 255] → int8 [-128, 127].
    Applied to input images before entering the fixed-point pipeline.
    """
    return (arr.astype(np.int32) - 128).astype(np.int8)


def int8_to_uint8_display(arr: np.ndarray) -> np.ndarray:
    """
    Convert int8 [-128, 127] → uint8 [0, 255] for display/PNG output only.
    Never used as convolution input.
    """
    return np.clip(arr.astype(np.int32) + 128, 0, 255).astype(np.uint8)
