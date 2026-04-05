"""
POST /api/filter — Apply a named INT8 kernel to a grayscale image.

Accepts either:
  - source=<filename>  load from data/<filename> (for built-in media)
  - file upload        grayscale image (for user uploads)

Returns filtered output as base64-encoded PNG alongside statistics.
Computation delegates entirely to the V1 Python core via core_bridge.
"""
import base64
import io
import os
from typing import Literal, Optional

import numpy as np
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from PIL import Image as PILImage
from pydantic import BaseModel

import core_bridge  # noqa: F401
from conv_reference import conv2d_int8
from conversions import uint8_to_int8, int8_to_uint8_display
from kernels import KERNELS

router = APIRouter(tags=["filter"])

_BACKEND_DIR     = os.path.dirname(os.path.abspath(__file__))
_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
_DATA_DIR    = os.path.abspath(os.path.join(_BACKEND_DIR, "..", "..", "data"))

KernelName = Literal["sobel_x", "sobel_y", "laplacian", "gaussian"]


class FilterResult(BaseModel):
    kernel: str
    input_h: int
    input_w: int
    output_h: int
    output_w: int
    output_min: int
    output_max: int
    output_mean: float
    saturated_pixels: int
    saturated_pct: float
    input_png_b64: str   # cropped to output size, display-ready
    output_png_b64: str


def _to_b64_png(arr_uint8: np.ndarray) -> str:
    buf = io.BytesIO()
    PILImage.fromarray(arr_uint8, mode="L").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@router.post("/filter", response_model=FilterResult)
async def apply_filter(
    file: Optional[UploadFile] = File(default=None),
    source: Optional[str] = Query(default=None),
    kernel: KernelName = Query(default="sobel_x"),
):
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
            img_uint8 = np.array(img, dtype=np.uint8)
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
            img_uint8 = np.array(img, dtype=np.uint8)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=f"Cannot decode image: {exc}")

    H, W = img_uint8.shape
    if H < 3 or W < 3:
        raise HTTPException(status_code=400, detail="Image must be at least 3×3 pixels.")

    img_int8 = uint8_to_int8(img_uint8)
    out_int8 = conv2d_int8(img_int8, KERNELS[kernel])

    out_H, out_W = out_int8.shape
    total = out_H * out_W
    sat   = int(np.sum((out_int8 == 127) | (out_int8 == -128)))

    return FilterResult(
        kernel          = kernel,
        input_h         = H, input_w  = W,
        output_h        = out_H, output_w = out_W,
        output_min      = int(out_int8.min()),
        output_max      = int(out_int8.max()),
        output_mean     = round(float(out_int8.astype(np.float32).mean()), 3),
        saturated_pixels = sat,
        saturated_pct   = round(100 * sat / total, 1),
        input_png_b64   = _to_b64_png(img_uint8[1:H-1, 1:W-1]),
        output_png_b64  = _to_b64_png(int8_to_uint8_display(out_int8)),
    )
