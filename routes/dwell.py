"""
POST /dwell
-----------
V3 two-pipeline endpoint. Called by the browser extension on every confirmed gaze dwell.

Three concurrent tasks:
  Cat 1: Screenshot → SerpApi Lens → top visual match → "You looked at"
  Cat 2: Read profile → compose query → SerpApi Shopping → "Based on your taste"
  Gemini: Identify product → extract signals → write to Backboard (fire-and-forget)

Cat 1 and Cat 2 return immediately. Gemini updates the profile for the *next* dwell.
"""

import asyncio
from fastapi import APIRouter
from models.schemas import DwellEvent, DwellResponse, Cat1Product, ProductCandidate
from services import gemini_service, backboard_service, sourcing_service, cloudinary_service
from config.settings import settings

router = APIRouter()


async def run_cat1(screenshot_b64: str) -> Cat1Product:
    """
    Cat 1 pipeline: find the exact product the user is looking at.
    SerpApi Lens (live) or first hardcoded catalog item (fallback).
    """
    if settings.PRODUCT_SOURCING_MODE == "serpapi":
        try:
            product = await sourcing_service.source_cat1_serpapi(screenshot_b64)
            product.image_url = await cloudinary_service.transform_product_image(product.image_url)
            return product
        except Exception as e:
            print(f"[Cat1] SerpApi Lens failed: {e} — using hardcoded fallback")

    return await sourcing_service.source_cat1_hardcoded()


async def run_cat2(user_id: str) -> list[ProductCandidate]:
    """
    Cat 2 pipeline: find products matching the user's accumulated taste profile.
    SerpApi Shopping (live) or profile-scored hardcoded catalog (fallback).
    """
    profile = await backboard_service.get_profile(user_id)

    if settings.PRODUCT_SOURCING_MODE == "serpapi":
        candidates = await sourcing_service.source_cat2_serpapi(profile)
    else:
        candidates = await sourcing_service.source_cat2_hardcoded(profile)

    # Cloudinary transform each candidate image
    if settings.CLOUDINARY_ENABLED:
        for c in candidates:
            try:
                c.image_url = await cloudinary_service.transform_product_image(c.image_url)
            except Exception:
                pass  # Keep raw URL on failure

    return candidates


@router.post("/", response_model=DwellResponse)
async def handle_dwell(event: DwellEvent):
    """
    V3 dwell handler — fires Cat 1, Cat 2, and Gemini concurrently.
    Returns DwellResponse with current_product + taste_picks.
    """
    print(f"\n[Dwell] user={event.user_id} dwell={event.dwell_duration_ms}ms url={event.page_url}")

    # Fire all three tasks concurrently
    cat1_task = asyncio.create_task(run_cat1(event.screenshot_b64))
    cat2_task = asyncio.create_task(run_cat2(event.user_id))
    gemini_task = asyncio.create_task(
        gemini_service.identify_and_update_profile(
            screenshot_b64=event.screenshot_b64,
            page_url=event.page_url,
            page_title=event.page_title or "",
            user_id=event.user_id,
        )
    )

    # Gather all — return_exceptions=True so one failure doesn't kill the others
    results = await asyncio.gather(cat1_task, cat2_task, gemini_task, return_exceptions=True)
    current_product, taste_picks, gemini_signals = results

    # Handle exceptions gracefully
    if isinstance(current_product, Exception):
        print(f"[Pipeline] Cat 1 failed: {current_product}")
        current_product = None

    if isinstance(taste_picks, Exception):
        print(f"[Pipeline] Cat 2 failed: {taste_picks}")
        taste_picks = []

    if isinstance(gemini_signals, Exception):
        print(f"[Pipeline] Gemini failed (non-blocking): {gemini_signals}")

    # Read latest profile + dwell count
    profile = await backboard_service.get_profile(event.user_id)
    dwell_count = backboard_service.get_dwell_count(event.user_id)

    response = DwellResponse(
        user_id=event.user_id,
        current_product=current_product,
        taste_picks=taste_picks,
        profile_snapshot=profile,
        dwell_count=dwell_count,
        sourcing_mode=settings.PRODUCT_SOURCING_MODE,
    )

    print(f"[Pipeline] Done — cat1={'yes' if current_product else 'no'}, cat2={len(taste_picks)} picks, dwells={dwell_count}")
    return response
