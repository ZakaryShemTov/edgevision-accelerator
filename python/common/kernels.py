"""
Named INT8 kernel definitions — shared across the full pipeline.

All kernels are signed INT8 (values fit in [-128, 127]).
Used by: gen_test_vectors.py, run_filter.py, preview engine.

Kernel semantics:
  sobel_x   — responds to vertical edges (horizontal gradient)
  sobel_y   — responds to horizontal edges (vertical gradient)
  laplacian — second-derivative edge sharpener (all-direction edges)
  gaussian  — unnormalized 3x3 Gaussian blur (scale factor 1/16 not applied)
"""

import numpy as np

KERNELS: dict[str, np.ndarray] = {
    "sobel_x": np.array([
        [-1,  0,  1],
        [-2,  0,  2],
        [-1,  0,  1],
    ], dtype=np.int8),

    "sobel_y": np.array([
        [-1, -2, -1],
        [ 0,  0,  0],
        [ 1,  2,  1],
    ], dtype=np.int8),

    "laplacian": np.array([
        [ 0,  1,  0],
        [ 1, -4,  1],
        [ 0,  1,  0],
    ], dtype=np.int8),

    "gaussian": np.array([
        [1, 2, 1],
        [2, 4, 2],
        [1, 2, 1],
    ], dtype=np.int8),
}

KERNEL_NAMES = list(KERNELS.keys())
