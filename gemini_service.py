"""
Gemini Vision Service
---------------------
Called twice per dwell event:

  1. identify_product()   — What is this product? Extract taste signals.
  2. select_best_match()  — Given the taste profile, which sourced product fits best?
"""

import json
import google.generativeai as genai
from config.settings import settings
from models.schemas import TasteProfile, ProductCandidate

genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # Flash: fast + cheap for demo


# ── Call 1: Product Identification + Taste Signal Extraction ──────────────────

IDENTIFY_PROMPT = """
You are analyzing a screenshot from a social media feed (Instagram or TikTok).

Identify the primary product visible and extract taste signals.
Respond ONLY with valid JSON — no markdown, no explanation.

{
  "product_name": "short descriptive name",
  "product_category": "e.g. sneakers, hoodie, water bottle",
  "style_signals": ["list", "of", "style", "descriptors"],
  "color_signals": ["list", "of", "colors"],
  "estimated_price_range": "$XX-$XX or 'unknown'",
  "brand_guess": "brand name or 'unknown'",
  "search_query": "best search query to find this product to buy online"
}

Page URL for context: {page_url}
Page title: {page_title}
"""

async def identify_product(screenshot_b64: str, page_url: str, page_title: str) -> dict:
    """
    Sends viewport screenshot to Gemini Vision.
    Returns parsed dict with product info and taste signals.
    """
    import base64

    prompt = IDENTIFY_PROMPT.format(page_url=page_url, page_title=page_title or "unknown")

    response = model.generate_content([
        {"mime_type": "image/jpeg", "data": screenshot_b64},
        prompt,
    ])

    raw = response.text.strip()
    # Strip markdown fences if Gemini wraps in ```json
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# ── Call 2: Personalized Match Selection ──────────────────────────────────────

MATCH_PROMPT = """
You are a personal shopping assistant with deep knowledge of the user's taste.

User taste profile:
{profile_json}

The user just looked at: {product_name} ({product_category})

Here are available products to recommend:
{candidates_json}

Pick the single best match for this user. Consider their preferred styles, colors,
brands, and price range. Respond ONLY with valid JSON — no markdown, no explanation.

{
  "best_match_index": 0,
  "match_reason": "one concise sentence explaining why this fits their taste"
}
"""

async def select_best_match(
    profile: TasteProfile,
    identified_product: dict,
    candidates: list[ProductCandidate],
) -> tuple[ProductCandidate, str]:
    """
    Given the user's taste profile and a list of product candidates,
    asks Gemini to pick the best match and explain why.
    Returns (best_product, match_reason).
    """
    if not candidates:
        raise ValueError("No candidates to select from")

    if len(candidates) == 1:
        return candidates[0], "Best available match for your style."

    candidates_json = json.dumps([
        {"index": i, "name": c.name, "price": c.price, "buy_url": c.buy_url}
        for i, c in enumerate(candidates)
    ])

    prompt = MATCH_PROMPT.format(
        profile_json=profile.model_dump_json(indent=2),
        product_name=identified_product.get("product_name", "unknown"),
        product_category=identified_product.get("product_category", "unknown"),
        candidates_json=candidates_json,
    )

    response = model.generate_content(prompt)
    raw = response.text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())
    idx = int(result.get("best_match_index", 0))
    reason = result.get("match_reason", "Matched to your taste profile.")

    # Clamp index to valid range
    idx = max(0, min(idx, len(candidates) - 1))
    return candidates[idx], reason
