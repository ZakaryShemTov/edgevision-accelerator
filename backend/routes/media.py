"""
GET /api/media — List available media sources from the data/ directory.

Returns a list of {name, type} objects for images and videos that can be
referenced by name in /api/filter?source= and /api/validate?source=.
"""
import os

from fastapi import APIRouter

router = APIRouter(tags=["media"])

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR    = os.path.abspath(os.path.join(_BACKEND_DIR, "..", "..", "data"))

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif"}
_VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


@router.get("/media")
def list_media():
    if not os.path.isdir(_DATA_DIR):
        return []

    items = []
    for fname in sorted(os.listdir(_DATA_DIR)):
        ext = os.path.splitext(fname)[1].lower()
        if ext in _IMAGE_EXTS:
            items.append({"name": fname, "type": "image"})
        elif ext in _VIDEO_EXTS:
            items.append({"name": fname, "type": "video"})

    return items
