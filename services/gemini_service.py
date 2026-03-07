"""
Gemini Vision Service
---------------------
Called once per dwell event (fire-and-forget, never blocks cards):

  identify_and_update_profile() — Identify product, extract taste signals,
                                   write to Backboard asynchronously.

The profile update feeds the *next* dwell's Cat 2 pipeline, not the current one.
"""

import asyncio
import json
import google.generativeai as genai
from config.settings import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel(settings.GEMINI_MODEL)


# ── Product Identification + Taste Signal Extraction ─────────────────────────

IDENTIFY_PROMPT = """
You are analyzing a screenshot from a social media feed (Instagram or TikTok).

Identify the primary product visible and extract taste signals.
Respond ONLY with valid JSON — no markdown, no explanation.

{{
  "product_name": "short descriptive name",
  "product_category": "e.g. sneakers, hoodie, water bottle",
  "style_signals": ["list", "of", "style", "descriptors"],
  "color_signals": ["list", "of", "colors"],
  "estimated_price_range": "$XX-$XX or 'unknown'",
  "brand_guess": "brand name or 'unknown'",
  "search_query": "best search query to find this product to buy online"
}}

Page URL for context: {page_url}
Page title: {page_title}
"""


async def identify_and_update_profile(
    screenshot_b64: str,
    page_url: str,
    page_title: str,
    user_id: str,
) -> dict:
    """
    Sends viewport screenshot to Gemini Vision, extracts signals,
    and writes them to Backboard. Fire-and-forget — the pipeline
    does not wait on this to return cards.

    Returns the extracted signals dict (for logging only).
    """
    from services import backboard_service

    prompt = IDENTIFY_PROMPT.format(page_url=page_url, page_title=page_title or "unknown")

    try:
        response = await asyncio.to_thread(
            model.generate_content,
            [
                {"mime_type": "image/jpeg", "data": screenshot_b64},
                prompt,
            ],
            request_options={"timeout": 30},
        )

        raw = response.text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        signals = json.loads(raw.strip())

    except Exception as e:
        print(f"[Gemini] identify_and_update_profile failed: {e}")
        signals = {
            "product_name": "unknown",
            "product_category": "unknown",
            "style_signals": [],
            "color_signals": [],
            "estimated_price_range": "unknown",
            "brand_guess": "unknown",
            "search_query": "",
        }

    # Write signals to Backboard (non-fatal if it fails)
    try:
        await backboard_service.update_profile(user_id, signals)
    except Exception as e:
        print(f"[Gemini] Backboard write failed: {e}")

    return signals
