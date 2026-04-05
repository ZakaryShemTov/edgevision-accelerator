"""
Visual filter pipeline for EdgeVision Accelerator — V2 demonstration layer.

Loads a grayscale PNG, converts it to INT8 (V1 contract), runs the Python
golden reference convolution with a named kernel, and saves the output as
a PNG for visual inspection.

This is the demo-facing entry point for the project. It does not modify
any RTL files or test vectors — it uses conv2d_int8 directly.

INT8 conversion convention (shared with gen_test_vectors.py --image mode):
    int8_pixel = uint8_pixel - 128
    uint8_pixel = int8_output + 128  (for display only, clipped to [0, 255])

Available kernels (all INT8-compatible, no division required):
    sobel_x   — horizontal edge detection (responds to vertical edges)
    sobel_y   — vertical edge detection (responds to horizontal edges)
    laplacian — second-derivative edge sharpening
    gaussian  — unnormalized 3x3 approximation (scale factor 1/16 not applied)

Usage:
    python3 run_filter.py
    python3 run_filter.py --image path/to/image.png --kernel sobel_x
    python3 run_filter.py --kernel laplacian --output-dir results/
"""

import argparse
import os
import sys

import numpy as np

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_GOLDEN_DIR = os.path.join(_THIS_DIR, "..", "golden")
_COMMON_DIR = os.path.join(_THIS_DIR, "..", "common")
sys.path.insert(0, _GOLDEN_DIR)
sys.path.insert(0, _COMMON_DIR)

from conv_reference import conv2d_int8              # noqa: E402
from kernels import KERNELS                         # noqa: E402
from conversions import uint8_to_int8, int8_to_uint8_display  # noqa: E402

try:
    from PIL import Image as PILImage
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use("Agg")   # headless — safe in all environments
    import matplotlib.pyplot as plt
    _MPL_AVAILABLE = True
except ImportError:
    _MPL_AVAILABLE = False



# ---------------------------------------------------------------------------
# Image I/O helpers
# ---------------------------------------------------------------------------

def load_grayscale_uint8(path: str) -> np.ndarray:
    """Load a PNG (or any PIL-readable format) as a uint8 grayscale array."""
    if not _PIL_AVAILABLE:
        raise RuntimeError(
            "Pillow is required for image loading.\n"
            "Install with: pip3 install Pillow"
        )
    img = PILImage.open(path).convert("L")   # "L" = 8-bit grayscale
    return np.array(img, dtype=np.uint8)


def load_cameraman() -> np.ndarray:
    """
    Return the standard 256x256 cameraman test image as uint8.

    Tries scikit-image first (canonical source). If not installed, prints
    instructions and exits. The image can also be saved locally with:
        python3 -c "from skimage import data; ..."  (see README)
    """
    try:
        from skimage import data as skdata
        return skdata.camera()      # uint8, shape (256, 256)
    except ImportError:
        print(
            "scikit-image is needed to load the cameraman image.\n"
            "Install with:  pip3 install scikit-image\n"
            "Or pass a PNG directly:  --image path/to/image.png",
            file=sys.stderr
        )
        sys.exit(1)



def save_png(array_uint8: np.ndarray, path: str) -> None:
    """Save a uint8 2D array as a grayscale PNG."""
    if not _PIL_AVAILABLE:
        raise RuntimeError("Pillow required. Install with: pip3 install Pillow")
    PILImage.fromarray(array_uint8, mode="L").save(path)


# ---------------------------------------------------------------------------
# Side-by-side comparison figure
# ---------------------------------------------------------------------------

