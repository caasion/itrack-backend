"""
POST /dwell
-----------
The core pipeline endpoint. Called by the browser extension on every confirmed gaze dwell.

Pipeline:
  1. Receive DwellEvent (screenshot + user_id + page context)
  2. Gemini Call 1: identify product + extract taste signals
  3. Backboard: update taste profile with new signals
  4. Product sourcing: find candidates (SerpApi or hardcoded)
  5. Gemini Call 2: select best match given updated profile
  6. Cloudinary: transform product image
  7. Return RecommendationCard to extension
"""

from fastapi import APIRouter, HTTPException
from models.schemas import DwellEvent, RecommendationCard
from services import gemini_service, backboard_service, sourcing_service, cloudinary_service

router = APIRouter()


@router.post("/", response_model=RecommendationCard)
async def handle_dwell(event: DwellEvent):
    """
    Full pipeline: dwell event in → recommendation card out.
    """
    print(f"\n[Dwell] user={event.user_id} dwell={event.dwell_duration_ms}ms url={event.page_url}")

    # ── Step 1: Gemini Vision — identify product ───────────────────────────
    print("[Pipeline] Step 1: Gemini product identification")
    try:
        identified = await gemini_service.identify_product(
            screenshot_b64=event.screenshot_b64,
            page_url=event.page_url,
            page_title=event.page_title or "",
        )
        print(f"[Pipeline] Identified: {identified.get('product_name')} ({identified.get('product_category')})")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini identification failed: {e}")

    # ── Step 2: Backboard — update taste profile ───────────────────────────
    print("[Pipeline] Step 2: Backboard profile update")
    try:
        updated_profile = await backboard_service.update_profile(
            user_id=event.user_id,
            signals=identified,
        )
        print(f"[Pipeline] Profile updated. Dwell count: {backboard_service.get_dwell_count(event.user_id)}")
    except Exception as e:
        # Non-fatal — use empty profile and continue
        print(f"[Pipeline] Backboard update failed: {e} — using empty profile")
        updated_profile = await backboard_service.get_profile(event.user_id)

    # ── Step 3: Product sourcing ───────────────────────────────────────────
    print("[Pipeline] Step 3: Product sourcing")
    try:
        candidates = await sourcing_service.source_products(
            screenshot_b64=event.screenshot_b64,
            signals=identified,
        )
        print(f"[Pipeline] {len(candidates)} candidates found via {candidates[0].source if candidates else 'none'}")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Product sourcing failed: {e}")

    if not candidates:
        raise HTTPException(status_code=404, detail="No product candidates found")

    # ── Step 4: Gemini — select best match ────────────────────────────────
    print("[Pipeline] Step 4: Gemini match selection")
    try:
        best_product, match_reason = await gemini_service.select_best_match(
            profile=updated_profile,
            identified_product=identified,
            candidates=candidates,
        )
        print(f"[Pipeline] Best match: {best_product.name} — {match_reason}")
    except Exception as e:
        # Fallback: just take first candidate
        print(f"[Pipeline] Gemini selection failed: {e} — using first candidate")
        best_product = candidates[0]
        match_reason = "Matched to your recent interests."

    # ── Step 5: Cloudinary image transform ────────────────────────────────
    print("[Pipeline] Step 5: Cloudinary transform")
    transformed_image_url = await cloudinary_service.transform_product_image(
        best_product.image_url
    )
    best_product.image_url = transformed_image_url

    # ── Step 6: Return card ────────────────────────────────────────────────
    card = RecommendationCard(
        user_id=event.user_id,
        product=best_product,
        match_reason=match_reason,
        profile_snapshot=updated_profile,
        sourcing_mode=best_product.source,
    )

    print(f"[Pipeline] Card ready: {card.product.name} @ {card.product.price}")
    return card
