// Signed 8x8 multiply, 32-bit signed output.
//
// Purely combinational — no clock, no state.
// Instantiated nine times inside conv3x3 to form the 3x3 MAC array.
//
// Why 32-bit output?
//   INT8 x INT8 can produce up to 8+8 = 16 significant bits. We output
//   32 bits so conv3x3 can sum all nine products in a 32-bit accumulator
//   without overflow. The worst-case sum is 9 x (128 x 128) = 147,456,
//   which is well within INT32 range.
//
// Why sign-extend before multiplying?
//   In Verilog, the result of a * b has the width of the wider operand.
//   Without explicit extension, both operands are 8-bit and the product
//   would be silently truncated to 8 bits. Extending both to 32 bits
//   first gives a correct 32-bit signed result.

`timescale 1ns / 1ps

module mac (
    input  wire signed [7:0]  a,
    input  wire signed [7:0]  b,
    output wire signed [31:0] product
);

    wire signed [31:0] a32 = {{24{a[7]}}, a};   // sign-extend a to 32 bits
    wire signed [31:0] b32 = {{24{b[7]}}, b};   // sign-extend b to 32 bits

    assign product = a32 * b32;

endmodule
