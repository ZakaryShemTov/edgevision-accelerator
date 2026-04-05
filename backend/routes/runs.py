"""
GET /api/runs         — List past validation runs.
GET /api/runs/{id}    — Fetch metrics for a specific run.
GET /api/runs/{id}/artifacts/{filename} — Serve a run artifact (PNG/JSON/TXT).

Runs are stored as files by the V4 validation pipeline in
results/runs/<run_id>/  — no database required.
"""
import json
import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter(tags=["runs"])

_PROJECT_ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
_RUNS_DIR = os.path.join(_PROJECT_ROOT, "results", "runs")

_ARTIFACTS = {"board.png", "diff_map.png", "report.json", "report.txt"}


def _run_ids() -> list[str]:
    if not os.path.isdir(_RUNS_DIR):
        return []
    return sorted(
        [d for d in os.listdir(_RUNS_DIR) if os.path.isdir(os.path.join(_RUNS_DIR, d))],
        reverse=True,
    )


@router.get("/runs")
def list_runs():
    runs = []
    for run_id in _run_ids():
        report_path = os.path.join(_RUNS_DIR, run_id, "report.json")
        if os.path.isfile(report_path):
            with open(report_path) as f:
                runs.append(json.load(f))
    return runs


@router.get("/runs/{run_id}")
def get_run(run_id: str):
    report_path = os.path.join(_RUNS_DIR, run_id, "report.json")
    if not os.path.isfile(report_path):
        raise HTTPException(status_code=404, detail=f"Run not found: {run_id}")
    with open(report_path) as f:
        return json.load(f)


@router.get("/runs/{run_id}/artifacts/{filename}")
def get_artifact(run_id: str, filename: str):
    if filename not in _ARTIFACTS:
        raise HTTPException(status_code=400, detail=f"Unknown artifact: {filename}")
    path = os.path.join(_RUNS_DIR, run_id, filename)
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail=f"Artifact not found: {filename}")
    return FileResponse(path)
