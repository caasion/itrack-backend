"""
GET /health
------------
Liveness check with service availability info.
Lets the extension team (or any integrator) verify which services are live vs fallback.
"""

from fastapi import APIRouter
from config.settings import settings

router = APIRouter()


@router.get("/")
async def health_check():
    gemini_available = (
        settings.GEMINI_API_KEY
        and settings.GEMINI_API_KEY != "YOUR_GEMINI_API_KEY"
    )
    backboard_available = (
        settings.BACKBOARD_API_KEY
        and settings.BACKBOARD_API_KEY != "YOUR_BACKBOARD_API_KEY"
    )

    return {
        "status": "ok",
        "sourcing_mode": settings.PRODUCT_SOURCING_MODE,
        "cloudinary_enabled": settings.CLOUDINARY_ENABLED,
        "gemini_available": bool(gemini_available),
        "backboard_available": bool(backboard_available),
    }
