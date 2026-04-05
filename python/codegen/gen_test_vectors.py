"""
Test vector generator for RTL simulation.

Supports two modes:

  Random mode (default, V1 baseline):
    Generates a random INT8 image and kernel seeded for reproducibility.

        python3 gen_test_vectors.py
        python3 gen_test_vectors.py --seed 42 --height 8 --width 8

  Image mode (V2 extension):
    Loads a grayscale PNG, converts to INT8 (uint8 - 128), applies a named
    kernel. Same hex output format — no RTL changes required.

        python3 gen_test_vectors.py --image data/cameraman.png --kernel sobel_x

In both modes, writes:
    sim/input.hex     -- input image pixels, row-major
    sim/kernel.hex    -- 3x3 kernel weights, row-major
    sim/expected.hex  -- golden output pixels, row-major
    sim/meta.json     -- image dimensions and run metadata (used by compare_outputs.py)

Each hex file contains one signed byte per line in two's-complement hex.
This is the format expected by Verilog's $readmemh with signed [7:0] registers.

INT8 conversion (image mode):
    int8_pixel = uint8_pixel - 128
    Maps 0→-128, 128→0, 255→127. Shared convention with run_filter.py.
"""

import argparse
import json
import os
import sys

import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_GOLDEN_DIR = os.path.join(_THIS_DIR, "..", "golden")
_COMMON_DIR = os.path.join(_THIS_DIR, "..", "common")
sys.path.insert(0, _GOLDEN_DIR)
sys.path.insert(0, _COMMON_DIR)

from conv_reference import conv2d_int8        # noqa: E402
from kernels import KERNELS                   # noqa: E402
from hex_io import write_hex_file             # noqa: E402
from conversions import uint8_to_int8         # noqa: E402


# ---------------------------------------------------------------------------
# Image loading (image mode only)
# ---------------------------------------------------------------------------

def _load_png_as_int8(path: str) -> np.ndarray:
    """
    Load a grayscale PNG and convert to INT8 using the V1 convention:
        int8 = uint8 - 128
    Returns a 2D np.int8 array.
    """
    try:
        from PIL import Image as PILImage
    except ImportError:
        print(
            "Error: Pillow is required for --image mode.\n"
            "Install with: pip3 install Pillow",
            file=sys.stderr
        )
        sys.exit(1)

    img = PILImage.open(path).convert("L")
    return uint8_to_int8(np.array(img, dtype=np.uint8))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate INT8 convolution test vectors for RTL simulation.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  Random mode:  python3 gen_test_vectors.py --seed 0 --height 8 --width 8\n"
            "  Image mode:   python3 gen_test_vectors.py --image data/cameraman.png --kernel sobel_x\n"
        )
    )

    # --- Random mode arguments ---
    parser.add_argument(
        "--seed", type=int, default=0,
        help="Random seed (random mode only, default: 0)."
    )
    parser.add_argument(
        "--height", type=int, default=8,
        help="Image height in pixels (random mode only, default: 8, minimum: 3)."
    )
    parser.add_argument(
        "--width", type=int, default=8,
        help="Image width in pixels (random mode only, default: 8, minimum: 3)."
    )

    # --- Image mode arguments ---
    parser.add_argument(
        "--image", type=str, default=None,
        help="Path to a grayscale PNG (activates image mode)."
    )
    parser.add_argument(
        "--kernel", type=str, default="sobel_x",
        choices=list(KERNELS.keys()),
        help="Named kernel to use in image mode (default: sobel_x)."
    )

    # --- Shared ---
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Directory to write hex files (default: <project-root>/sim/)."
    )
    args = parser.parse_args()

    # --- Resolve output directory ---
    if args.output_dir is not None:
        out_dir = os.path.abspath(args.output_dir)
    else:
        _PROJECT_ROOT = os.path.join(_THIS_DIR, "..", "..")
        out_dir = os.path.abspath(os.path.join(_PROJECT_ROOT, "sim"))
    os.makedirs(out_dir, exist_ok=True)

    # --- Build image and kernel depending on mode ---
    if args.image is not None:
        # Image mode: load PNG, convert to INT8, use named kernel
        img_path = os.path.abspath(args.image)
        if not os.path.isfile(img_path):
            print(f"Error: image file not found: {img_path}", file=sys.stderr)
            sys.exit(1)

        image  = _load_png_as_int8(img_path)
        kernel = KERNELS[args.kernel]
        source = img_path
        mode   = "image"

        H, W = image.shape
        if H < 3 or W < 3:
            print(f"Error: image must be at least 3x3, got {H}x{W}.", file=sys.stderr)
            sys.exit(1)

    else:
        # Random mode: existing V1 behavior
        if args.height < 3 or args.width < 3:
            print("Error: --height and --width must each be at least 3.", file=sys.stderr)
            sys.exit(1)

        rng    = np.random.default_rng(args.seed)
        image  = rng.integers(-128, 128, size=(args.height, args.width), dtype=np.int8)
        kernel = rng.integers(-128, 128, size=(3, 3), dtype=np.int8)
        source = "random"
        mode   = "random"
        H, W   = image.shape

    # --- Run golden reference ---
    expected = conv2d_int8(image, kernel)
    out_h = H - 2
    out_w = W - 2

    # --- Write hex files ---
    input_path    = os.path.join(out_dir, "input.hex")
    kernel_path   = os.path.join(out_dir, "kernel.hex")
    expected_path = os.path.join(out_dir, "expected.hex")

    write_hex_file(input_path,    image)
    write_hex_file(kernel_path,   kernel)
    write_hex_file(expected_path, expected)

    # --- Write metadata for compare_outputs.py ---
    meta = {
        "mode":        mode,
        "source":      source,
        "kernel_name": args.kernel if mode == "image" else "random",
        "img_h":       H,
        "img_w":       W,
        "out_h":       out_h,
        "out_w":       out_w,
        "seed":        args.seed if mode == "random" else None,
    }
    meta_path = os.path.join(out_dir, "meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    # --- Report ---
    print(f"Mode:        {mode}")
    if mode == "image":
        print(f"Source:      {source}")
        print(f"Kernel:      {args.kernel}")
    else:
        print(f"Seed:        {args.seed}")
    print(f"Image:       {H}x{W}  ({H * W} bytes)")
    print(f"Kernel:      3x3      (9 bytes)")
    print(f"Output:      {out_h}x{out_w}  ({out_h * out_w} bytes)")
    print(f"Written to:  {out_dir}/")
    print(f"  {os.path.basename(input_path)}")
    print(f"  {os.path.basename(kernel_path)}")
    print(f"  {os.path.basename(expected_path)}")
    print(f"  {os.path.basename(meta_path)}")


if __name__ == "__main__":
    main()
