"""
Product Sourcing Service
------------------------
Two paths, toggled by settings.PRODUCT_SOURCING_MODE:

  "serpapi"   → Google Lens reverse image search via SerpApi
  "hardcoded" → Local catalog in HARDCODED_CATALOG below

Both return List[ProductCandidate]. Gemini then selects the best match.
"""

import httpx
from models.schemas import ProductCandidate
from config.settings import settings


# ── Hardcoded Catalog (Fallback) ──────────────────────────────────────────────
# Add/swap products here. Keep 15-20 for variety across demo sessions.
# Use real product images and URLs for a convincing demo.

HARDCODED_CATALOG: list[dict] = [
    {
        "name": "Nike Air Force 1 '07",
        "price": "$110",
        "image_url": "https://static.nike.com/a/images/t_PDP_1280_v1/f_auto/af20ff4c-7aa2-4d68-b16e-a28a6c96aba8/air-force-1-07-shoes-WrLlWX.png",
        "buy_url": "https://www.nike.com/t/air-force-1-07-shoes",
        "tags": ["sneakers", "minimalist", "white", "streetwear", "nike"],
    },
    {
        "name": "Aritzia TNA Super Puff Jacket",
        "price": "$325",
        "image_url": "https://images.aritzia.com/media/catalog/product/cache/7/image/480x/9df78eab33525d08d6e5fb8d27136e95/a/r/ar_00000000000000000003388_s_a.jpg",
        "buy_url": "https://www.aritzia.com/en/product/super-puff-jacket",
        "tags": ["jacket", "minimalist", "black", "aritzia", "outerwear"],
    },
    {
        "name": "Carhartt WIP Chase Hoodie",
        "price": "$120",
        "image_url": "https://images.carhartt-wip.com/media/catalog/product/i/0/i026384_0c_01_fv.jpg",
        "buy_url": "https://www.carhartt-wip.com/en/sweatshirts/chase-hoodie",
        "tags": ["hoodie", "streetwear", "earth tones", "oversized", "carhartt"],
    },
    {
        "name": "Hydro Flask 32 oz Wide Mouth",
        "price": "$55",
        "image_url": "https://www.hydroflask.com/media/catalog/product/w/h/wh32bts001_a_1200x1200.jpg",
        "buy_url": "https://www.hydroflask.com/32-oz-wide-mouth",
        "tags": ["water bottle", "accessories", "black", "minimalist"],
    },
    {
        "name": "New Balance 990v5",
        "price": "$185",
        "image_url": "https://nb.scene7.com/is/image/NB/m990gl5_nb_02_i?$pdpflexf2$&qlt=80&fmt=webp&wid=440&hei=440",
        "buy_url": "https://www.newbalance.com/pd/made-in-usa-990v5",
        "tags": ["sneakers", "grey", "minimalist", "new balance", "dad shoes"],
    },
    {
        "name": "Lululemon Everywhere Belt Bag",
        "price": "$38",
        "image_url": "https://images.lululemon.com/is/image/lululemon/LU9AFBS_0001_1",
        "buy_url": "https://shop.lululemon.com/p/bags/Everywhere-Belt-Bag",
        "tags": ["bag", "accessories", "black", "minimalist", "lululemon"],
    },
    {
        "name": "Arc'teryx Atom LT Hoody",
        "price": "$260",
        "image_url": "https://arcteryx.com/media/catalog/product/A/r/Atom-LT-Hoody-Mens-Black-24.jpg",
        "buy_url": "https://arcteryx.com/us/en/shop/mens/atom-lt-hoody",
        "tags": ["jacket", "minimalist", "black", "technical", "arcteryx"],
    },
    {
        "name": "Uniqlo Ultra Light Down Jacket",
        "price": "$70",
        "image_url": "https://image.uniqlo.com/UQ/ST3/us/imagesgoods/467870/item/usgoods_09_467870.jpg",
        "buy_url": "https://www.uniqlo.com/us/en/products/E467870-000",
        "tags": ["jacket", "minimalist", "packable", "affordable", "uniqlo"],
    },
    {
        "name": "Adidas Samba OG",
        "price": "$100",
        "image_url": "https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/7ed0855435194229a525aad6009a0497_9366/Samba_OG_Shoes_White_B75806_01_standard.jpg",
        "buy_url": "https://www.adidas.com/us/samba-og-shoes",
        "tags": ["sneakers", "white", "minimalist", "adidas", "retro"],
    },
    {
        "name": "Patagonia Better Sweater Fleece",
        "price": "$139",
        "image_url": "https://www.patagonia.com/dw/image/v2/BDJB_PRD/on/demandware.static/-/Sites-patagonia-master/default/dw5be1d9a0/images/hi-res/25528_BLK.jpg",
        "buy_url": "https://www.patagonia.com/product/mens-better-sweater-fleece-jacket",
        "tags": ["fleece", "earth tones", "minimalist", "patagonia", "outdoor"],
    },
    {
        "name": "Ray-Ban Wayfarer Classic",
        "price": "$163",
        "image_url": "https://www.ray-ban.com/media/catalog/product/R/B/RB2140__901_58__P21.png",
        "buy_url": "https://www.ray-ban.com/usa/sunglasses/RB2140%20UNISEX%20004-wayfarer",
        "tags": ["sunglasses", "accessories", "black", "classic", "ray-ban"],
    },
    {
        "name": "Supreme Box Logo Tee",
        "price": "$44",
        "image_url": "https://via.placeholder.com/400x400/FF0000/FFFFFF?text=Supreme+Tee",
        "buy_url": "https://www.supremenewyork.com",
        "tags": ["t-shirt", "streetwear", "supreme", "graphic"],
    },
    {
        "name": "Stanley Quencher 40 oz",
        "price": "$45",
        "image_url": "https://www.stanley1913.com/cdn/shop/files/SS-10-09849-001-The-Quencher-H2.0-FlowState-Tumbler-40OZ-Cream_3f7b9c4a-2c2a-4db3-8f73-03b7ea6b3b9f.jpg",
        "buy_url": "https://www.stanley1913.com/products/the-quencher-h2-0-flowstate-tumbler-40-oz",
        "tags": ["water bottle", "accessories", "cream", "trending"],
    },
    {
        "name": "Zara Oversized Blazer",
        "price": "$90",
        "image_url": "https://static.zara.net/photos///2023/V/0/2/p/2718/272/712/2/w/750/2718272712_1_1_1.jpg",
        "buy_url": "https://www.zara.com/us/en/oversized-blazer",
        "tags": ["blazer", "minimalist", "earth tones", "oversized", "zara"],
    },
    {
        "name": "Dr. Martens 1460 Boots",
        "price": "$150",
        "image_url": "https://i1.adis.ws/i/drmartens/10072004.90.jpg",
        "buy_url": "https://www.drmartens.com/us/en/1460-smooth-leather-lace-up-boots",
        "tags": ["boots", "black", "streetwear", "dr martens", "chunky"],
    },
]


