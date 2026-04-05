"""
POST /api/validate — Run full RTL snapshot validation.

Accepts either:
  - source=<filename>  load from data/<filename> (for built-in media)
  - file upload        grayscale image (for user uploads)

Optional ROI: roi_x, roi_y, roi_w, roi_h query params.

Delegates to the V4 snapshot validation pipeline via core_bridge.
Returns structured metrics + run_id for subsequent artifact retrieval.
"""
import io
import os
from typing import Literal, Optional

import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image as PILImage
from pydantic import BaseModel

import core_bridge  # noqa: F401
from snapshot_exporter import export_snapshot
from rtl_runner import run_rtl_simulation
from validation_reporter import generate_report

router = APIRouter(tags=["validate"])

_BACKEND_DIR     = os.path.dirname(os.path.abspath(__file__))
_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
_PROJECT_ROOT = os.path.abspath(os.path.join(_BACKEND_DIR, "..", ".."))
_DATA_DIR     = os.path.join(_PROJECT_ROOT, "data")
_RESULTS_ROOT = os.path.join(_PROJECT_ROOT, "results")

KernelName = Literal["sobel_x", "sobel_y", "laplacian", "gaussian"]


class ValidationResult(BaseModel):
    run_id: str
    kernel_name: str
    status: str
    total_pixels: int
    matches: int
    mismatches: int
    img_h: int
    img_w: int
    out_h: int
    out_w: int
    saturated_pct: float
    output_min: int
    output_max: int
    output_mean: float
    has_roi: bool
    roi: Optional[list]


def _load_source(source: Optional[str], file: Optional[UploadFile]) -> np.ndarray:
    """Load image from named source (data/) or uploaded file. Raises HTTPException on failure."""
    if source is not None:
        path = os.path.join(_DATA_DIR, os.path.basename(source))
        if not os.path.isfile(path):
            raise HTTPException(status_code=404, detail=f"Source not found: {source}")
        try:
            img = PILImage.open(path).convert("L")
            return np.array(img, dtype=np.uint8)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Cannot decode source: {exc}")

    if file is not None:
        try:
            import asyncio
            data = asyncio.get_event_loop().run_until_complete(file.read()) \
                   if not hasattr(file, '_data') else file._data
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to read uploaded file.")
        try:
            img = PILImage.open(io.BytesIO(data)).convert("L")
            return np.array(img, dtype=np.uint8)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Cannot decode image: {exc}")

    raise HTTPException(status_code=422, detail="Provide either source= or upload a file.")


@router.post("/validate", response_model=ValidationResult)
async def validate(
    file: Optional[UploadFile] = File(default=None),
    source: Optional[str] = Query(default=None),
    kernel: KernelName = Query(default="sobel_x"),
    roi_x: Optional[int] = Query(default=None),
    roi_y: Optional[int] = Query(default=None),
    roi_w: Optional[int] = Query(default=None),
    roi_h: Optional[int] = Query(default=None),
):
    # --- Load image ---
    if source is None and file is None:
        raise HTTPException(status_code=422, detail="Provide either source= or upload a file.")

    if source is not None:
        ext = os.path.splitext(source)[1].lower()
        if ext in _VIDEO_EXTENSIONS:
            raise HTTPException(
                status_code=422,
                detail="Video files are not supported. Please select an image source."
            )
        path = os.path.join(_DATA_DIR, os.path.basename(source))
        if not os.path.isfile(path):
            raise HTTPException(status_code=404, detail=f"Source not found: {source}")
        try:
            img = PILImage.open(path).convert("L")
            frame_uint8 = np.array(img, dtype=np.uint8)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Cannot decode source: {exc}")
    else:
        if file.content_type and file.content_type.startswith("video/"):
            raise HTTPException(
                status_code=422,
                detail="Video upload is not supported. Please upload an image file (PNG, JPEG, etc.)."
            )
        try:
            data = await file.read()
            img = PILImage.open(io.BytesIO(data)).convert("L")
            frame_uint8 = np.array(img, dtype=np.uint8)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Cannot decode image: {exc}")

    if frame_uint8.shape[0] < 3 or frame_uint8.shape[1] < 3:
        raise HTTPException(status_code=400, detail="Image must be at least 3×3 pixels.")

    # --- Build ROI tuple ---
    roi = None
    if all(v is not None for v in [roi_x, roi_y, roi_w, roi_h]):
        roi = (roi_x, roi_y, roi_w, roi_h)

    # --- Run validation pipeline (mirrors validate_snapshot.py exactly) ---
    try:
        run_info = export_snapshot(
            frame_uint8  = frame_uint8,
            kernel_name  = kernel,
            results_root = _RESULTS_ROOT,
            roi          = roi,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Export failed: {exc}")

    rtl_result = run_rtl_simulation(run_info, _PROJECT_ROOT)

    if rtl_result.status == "no_simulator":
        raise HTTPException(status_code=503, detail="iverilog not installed on server.")
    if rtl_result.status == "error":
        raise HTTPException(status_code=500, detail=f"RTL simulation failed: {rtl_result.sim_log}")

    # Use ROI-cropped version for the board (matches validate_snapshot.py behaviour)
    if roi:
        rx, ry, rw, rh = roi
        source_for_board = frame_uint8[ry:ry+rh, rx:rx+rw]
    else:
        source_for_board = frame_uint8

    try:
        metrics = generate_report(
            run_info     = run_info,
            rtl_hex_path = rtl_result.rtl_hex_path,
            sim_log      = rtl_result.sim_log,
            source_uint8 = source_for_board,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")

    return ValidationResult(
        run_id       = metrics["run_id"],
        kernel_name  = metrics["kernel_name"],
        status       = metrics["status"],
        total_pixels = metrics["total_pixels"],
        matches      = metrics["matches"],
        mismatches   = metrics["mismatches"],
        img_h        = metrics["img_h"],
        img_w        = metrics["img_w"],
        out_h        = metrics["out_h"],
        out_w        = metrics["out_w"],
        saturated_pct = metrics["saturated_pct"],
        output_min   = metrics["output_min"],
        output_max   = metrics["output_max"],
        output_mean  = metrics["output_mean"],
        has_roi      = metrics["has_roi"],
        roi          = metrics["roi"],
    )
