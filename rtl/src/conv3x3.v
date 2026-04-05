// Single-channel 3x3 fixed-point convolution engine.
//
// Accepts one 3x3 pixel patch and the kernel as flat 72-bit buses (9 packed
// signed INT8 values). Instantiates 9 combinational mac units in parallel,
// sums their INT32 products into a 32-bit accumulator, saturates to INT8,
// and registers the result on the rising edge where start is asserted.
//
// Bit layout for pixels and weights buses (both identical):
//   [71:64] = element [0,0]   (top-left)
//   [63:56] = element [0,1]
//   [55:48] = element [0,2]
//   [47:40] = element [1,0]
//   [39:32] = element [1,1]
//   [31:24] = element [1,2]
//   [23:16] = element [2,0]
//   [15: 8] = element [2,1]
//   [ 7: 0] = element [2,2]   (bottom-right)
//
// Timing:
//   Cycle N  : start=1, pixels and weights stable.
//              At posedge N the DUT registers sat_result -> result
//              and valid goes high.
//   Cycle N+1: testbench samples result (stable since posedge N).
//              start=0.
//
// Reset is synchronous, active-low.

`timescale 1ns / 1ps

module conv3x3 (
    input  wire        clk,
    input  wire        rst_n,    // synchronous active-low reset
    input  wire        start,    // assert for one cycle to latch a result

    // Packed flat buses: 9 signed INT8 values each
    input  wire [71:0] pixels,
    input  wire [71:0] weights,

    output reg  [7:0]  result,   // signed INT8 saturated output
    output reg         valid     // high one cycle after start
);

    // -----------------------------------------------------------------------
    // Saturation bounds as localparams for readability
    // -----------------------------------------------------------------------
    localparam signed [31:0] SAT_MAX =  32'sd127;
    localparam signed [31:0] SAT_MIN = -32'sd128;

    // -----------------------------------------------------------------------
    // 9 MAC units (fully combinational)
    // -----------------------------------------------------------------------
    wire signed [31:0] products [0:8];

    genvar i;
    generate
        for (i = 0; i < 9; i = i + 1) begin : mac_array
            mac u_mac (
                .a      (pixels [71 - 8*i -: 8]),   // pixel  element i
                .b      (weights[71 - 8*i -: 8]),   // kernel element i
                .product(products[i])
            );
        end
    endgenerate

    // -----------------------------------------------------------------------
    // Accumulate: sum all 9 products into one INT32 wire.
    // No overflow risk: max sum = 9 x (128 x 128) = 147,456 << INT32 max.
    // -----------------------------------------------------------------------
    wire signed [31:0] acc;
    assign acc = products[0] + products[1] + products[2] +
                 products[3] + products[4] + products[5] +
                 products[6] + products[7] + products[8];

    // -----------------------------------------------------------------------
    // Saturate INT32 accumulator to INT8 [-128, 127].
    // 8'h7F = +127,  8'h80 = -128 (two's complement).
    // -----------------------------------------------------------------------
    wire [7:0] sat_result;
    assign sat_result = (acc > SAT_MAX) ? 8'h7F :
                        (acc < SAT_MIN) ? 8'h80 :
                        acc[7:0];

    // -----------------------------------------------------------------------
    // Register output on start.
    // valid mirrors start with one cycle latency.
    // -----------------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            result <= 8'h00;
            valid  <= 1'b0;
        end else begin
            valid <= start;
            if (start)
                result <= sat_result;
        end
    end

endmodule
