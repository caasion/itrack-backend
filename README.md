# iTrack Backend

FastAPI server — passive gaze commerce pipeline.

## Setup

```bash
cd itrack-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in .env with your API keys

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Confirm it's running: http://localhost:8000/health

API docs: http://localhost:8000/docs

---

## Feature Flags (set in .env)

| Flag | Values | Effect |
|------|--------|--------|
| `PRODUCT_SOURCING_MODE` | `hardcoded` / `serpapi` | Toggle product sourcing path |
| `CLOUDINARY_ENABLED` | `false` / `true` | Skip Cloudinary during dev, enable when ready |

Start with both flags on their safe defaults (`hardcoded`, `false`).
Flip one at a time once the pipeline is running end-to-end.

---

## Pipeline (POST /dwell)

```
Extension sends DwellEvent
        │
        ▼
[1] Gemini Vision — identify product + extract taste signals
        │
        ▼
[2] Backboard — merge signals into taste profile, write back
        │
        ▼
[3] Product Sourcing — SerpApi OR hardcoded catalog (toggle flag)
        │
        ▼
[4] Gemini — select best match from candidates given taste profile
        │
        ▼
[5] Cloudinary — transform product image (if CLOUDINARY_ENABLED)
        │
        ▼
RecommendationCard returned to extension
```

---

## Request / Response

**POST /dwell**

```json
{
  "user_id": "anon-abc123",
  "screenshot_b64": "<base64 JPEG>",
  "page_url": "https://www.instagram.com/",
  "page_title": "Instagram",
  "dwell_duration_ms": 2400
}
```

**Response: RecommendationCard**

```json
{
  "user_id": "anon-abc123",
  "product": {
    "name": "Nike Air Force 1 '07",
    "price": "$110",
    "image_url": "https://...",
    "buy_url": "https://...",
    "source": "hardcoded"
  },
  "match_reason": "Matches your minimalist style and black color preference.",
  "profile_snapshot": {
    "preferred_styles": ["minimalist", "streetwear"],
    "preferred_colors": ["black"],
    "price_range": "$50-$150",
    "preferred_brands": ["Nike"],
    "recent_interests": ["sneakers"]
  },
  "sourcing_mode": "hardcoded"
}
```

---

## Development Roadmap

### Phase 1 — Skeleton (Hours 0–6)
- [ ] Server starts, /health returns 200
- [ ] POST /dwell accepts request, logs to console
- [ ] Returns a hardcoded RecommendationCard (no real API calls yet)
- [ ] Extension can hit the endpoint and receive a response

### Phase 2 — Pipes Connected (Hours 6–14)
- [ ] Gemini Call 1 working (product identification from screenshot)
- [ ] Backboard read/write working (confirm profile persists between calls)
- [ ] Hardcoded catalog sourcing returning candidates
- [ ] Gemini Call 2 working (match selection)
- [ ] Full pipeline fires end-to-end with real screenshots

### Phase 3 — Real Data (Hours 14–20)
- [ ] Test with live Instagram/TikTok screenshots
- [ ] Tune Gemini prompts for accuracy
- [ ] Flip PRODUCT_SOURCING_MODE=serpapi, test + compare
- [ ] Enable CLOUDINARY_ENABLED=true, test image transforms
- [ ] Profile visibly grows across 5–10 dwell events

### Phase 4 — Polish (Hours 20–24)
- [ ] Error handling confirmed on all failure paths
- [ ] /profile/{user_id} endpoint useful for live demo
- [ ] DELETE /profile/{user_id} works for demo reset
- [ ] Response time under 3 seconds end-to-end

---

## File Structure

```
itrack-backend/
├── main.py                   # FastAPI app, CORS, router registration
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py           # All env vars + feature flags
├── models/
│   └── schemas.py            # DwellEvent, RecommendationCard, TasteProfile
├── routes/
│   ├── dwell.py              # POST /dwell — core pipeline
│   ├── profile.py            # GET/DELETE /profile/{user_id}
│   └── health.py             # GET /health
└── services/
    ├── gemini_service.py     # Gemini Vision calls (identify + select)
    ├── backboard_service.py  # Backboard read/write + in-memory cache
    ├── sourcing_service.py   # SerpApi + hardcoded catalog (toggled)
    └── cloudinary_service.py # Image animation + bg removal
```

---

## Telling the Extension What to Render

The extension receives a `RecommendationCard` JSON object and injects a card into the feed.
Minimum fields the extension needs:

```
product.image_url   → card hero image
product.name        → product title
product.price       → price badge
product.buy_url     → tap/click target
match_reason        → subtitle ("Matched to your style")
```
