"""
VigilGrid — FastAPI backend

Loads and fits the hotspot engine ONCE at startup, not per-request. DBSCAN
over tens of thousands of points is cheap but not free, and re-running it on
every API call would be wasteful and would let a stray edge case flip a
request's results non-deterministically.

Run: uvicorn app:app --reload
"""
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import config
from model import HotspotEngine

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("vigilgrid.app")

engine: Optional[HotspotEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    logger.info("Starting up — loading and fitting hotspot engine")
    engine = HotspotEngine().load().fit()
    yield
    logger.info("Shutting down")


app = FastAPI(title="VigilGrid API", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your actual frontend origin before deploying
    allow_methods=["GET"],
    allow_headers=["*"],
)


class HealthResponse(BaseModel):
    status: str
    points_loaded: int
    hotspots_found: int


def _require_engine() -> HotspotEngine:
    if engine is None or engine.points is None:
        raise HTTPException(status_code=503, detail="Engine not ready")
    return engine


@app.get("/health", response_model=HealthResponse)
def health():
    eng = _require_engine()
    return HealthResponse(
        status="ok",
        points_loaded=len(eng.points),
        hotspots_found=len(eng.hotspots) if eng.hotspots is not None else 0,
    )


@app.get("/vigilgrid/hotspots")
def get_hotspots():
    eng = _require_engine()
    return {"hotspots": eng.get_hotspots()}


@app.get("/vigilgrid/points")
def get_points(limit: int = Query(default=5000, le=40000, description="Cap payload size for map rendering")):
    eng = _require_engine()
    return {"points": eng.get_points(limit=limit)}


@app.get("/vigilgrid/patrol-allocation")
def get_patrol_allocation(n_units: int = Query(default=config.DEFAULT_PATROL_UNITS, ge=1, le=100)):
    eng = _require_engine()
    return {"n_units": n_units, "allocation": eng.allocate_patrols(n_units)}
