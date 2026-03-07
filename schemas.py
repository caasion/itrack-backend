"""
Shared Pydantic models for request/response shapes.
The extension sends DwellEvent; the backend responds with RecommendationCard.
"""

from pydantic import BaseModel
from typing import Optional


# ── Inbound (Extension → Backend) ─────────────────────────────────────────────

class DwellEvent(BaseModel):
    user_id: str                        # Stable anonymous ID set by extension
    screenshot_b64: str                 # Base64-encoded JPEG/PNG of viewport crop
    page_url: str                       # Current tab URL (context for Gemini)
    page_title: Optional[str] = None    # <title> tag if available
    dwell_duration_ms: int              # How long gaze lingered (should be 2000+)


# ── Taste Profile (Backboard shape) ──────────────────────────────────────────

class TasteProfile(BaseModel):
    preferred_styles: list[str] = []
    preferred_colors: list[str] = []
    price_range: str = "unknown"
    preferred_brands: list[str] = []
    recent_interests: list[str] = []


# ── Outbound (Backend → Extension) ────────────────────────────────────────────

class ProductCandidate(BaseModel):
    name: str
    price: str
    image_url: str                      # Raw or Cloudinary-transformed URL
    buy_url: str
    source: str                         # "serpapi" | "hardcoded"


class RecommendationCard(BaseModel):
    user_id: str
    product: ProductCandidate
    match_reason: str                   # One-line explanation from Gemini
    profile_snapshot: TasteProfile      # What the profile looked like when match was made
    sourcing_mode: str                  # Which path was used — useful for debugging


# ── Profile API ───────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    user_id: str
    profile: TasteProfile
    dwell_event_count: int