def save_comparison(
    original_uint8: np.ndarray,
    output_uint8:   np.ndarray,
    kernel_name:    str,
    out_path:       str,
) -> None:
    """
    Save a two-panel figure: original image | filtered output.
    Requires matplotlib. Skipped (with a warning) if not available.
    """
    if not _MPL_AVAILABLE:
        print("matplotlib not found — skipping comparison figure.")
        print("Install with: pip3 install matplotlib")
        return

    fig, axes = plt.subplots(1, 2, figsize=(10, 5))
    fig.suptitle(f"EdgeVision Accelerator — {kernel_name} filter (Python golden reference)",
                 fontsize=12)

    axes[0].imshow(original_uint8, cmap="gray", vmin=0, vmax=255)
    axes[0].set_title("Input (grayscale)")
    axes[0].axis("off")

    axes[1].imshow(output_uint8, cmap="gray", vmin=0, vmax=255)
    axes[1].set_title(f"Output — {kernel_name}")
    axes[1].axis("off")

    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a named INT8 filter on a grayscale image (V2 demo)."
    )
    parser.add_argument(
        "--image", type=str, default=None,
        help="Path to input PNG. Defaults to the standard cameraman test image."
    )
    parser.add_argument(
        "--kernel", type=str, default="sobel_x",
        choices=list(KERNELS.keys()),
        help="Filter kernel to apply (default: sobel_x)."
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Directory for output PNGs (default: <project-root>/results/)."
    )
    args = parser.parse_args()

    # --- Resolve output directory ---
    if args.output_dir is not None:
        out_dir = os.path.abspath(args.output_dir)
    else:
        _PROJECT_ROOT = os.path.join(_THIS_DIR, "..", "..")
        out_dir = os.path.abspath(os.path.join(_PROJECT_ROOT, "results"))
    os.makedirs(out_dir, exist_ok=True)

    # --- Load image ---
    if args.image is not None:
        print(f"Loading image: {args.image}")
        img_uint8 = load_grayscale_uint8(args.image)
        stem = os.path.splitext(os.path.basename(args.image))[0]
    else:
        print("Loading cameraman (default demo image)...")
        img_uint8 = load_cameraman()
        stem = "cameraman"

    H, W = img_uint8.shape
    print(f"Image size:  {H}x{W}")

    # --- Convert to INT8 (V1 contract) ---
    img_int8 = uint8_to_int8(img_uint8)

    # --- Apply filter ---
    kernel = KERNELS[args.kernel]
    print(f"Kernel:      {args.kernel}")
    print(f"Kernel values:\n{kernel}")

    output_int8 = conv2d_int8(img_int8, kernel)
    out_H, out_W = output_int8.shape
    print(f"Output size: {out_H}x{out_W}  (input shrinks by 2 each side, no padding)")

    # --- Convert outputs to uint8 for display ---
    output_uint8 = int8_to_uint8_display(output_int8)
    # Crop input to match output size (remove 1-pixel border) for fair comparison
    input_cropped_uint8 = img_uint8[1:H-1, 1:W-1]

    # --- Save PNGs ---
    input_path  = os.path.join(out_dir, f"{stem}_input.png")
    output_path = os.path.join(out_dir, f"{stem}_{args.kernel}_python.png")
    comparison_path = os.path.join(out_dir, f"{stem}_{args.kernel}_comparison.png")

    save_png(img_uint8, input_path)
    save_png(output_uint8, output_path)
    save_comparison(input_cropped_uint8, output_uint8, args.kernel, comparison_path)

    print(f"\nWritten to: {out_dir}/")
    print(f"  {os.path.basename(input_path)}")
    print(f"  {os.path.basename(output_path)}")
    if _MPL_AVAILABLE:
        print(f"  {os.path.basename(comparison_path)}")

    # --- Numeric summary ---
    print(f"\nOutput stats (INT8):")
    print(f"  min={int(output_int8.min()):4d}  max={int(output_int8.max()):4d}"
          f"  mean={float(output_int8.astype(np.float32).mean()):.1f}")
    sat_count = int(np.sum((output_int8 == 127) | (output_int8 == -128)))
    print(f"  saturated pixels: {sat_count} / {out_H * out_W}")


if __name__ == "__main__":
    main()
