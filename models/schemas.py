"""
Shared Pydantic models for request/response shapes.
The extension sends DwellEvent; the backend responds with DwellResponse.
"""

from pydantic import BaseModel
from typing import Optional, Literal


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


# ── Product Models (Backend → Extension) ─────────────────────────────────────

class ProductCandidate(BaseModel):
    """A product sourced via SerpApi or the hardcoded catalog."""
    name: str
    price: str
    image_url: str                      # Raw or Cloudinary-transformed URL
    buy_url: str
    source: str                         # "serpapi" | "hardcoded"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Nike Air Force 1 '07",
                    "price": "$110",
                    "image_url": "https://static.nike.com/a/images/af1.png",
                    "buy_url": "https://www.nike.com/t/air-force-1-07-shoes",
                    "source": "hardcoded",
                }
            ]
        }
    }


class Cat1Product(BaseModel):
    """Category 1: exact visual match for what the user just looked at."""
    name: str
    price: str
    image_url: str
    buy_url: str
    source: str                         # "serpapi" | "hardcoded"
    match_type: Literal["visual_match"] = "visual_match"

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "Nike Air Force 1 '07",
                    "price": "$110",
                    "image_url": "https://static.nike.com/a/images/af1.png",
                    "buy_url": "https://www.nike.com/t/air-force-1-07-shoes",
                    "source": "serpapi",
                    "match_type": "visual_match",
                }
            ]
        }
    }


# ── Response (Backend → Extension) ───────────────────────────────────────────

class DwellResponse(BaseModel):
    """
    V3 response shape returned on every dwell event.

    Two parallel pipelines:
      - current_product (Cat 1): exact visual match via SerpApi Lens — "You looked at"
      - taste_picks (Cat 2): profile-driven recs via SerpApi Shopping — "Based on your taste"

    current_product is null when Cat 1 fails or no visual match found.
    taste_picks is always an array (empty [] for new users, never null).
    """
    user_id: str
    current_product: Optional[Cat1Product] = None
    taste_picks: list[ProductCandidate] = []
    profile_snapshot: TasteProfile
    dwell_count: int
    sourcing_mode: str

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "user_id": "anon-abc123",
                    "current_product": {
                        "name": "Nike Air Force 1 '07",
                        "price": "$110",
                        "image_url": "https://static.nike.com/a/images/af1.png",
                        "buy_url": "https://www.nike.com/t/air-force-1-07-shoes",
                        "source": "serpapi",
                        "match_type": "visual_match",
                    },
                    "taste_picks": [
                        {
                            "name": "Adidas Samba OG",
                            "price": "$100",
                            "image_url": "https://assets.adidas.com/samba.jpg",
                            "buy_url": "https://www.adidas.com/us/samba-og-shoes",
                            "source": "serpapi",
                        },
                        {
                            "name": "New Balance 990v5",
                            "price": "$185",
                            "image_url": "https://nb.scene7.com/990v5.jpg",
                            "buy_url": "https://www.newbalance.com/pd/made-in-usa-990v5",
                            "source": "serpapi",
                        },
                    ],
                    "profile_snapshot": {
                        "preferred_styles": ["minimalist", "streetwear"],
                        "preferred_colors": ["black", "white"],
                        "price_range": "$50-$200",
                        "preferred_brands": ["Nike", "Adidas"],
                        "recent_interests": ["sneakers"],
                    },
                    "dwell_count": 3,
                    "sourcing_mode": "serpapi",
                }
            ]
        }
    }


# ── Profile API ───────────────────────────────────────────────────────────────

class ProfileResponse(BaseModel):
    user_id: str
    profile: TasteProfile
    dwell_event_count: int
