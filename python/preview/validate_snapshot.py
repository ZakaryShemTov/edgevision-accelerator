"""
EdgeVision Accelerator — V4 Snapshot Validation

Captures a frame or ROI from an image or video file, runs the full
Python → hex → RTL simulation → diff pipeline, and produces a
self-contained validation package.

Usage:
    python3 validate_snapshot.py --image data/cameraman.png --kernel sobel_x
    python3 validate_snapshot.py --image data/cameraman.png --kernel laplacian --roi 50 50 128 128
    python3 validate_snapshot.py --video clip.mp4 --frame 30 --kernel sobel_y

Options:
    --image PATH        Source image file
    --video PATH        Source video file
    --frame N           Frame index to capture (video only, default: 0)
    --kernel NAME       Kernel: sobel_x | sobel_y | laplacian (default: sobel_x)
    --roi X Y W H       Crop region in pixels (applied after loading)
    --max-dim PX        Resize longest dimension to PX before processing
                        (default: none — full resolution)
    --output-dir PATH   Root results directory (default: results/)
    --run-id ID         Override auto-generated run ID

Output (all in results/runs/<run_id>/):
    source.png          Source frame or ROI (uint8, for reference)
    sim/input.hex       INT8 image in V1 hex format
    sim/kernel.hex      3x3 kernel in V1 hex format
    sim/expected.hex    Python golden output in V1 hex format
    sim/meta.json       Run metadata
    sim/rtl_output.hex  RTL simulation output
    diff_map.png        Per-pixel error (grey=match, hot=mismatch)
    board.png           4-panel comparison board (portfolio artifact)
    report.json         Structured metrics
    report.txt          Human-readable summary

Pipeline layers:
    input_handler.py       — load / resize / convert
    snapshot_exporter.py   — frame → hex + meta
    rtl_runner.py          — invoke sim/run_sim.sh, collect output
    validation_reporter.py — diff, board, report
"""

import argparse
import os
import sys

_THIS_DIR     = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_THIS_DIR, "..", ".."))

sys.path.insert(0, os.path.join(_THIS_DIR, "..", "common"))

from kernels import KERNEL_NAMES  # noqa: E402


