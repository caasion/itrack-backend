"""
Profile routes
--------------
GET  /profile/{user_id}  — fetch a user's taste profile and dwell count
DELETE /profile/{user_id} — reset a user's profile (useful during demos)
"""

from fastapi import APIRouter
from models.schemas import ProfileResponse, TasteProfile
from services import backboard_service

router = APIRouter()


@router.get("/{user_id}", response_model=ProfileResponse)
async def get_profile(user_id: str):
    """Return the user's current taste profile and dwell event count."""
    profile = await backboard_service.get_profile(user_id)
    count = backboard_service.get_dwell_count(user_id)
    return ProfileResponse(user_id=user_id, profile=profile, dwell_event_count=count)


@router.delete("/{user_id}")
async def reset_profile(user_id: str):
    """Clear a user's cached profile (for demo resets)."""
    backboard_service._profile_cache.pop(user_id, None)
    backboard_service._dwell_counts.pop(user_id, None)
    return {"status": "ok", "user_id": user_id, "message": "Profile cache cleared"}