def _score_candidate(candidate: dict, signals: dict) -> int:
    """Simple tag-matching score. Gemini does the real ranking — this just pre-filters."""
    score = 0
    tags = set(t.lower() for t in candidate.get("tags", []))
    for signal in signals.get("style_signals", []) + signals.get("color_signals", []):
        if signal.lower() in tags:
            score += 1
    if signals.get("brand_guess", "").lower() in tags:
        score += 3
    category = signals.get("product_category", "").lower()
    if any(category in t for t in tags):
        score += 2
    return score


# ── SerpApi Path ──────────────────────────────────────────────────────────────

async def source_via_serpapi(screenshot_b64: str, search_query: str) -> list[ProductCandidate]:
    """
    Uses SerpApi Google Lens to find purchasable products from the viewport image.
    Falls back to hardcoded catalog if SerpApi fails.
    Docs: https://serpapi.com/google-lens-api
    """
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "engine": "google_lens",
                    "url": f"data:image/jpeg;base64,{screenshot_b64}",
                    "api_key": settings.SERPAPI_KEY,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            candidates = []
            for item in data.get("visual_matches", [])[:5]:
                candidates.append(ProductCandidate(
                    name=item.get("title", "Unknown Product"),
                    price=item.get("price", {}).get("value", "See site"),
                    image_url=item.get("thumbnail", ""),
                    buy_url=item.get("link", "#"),
                    source="serpapi",
                ))

            if candidates:
                return candidates

    except Exception as e:
        print(f"[SerpApi] Failed: {e} — falling back to hardcoded catalog")

    # Fallback within serpapi mode if API fails
    return await source_via_hardcoded({})


# ── Hardcoded Catalog Path ────────────────────────────────────────────────────

async def source_via_hardcoded(signals: dict) -> list[ProductCandidate]:
    """
    Scores the hardcoded catalog against Gemini's extracted signals,
    returns top 5 candidates for Gemini to rank.
    """
    scored = sorted(
        HARDCODED_CATALOG,
        key=lambda c: _score_candidate(c, signals),
        reverse=True,
    )
    top = scored[:5]
    return [
        ProductCandidate(
            name=c["name"],
            price=c["price"],
            image_url=c["image_url"],
            buy_url=c["buy_url"],
            source="hardcoded",
        )
        for c in top
    ]


# ── Public Interface ──────────────────────────────────────────────────────────

async def source_products(
    screenshot_b64: str,
    signals: dict,
) -> list[ProductCandidate]:
    """
    Entry point — routes to correct sourcing path based on feature flag.
    Always returns a list of ProductCandidate for Gemini to rank.
    """
    mode = settings.PRODUCT_SOURCING_MODE
    print(f"[Sourcing] Mode: {mode}")

    if mode == "serpapi":
        return await source_via_serpapi(screenshot_b64, signals.get("search_query", ""))
    else:
        return await source_via_hardcoded(signals)