def _resolve_results() -> str:
    return os.path.join(_PROJECT_ROOT, "results")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capture a frame/ROI, validate against RTL, produce artifacts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python3 validate_snapshot.py --image data/cameraman.png\n"
            "  python3 validate_snapshot.py --image data/cameraman.png --roi 64 64 64 64\n"
            "  python3 validate_snapshot.py --video clip.mp4 --frame 10 --kernel sobel_y\n"
        )
    )

    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--image", type=str, metavar="PATH")
    src.add_argument("--video", type=str, metavar="PATH")

    parser.add_argument("--frame",      type=int, default=0,
                        help="Frame index for video (default: 0).")
    parser.add_argument("--kernel",     type=str, default="sobel_x",
                        choices=KERNEL_NAMES)
    parser.add_argument("--roi",        type=int, nargs=4, metavar=("X","Y","W","H"),
                        default=None,
                        help="Crop region: X Y W H in pixels.")
    parser.add_argument("--max-dim",    type=int, default=None, metavar="PX",
                        help="Resize longest dimension before processing.")
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--run-id",     type=str, default=None)

    args = parser.parse_args()

    results_root = os.path.abspath(args.output_dir) \
                   if args.output_dir else _resolve_results()

    # --- Import pipeline modules ---
    from input_handler import (
        load_image, open_video, read_frame_gray, resize_for_preview
    )
    from snapshot_exporter   import export_snapshot
    from rtl_runner          import run_rtl_simulation
    from validation_reporter import generate_report

    # -----------------------------------------------------------------------
    # Step 1 — Load frame
    # -----------------------------------------------------------------------
    print(f"\n[1/4] Loading source...")
    if args.image:
        frame_uint8 = load_image(args.image)
        print(f"      Image: {args.image}  {frame_uint8.shape[0]}x{frame_uint8.shape[1]}")
    else:
        cap = open_video(args.video)
        cap.set(1, args.frame)  # CAP_PROP_POS_FRAMES
        frame_uint8 = read_frame_gray(cap)
        cap.release()
        if frame_uint8 is None:
            print(f"Error: could not read frame {args.frame} from {args.video}",
                  file=sys.stderr)
            sys.exit(1)
        print(f"      Video: {args.video}  frame {args.frame}"
              f"  {frame_uint8.shape[0]}x{frame_uint8.shape[1]}")

    if args.max_dim is not None:
        frame_uint8 = resize_for_preview(frame_uint8, args.max_dim)
        print(f"      Resized to: {frame_uint8.shape[0]}x{frame_uint8.shape[1]}")

    roi = tuple(args.roi) if args.roi else None
    if roi:
        print(f"      ROI: x={roi[0]} y={roi[1]} w={roi[2]} h={roi[3]}")

    # -----------------------------------------------------------------------
    # Step 2 — Export to hex
    # -----------------------------------------------------------------------
    print(f"\n[2/4] Exporting test vectors...")
    run_info = export_snapshot(
        frame_uint8  = frame_uint8,
        kernel_name  = args.kernel,
        results_root = results_root,
        roi          = roi,
        run_id       = args.run_id,
    )
    print(f"      Run ID:  {run_info['run_id']}")
    print(f"      Run dir: {run_info['run_dir']}")
    print(f"      Image:   {run_info['img_h']}x{run_info['img_w']}"
          f"  →  output {run_info['out_h']}x{run_info['out_w']}")

    # -----------------------------------------------------------------------
    # Step 3 — RTL simulation
    # -----------------------------------------------------------------------
    print(f"\n[3/4] Running RTL simulation...")
    rtl_result = run_rtl_simulation(run_info, _PROJECT_ROOT)

    if rtl_result.status == "no_simulator":
        print(f"      WARNING: {rtl_result.sim_log}")
        print(f"      Skipping RTL validation. Install iverilog to enable.")
        print(f"\nPartial artifacts written to: {run_info['run_dir']}/")
        print("(no RTL output — board and report require simulation)")
        return

    if rtl_result.status == "error":
        print(f"      ERROR during simulation:\n{rtl_result.sim_log}")
        sys.exit(1)

    print(f"      Simulation status: {rtl_result.status.upper()}")

    # -----------------------------------------------------------------------
    # Step 4 — Report and artifacts
    # -----------------------------------------------------------------------
    print(f"\n[4/4] Generating report and artifacts...")
    # Source image passed to reporter for the board's input panel
    # Use ROI-cropped version if applicable
    if roi:
        rx, ry, rw, rh = roi
        source_for_board = frame_uint8[ry:ry+rh, rx:rx+rw]
    else:
        source_for_board = frame_uint8

    metrics = generate_report(
        run_info      = run_info,
        rtl_hex_path  = rtl_result.rtl_hex_path,
        sim_log       = rtl_result.sim_log,
        source_uint8  = source_for_board,
    )

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    status_str = metrics["status"].upper()
    sep = "=" * 52
    print(f"\n{sep}")
    print(f"  RESULT: {status_str}")
    print(f"  {metrics['matches']}/{metrics['total_pixels']} pixels match"
          f"  |  {metrics['mismatches']} mismatches")
    print(f"  Kernel: {args.kernel}"
          f"  |  Saturated: {metrics['saturated_pct']}%")
    print(sep)
    print(f"\nArtifacts written to: {run_info['run_dir']}/")
    for fname in ["source.png", "diff_map.png", "board.png",
                  "report.json", "report.txt"]:
        path = os.path.join(run_info["run_dir"], fname)
        if os.path.isfile(path):
            size = os.path.getsize(path)
            print(f"  {fname:<22}  {size:>8} bytes")


if __name__ == "__main__":
    main()
