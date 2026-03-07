"""
Backboard Service
-----------------
Reads and writes the per-user taste profile.

NOTE: The official Backboard SDK (pip install backboard-sdk) exposes
  client.add(user_id, content) / client.add_message(..., memory="Auto")
for memory storage. The REST endpoints below are a best-effort guess;
if they return errors the service falls back gracefully to an in-memory
cache so the pipeline keeps working without remote persistence.
"""

import httpx
from models.schemas import TasteProfile
from config.settings import settings

# In-memory cache to avoid redundant reads within a session
_profile_cache: dict[str, TasteProfile] = {}
_dwell_counts: dict[str, int] = {}


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {settings.BACKBOARD_API_KEY}",
        "Content-Type": "application/json",
    }


def _profile_key(user_id: str) -> str:
    return f"itrack:profile:{user_id}"


# ── Read ──────────────────────────────────────────────────────────────────────

async def get_profile(user_id: str) -> TasteProfile:
    """
    Fetches the user's taste profile from Backboard.
    Falls back to empty profile if not found (first-time user).
    Uses in-memory cache for speed within a session.
    """
    if user_id in _profile_cache:
        return _profile_cache[user_id]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.BACKBOARD_BASE_URL}/memory/{_profile_key(user_id)}",
                headers=_headers(),
                timeout=5.0,
            )
            if resp.status_code == 200:
                data = resp.json()
                profile = TasteProfile(**data.get("value", {}))
                _profile_cache[user_id] = profile
                return profile
    except Exception as e:
        print(f"[Backboard] get_profile failed for {user_id}: {e}")

    # First-time user — return empty profile
    empty = TasteProfile()
    _profile_cache[user_id] = empty
    return empty


# ── Write ─────────────────────────────────────────────────────────────────────

async def update_profile(user_id: str, signals: dict) -> TasteProfile:
    """
    Merges new taste signals (from Gemini extraction) into the existing profile,
    then writes back to Backboard.

    Signals dict shape (from gemini_service.identify_product):
      {
        "style_signals": [...],
        "color_signals": [...],
        "estimated_price_range": "...",
        "brand_guess": "...",
        "product_category": "..."
      }
    """
    profile = await get_profile(user_id)

    # Merge — keep recent 10 unique values per list
    def merge_list(existing: list, new_items: list, limit: int = 10) -> list:
        combined = new_items + existing
        seen = []
        for item in combined:
            if item and item.lower() != "unknown" and item not in seen:
                seen.append(item)
        return seen[:limit]

    profile.preferred_styles = merge_list(profile.preferred_styles, signals.get("style_signals", []))
    profile.preferred_colors = merge_list(profile.preferred_colors, signals.get("color_signals", []))

    brand = signals.get("brand_guess", "")
    if brand and brand.lower() != "unknown" and brand not in profile.preferred_brands:
        profile.preferred_brands = ([brand] + profile.preferred_brands)[:10]

    price = signals.get("estimated_price_range", "")
    if price and price.lower() != "unknown":
        profile.price_range = price

    category = signals.get("product_category", "")
    if category:
        profile.recent_interests = merge_list(profile.recent_interests, [category], limit=5)

    # Write back to Backboard
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                f"{settings.BACKBOARD_BASE_URL}/memory/{_profile_key(user_id)}",
                headers=_headers(),
                json=profile.model_dump(),
                timeout=5.0,
            )
    except Exception as e:
        print(f"[Backboard] update_profile failed for {user_id}: {e}")
        # Non-fatal — profile is updated in memory even if write fails

    # Update cache
    _profile_cache[user_id] = profile
    _dwell_counts[user_id] = _dwell_counts.get(user_id, 0) + 1

    return profile


def get_dwell_count(user_id: str) -> int:
    return _dwell_counts.get(user_id, 0)
