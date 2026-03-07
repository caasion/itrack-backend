"""
iTrack Backend — FastAPI Server
Receives dwell events from the browser extension, orchestrates Gemini Vision,
Backboard taste profile, product sourcing, and returns a recommendation card payload.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from routes.dwell import router as dwell_router
from routes.profile import router as profile_router
from routes.health import router as health_router
from config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"iTrack backend starting — sourcing mode: {settings.PRODUCT_SOURCING_MODE}")
    yield
    print("iTrack backend shutting down")


app = FastAPI(
    title="iTrack Backend",
    description="Passive gaze commerce — dwell event processing pipeline",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten for production; extension origin goes here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(dwell_router, prefix="/dwell", tags=["dwell"])
app.include_router(profile_router, prefix="/profile", tags=["profile"])
