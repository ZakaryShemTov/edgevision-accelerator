# EdgeVision Studio — V5 Architecture

## Overview

V5 adds a **product layer** on top of the validated V1–V4 core.
No core computation changes. The hardware/software contract in `docs/fixed_point.md` remains
the source of truth. The RTL is not modified.

---

## Layer model

```
┌────────────────────────────────────────────────────────────────────┐
│  studio/              React + TypeScript + Tailwind CSS            │
│  EdgeVision Studio — interactive visual interface                  │
│  Communicates only via HTTP/JSON with the backend                  │
└──────────────────────────┬─────────────────────────────────────────┘
                           │  REST API  (JSON + base64 PNGs)
┌──────────────────────────▼─────────────────────────────────────────┐
│  backend/             FastAPI service                              │
│  Orchestrates core Python, manages run lifecycle                   │
│  Never reimplements core logic — calls it directly                 │
└──────────────────────────┬─────────────────────────────────────────┘
                           │  Python imports via core_bridge.py
┌──────────────────────────▼─────────────────────────────────────────┐
│  python/              Core (unchanged from V1–V4)                  │
│  golden/ · codegen/ · visualize/ · verify/ · preview/             │
│  common/  (kernels, hex_io, conversions)                           │
└──────────────────────────┬─────────────────────────────────────────┘
                           │  hex files + meta.json
┌──────────────────────────▼─────────────────────────────────────────┐
│  rtl/ + sim/          RTL simulation (locked)                      │
│  Icarus Verilog — run via sim/run_sim.sh                           │
└────────────────────────────────────────────────────────────────────┘
```

---

## Layer boundaries

| Boundary | Rule |
|---|---|
| Studio → Backend | HTTP only. No Python calls from the frontend. |
| Backend → Core | Python imports via `backend/core_bridge.py`. Never reimplemented. |
| Backend → RTL | Shell exec via `sim/run_sim.sh`, same as V4. |
| Core → RTL | Hex file interface. Unchanged from V1. |

---

## REST API surface

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/filter` | Apply kernel to image (software preview). Returns base64 PNGs + stats. |
| `POST` | `/api/validate` | Full RTL snapshot validation. Returns run ID + metrics. |
| `GET` | `/api/runs` | List all past validation runs (newest first). |
| `GET` | `/api/runs/{id}` | Fetch a single run's report. |
| `GET` | `/api/runs/{id}/artifacts/{file}` | Serve run artifact (board.png, diff_map.png, report.*). |
| `GET` | `/api/media` | List available source images from `data/`. |

Both `POST /api/filter` and `POST /api/validate` accept either:
- `source=<filename>` query param (loads from `data/`)
- `file` multipart upload (user-provided image)

Optional ROI: `roi_x`, `roi_y`, `roi_w`, `roi_h` query params on `/api/validate`.

---

## What V5 adds

| Component | Description |
|---|---|
| **Visual Workspace** | Dominant image canvas — split / board / single-panel display modes |
| **Control Panel** | Source picker, kernel selector, ROI draw tool, action buttons |
| **Validation Panel** | Live run metrics: status, pixel count, mismatches, saturation, range |
| **Run Gallery** | Browsable history of past RTL validation runs with thumbnails |
| **Board Viewer** | Full-screen overlay for the 4-panel comparison board (with keyboard nav) |
| **Presentation Mode** | Collapses sidebars to full-canvas view |

---

## Running V5

```bash
# Backend (from project root)
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Frontend (from project root, separate terminal)
cd studio
npm install
npm run dev        # → http://localhost:5173
```

---

## Out of scope for V5

- RTL changes (validated and locked)
- New kernels, multi-channel, AXI-Stream, FPGA synthesis
- Authentication, persistent database, multi-user support
