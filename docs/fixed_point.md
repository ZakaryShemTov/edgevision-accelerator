# Fixed-Point Data Contract

This document defines the numeric types and arithmetic rules used by both the
Python golden reference and the RTL implementation. Both sides must follow these
rules exactly. Any divergence is a bug.

---

## 1. Data Types

| Signal        | Type   | Bit Width | Range          |
|---------------|--------|-----------|----------------|
| Input pixel   | Signed | 8 bits    | −128 to +127   |
| Kernel weight | Signed | 8 bits    | −128 to +127   |
| Accumulator   | Signed | 32 bits   | −2³¹ to 2³¹−1 |
| Output pixel  | Signed | 8 bits    | −128 to +127   |

All integers use two's complement representation.

---

## 2. Arithmetic

Each output pixel is computed as:

    accumulator = Σ (input[i] × weight[i])   for i = 0..8  (nine products)

The accumulator is a signed 32-bit integer.
Each product is a signed 16-bit value (8-bit × 8-bit = up to 16 bits).
The accumulator is wide enough to hold the sum of all nine products without overflow.

Why 32 bits? Worst case: 9 × (−128 × −128) = 9 × 16,384 = 147,456.
This exceeds INT16 (max 32,767), so INT32 is required. INT32 gives ample headroom.

---

## 3. Output Saturation

After accumulation, the INT32 result is saturated (clamped) to INT8 before writing:

    if accumulator > 127:   output = 127
    if accumulator < −128:  output = −128
    else:                   output = accumulator

This is called saturation arithmetic. It prevents wraparound (the alternative,
where overflow "wraps" to the wrong sign), which would silently corrupt results.

---

## 4. No Bias Term

V1 does not include a bias addition. The operation is:

    output = saturate( Σ input[i] × weight[i] )

Bias is a standard part of real convolution layers but is deferred to a future version.

---

## 5. No Activation Function

V1 does not apply ReLU or any other activation after the convolution.
Output values may be negative.

---

## 6. Data Layout in Hex Files

Pixels and weights are stored in row-major order (left to right, top to bottom).
One signed byte per line, represented as a two-digit hex value in two's complement.

Example: a 4×4 input image is stored as 16 lines:
    row 0: pixel[0,0], pixel[0,1], pixel[0,2], pixel[0,3]
    row 1: pixel[1,0], ...
    ...

The kernel is stored as 9 lines in row-major order:
    weight[0,0], weight[0,1], weight[0,2]
    weight[1,0], ...

The expected output is stored in the same format.
Output dimensions: (H−2) × (W−2) for an H×W input, with no padding, stride 1.

---

## 7. Verilog Type Convention

    input pixels:   reg signed [7:0]
    kernel weights: reg signed [7:0]
    accumulator:    reg signed [31:0]
    output pixels:  reg signed [7:0]
