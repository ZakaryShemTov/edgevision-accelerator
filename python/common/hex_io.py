"""
Shared hex file I/O for the EdgeVision pipeline.

Used by: gen_test_vectors.py, snapshot_exporter.py,
         compare_outputs.py, validation_reporter.py.

Format: one signed byte per line, two hex digits, two's-complement.
  -1   → ff
  -128 → 80
   127 → 7f

This is the format Verilog's $readmemh expects for signed [7:0] registers.
"""

import numpy as np


def to_hex_line(value: np.int8) -> str:
    """Signed INT8 → two-digit two's-complement hex string."""
    return format(int(value) & 0xFF, "02x")


def write_hex_file(path: str, array: np.ndarray) -> None:
    """Write a numpy INT8 array to a hex file, one byte per line, row-major."""
    with open(path, "w") as f:
        for value in array.flat:
            f.write(to_hex_line(value) + "\n")


def read_hex_file(path: str, count: int) -> np.ndarray:
    """
    Read `count` signed INT8 values from a hex file (one value per line).
    Raises ValueError if the line count does not match.
    Returns a flat np.int8 array.
    """
    values = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                v = int(line, 16)
                if v >= 0x80:
                    v -= 0x100
                values.append(v)
    if len(values) != count:
        raise ValueError(f"Expected {count} values in {path}, got {len(values)}")
    return np.array(values, dtype=np.int8)
