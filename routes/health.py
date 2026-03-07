"""
GET /health
------------
Simple liveness check so the extension (or infra) can verify the backend is up.
"""

from fastapi import APIRouter
from config.settings import settings

router = APIRouter()


@router.get("/")
async def health_check():
    return {
        "status": "ok",
        "sourcing_mode": settings.PRODUCT_SOURCING_MODE,
        "cloudinary_enabled": settings.CLOUDINARY_ENABLED,
    }
