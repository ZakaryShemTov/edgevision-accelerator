"""
EdgeVision Studio — FastAPI backend

Thin orchestration layer over the V1–V4 Python core.
Never reimplements core logic — calls it via core_bridge.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import filter as filter_routes
from routes import validate as validate_routes
from routes import runs as runs_routes
from routes import media as media_routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    import core_bridge  # noqa: F401 — triggers path setup + import validation
    yield


app = FastAPI(
    title="EdgeVision Studio API",
    description="REST interface to the EdgeVision hardware/software pipeline",
    version="5.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(filter_routes.router,   prefix="/api")
app.include_router(validate_routes.router, prefix="/api")
app.include_router(runs_routes.router,     prefix="/api")
app.include_router(media_routes.router,    prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "5.0.0"}
