"""
Unit tests for the golden reference convolution.

Each test verifies one specific behavioral guarantee from docs/fixed_point.md.
These tests must all pass before the golden reference is used to verify RTL.
"""

import numpy as np
import pytest
from conv_reference import conv2d_int8


# ---------------------------------------------------------------------------
# Test 1: Known computation with hand-verifiable values
#
# Input 3x3 image with values 1..9, all-ones kernel.
# Each output pixel is the sum of the 3x3 patch under the kernel.
# For a 3x3 input, there is exactly one output pixel.
# Expected: 1+2+3+4+5+6+7+8+9 = 45
# ---------------------------------------------------------------------------
def test_known_values_all_ones_kernel():
    image = np.array([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ], dtype=np.int8)

    kernel = np.ones((3, 3), dtype=np.int8)

    result = conv2d_int8(image, kernel)

    expected = np.array([[45]], dtype=np.int8)
    np.testing.assert_array_equal(result, expected)


# ---------------------------------------------------------------------------
# Test 2: All-zeros input
#
# Any kernel applied to a zero image must produce a zero output.
# ---------------------------------------------------------------------------
def test_all_zeros_input():
    image = np.zeros((5, 5), dtype=np.int8)
    kernel = np.array([
        [1, 2, 3],
        [4, 5, 6],
        [7, 8, 9],
    ], dtype=np.int8)

    result = conv2d_int8(image, kernel)

    assert result.shape == (3, 3)
    np.testing.assert_array_equal(result, np.zeros((3, 3), dtype=np.int8))


# ---------------------------------------------------------------------------
# Test 3: Positive saturation
#
# Accumulator exceeds +127 and must be clamped to 127.
# Input: all 10s. Kernel: all 10s.
# Each product: 10 * 10 = 100. Sum of 9 products: 900.
# 900 > 127, so output must be 127.
# ---------------------------------------------------------------------------
def test_positive_saturation():
    image = np.full((3, 3), 10, dtype=np.int8)
    kernel = np.full((3, 3), 10, dtype=np.int8)

    result = conv2d_int8(image, kernel)

    expected = np.array([[127]], dtype=np.int8)
    np.testing.assert_array_equal(result, expected)


# ---------------------------------------------------------------------------
# Test 4: Negative saturation
#
# Accumulator falls below -128 and must be clamped to -128.
# Input: all -10s. Kernel: all 10s.
# Each product: -10 * 10 = -100. Sum of 9 products: -900.
# -900 < -128, so output must be -128.
# ---------------------------------------------------------------------------
def test_negative_saturation():
    image = np.full((3, 3), -10, dtype=np.int8)
    kernel = np.full((3, 3), 10, dtype=np.int8)

    result = conv2d_int8(image, kernel)

    expected = np.array([[-128]], dtype=np.int8)
    np.testing.assert_array_equal(result, expected)


# ---------------------------------------------------------------------------
# Test 5: Output shape
#
# For an H x W input, output must be (H-2) x (W-2).
# Tests several sizes to confirm the formula holds.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("H, W", [(3, 3), (4, 4), (5, 7), (8, 6)])
def test_output_shape(H, W):
    image = np.zeros((H, W), dtype=np.int8)
    kernel = np.zeros((3, 3), dtype=np.int8)

    result = conv2d_int8(image, kernel)

    assert result.shape == (H - 2, W - 2)


# ---------------------------------------------------------------------------
# Test 6: Identity kernel
#
# A kernel with 1 in the center and 0 everywhere else acts as an identity:
# each output pixel equals the corresponding center pixel of the input patch,
# i.e., the input shifted inward by one pixel on each side.
#
#   kernel = [[0, 0, 0],
#             [0, 1, 0],
#             [0, 0, 0]]
#
# For a 5x5 input, the output is the inner 3x3 region: image[1:4, 1:4].
# ---------------------------------------------------------------------------
def test_identity_kernel():
    image = np.array([
        [ 1,  2,  3,  4,  5],
        [ 6,  7,  8,  9, 10],
        [11, 12, 13, 14, 15],
        [16, 17, 18, 19, 20],
        [21, 22, 23, 24, 25],
    ], dtype=np.int8)

    kernel = np.array([
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0],
    ], dtype=np.int8)

    result = conv2d_int8(image, kernel)

    expected = image[1:4, 1:4].copy()
    np.testing.assert_array_equal(result, expected)


# ---------------------------------------------------------------------------
# Test 7: Vertical edge detector (worked example from Step 2 proposal)
#
# Validates the hand-calculated example shown during design.
# Output pixel at (0, 0) must equal -20.
# ---------------------------------------------------------------------------
def test_vertical_edge_detector():
    image = np.array([
        [ 10,  20,  30,  40,  50],
        [ 60,  70,  80,  90, 100],
        [-10, -20, -30, -40, -50],
        [  5,  15,  25,  35,  45],
        [  0,   0,   0,   0,   0],
    ], dtype=np.int8)

    kernel = np.array([
        [ 1,  0, -1],
        [ 1,  0, -1],
        [ 1,  0, -1],
    ], dtype=np.int8)

    result = conv2d_int8(image, kernel)

    assert result[0, 0] == -20, f"Expected -20 at (0,0), got {result[0, 0]}"


# ---------------------------------------------------------------------------
# Input validation tests
# ---------------------------------------------------------------------------
def test_rejects_non_2d_image():
    with pytest.raises(ValueError, match="2D"):
        conv2d_int8(np.zeros((3, 3, 1), dtype=np.int8),
                    np.zeros((3, 3), dtype=np.int8))


def test_rejects_wrong_kernel_shape():
    with pytest.raises(ValueError, match="3, 3"):
        conv2d_int8(np.zeros((5, 5), dtype=np.int8),
                    np.zeros((4, 4), dtype=np.int8))


def test_rejects_wrong_dtype():
    with pytest.raises(TypeError, match="int8"):
        conv2d_int8(np.zeros((5, 5), dtype=np.float32),
                    np.zeros((3, 3), dtype=np.int8))


def test_rejects_image_too_small():
    with pytest.raises(ValueError, match="3x3"):
        conv2d_int8(np.zeros((2, 5), dtype=np.int8),
                    np.zeros((3, 3), dtype=np.int8))
