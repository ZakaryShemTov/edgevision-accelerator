"""
EdgeVision Accelerator — V4 Interactive Preview

Launch a live interactive preview of the INT8 convolution pipeline on an
image or video file. The display updates in real time; the kernel can be
switched on the fly with keyboard shortcuts.

Usage:
    python3 preview.py --image data/cameraman.png
    python3 preview.py --image data/cameraman.png --kernel laplacian
    python3 preview.py --video path/to/video.mp4
    python3 preview.py --video path/to/video.mp4 --max-dim 480

Keyboard controls:
    1   — switch to sobel_x
    2   — switch to sobel_y
    3   — switch to laplacian
    S   — save snapshot (display PNG + contractual INT8 .npy → results/preview/)
    Q / Esc — quit

Architecture:
    preview.py          ← this file: CLI, argument parsing, top-level dispatch
    input_handler.py    ← load / resize / convert input frames
    preview_engine.py   ← apply filter, build display panel, run event loop
    artifact_handler.py ← save snapshots (display + contractual output)

The preview uses the same conv2d_int8 function as the golden reference and
the RTL test vector pipeline. No separate implementation.

Note on video performance:
    conv2d_int8 uses pure Python loops. Frames are resized to --max-dim
    (default 320px) before processing to maintain interactive frame rates.
    Snapshots use the resized resolution — same as what the preview sees.
"""

import argparse
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.join(_THIS_DIR, "..", "..")
sys.path.insert(0, os.path.join(_THIS_DIR, "..", "common"))

from kernels import KERNEL_NAMES  # noqa: E402


def _resolve_default_results() -> str:
    return os.path.abspath(os.path.join(_PROJECT_ROOT, "results"))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="V4 interactive INT8 convolution preview.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 preview.py --image data/cameraman.png\n"
            "  python3 preview.py --video clip.mp4 --kernel sobel_y\n"
            "  python3 preview.py --image data/cameraman.png --kernel laplacian\n"
        )
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--image", type=str, metavar="PATH",
                        help="Path to a grayscale (or color) PNG/JPEG.")
    source.add_argument("--video", type=str, metavar="PATH",
                        help="Path to a video file (MP4, AVI, ...).")

    parser.add_argument(
        "--kernel", type=str, default="sobel_x",
        choices=KERNEL_NAMES,
        help=f"Starting kernel (default: sobel_x). Switch live with 1/2/3."
    )
    parser.add_argument(
        "--max-dim", type=int, default=320, metavar="PX",
        help="Max frame dimension for video preview, pixels (default: 320)."
    )
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Directory for saved snapshots (default: <project-root>/results/)."
    )

    args = parser.parse_args()

    artifact_dir = os.path.abspath(args.output_dir) \
                   if args.output_dir else _resolve_default_results()

    # --- Image mode ---
    if args.image:
        from input_handler import load_image
        from preview_engine import run_image_preview

        print(f"Loading image: {args.image}")
        image = load_image(args.image)
        h, w = image.shape
        print(f"Size: {h}x{w}  |  Kernel: {args.kernel}")
        print("Controls: 1 sobel_x  2 sobel_y  3 laplacian  S save  Q quit")
        run_image_preview(image, args.kernel, artifact_dir)

    # --- Video mode ---
    elif args.video:
        from input_handler import open_video, video_fps
        from preview_engine import run_video_preview

        print(f"Opening video: {args.video}")
        cap = open_video(args.video)
        fps = video_fps(cap)
        print(f"FPS: {fps:.1f}  |  Preview max-dim: {args.max_dim}px  |  Kernel: {args.kernel}")
        print("Controls: 1 sobel_x  2 sobel_y  3 laplacian  S save  Q quit")
        run_video_preview(cap, args.kernel, args.max_dim, artifact_dir)


if __name__ == "__main__":
    main()
