"""
Central config — all secrets and feature flags live here.
Copy .env.example to .env and fill in values before running.
"""

from pydantic_settings import BaseSettings
from typing import Literal


class Settings(BaseSettings):
    # --- API Keys ---
    GEMINI_API_KEY: str = "YOUR_GEMINI_API_KEY"
    GEMINI_MODEL: str = "gemini-flash-latest"
    BACKBOARD_API_KEY: str = "YOUR_BACKBOARD_API_KEY"
    BACKBOARD_BASE_URL: str = "https://api.backboard.io"
    SERPAPI_KEY: str = "YOUR_SERPAPI_KEY"
    CLOUDINARY_CLOUD_NAME: str = "YOUR_CLOUD_NAME"
    CLOUDINARY_API_KEY: str = "YOUR_CLOUDINARY_KEY"
    CLOUDINARY_API_SECRET: str = "YOUR_CLOUDINARY_SECRET"

    # --- Feature Flags ---
    # "serpapi"   → live Google Lens reverse image search
    # "hardcoded" → local catalog in services/catalog.py (reliable demo fallback)
    PRODUCT_SOURCING_MODE: Literal["serpapi", "hardcoded"] = "hardcoded"

    # Set False during dev to skip Cloudinary and return raw image URLs
    CLOUDINARY_ENABLED: bool = False

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
