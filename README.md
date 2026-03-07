# iTrack Backend (V3)

FastAPI server — passive gaze commerce, two-pipeline architecture.

## Setup

```bash
cd itrack-backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in .env with your API keys (or leave defaults for zero-config local dev)

uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Confirm it's running: http://localhost:8000/health

API docs (interactive): http://localhost:8000/docs

---

## Local Development (Zero-Config Mode)

The backend runs fully end-to-end with **no API keys** using fallback mode:

```env
PRODUCT_SOURCING_MODE=hardcoded
CLOUDINARY_ENABLED=false
```

| Service | What happens without a key |
|---------|---------------------------|
| **Gemini** | Signals default to empty; profile won't update but cards still return |
| **SerpApi** | Hardcoded catalog used for both Cat 1 and Cat 2 |
| **Cloudinary** | Raw image URLs passed through |
| **Backboard** | In-memory cache used (profile lost on restart) |

Add real API keys one at a time as you're ready to test live integrations.

---

## Feature Flags (set in .env)

| Flag | Values | Effect |
|------|--------|--------|
| `PRODUCT_SOURCING_MODE` | `hardcoded` / `serpapi` | Toggle product sourcing between local catalog and live SerpApi |
| `CLOUDINARY_ENABLED` | `false` / `true` | Skip Cloudinary during dev, enable when ready |

---

## Pipeline (POST /dwell)

Three concurrent tasks fire on every dwell event:

```
Extension sends DwellEvent
        │
        ├──────────────────────────────────────────┐
        │                                          │
        ▼                                          ▼
┌─ Cat 1 (Visual Match) ─┐  ┌─ Cat 2 (Taste-Based) ─┐  ┌─ Gemini (Async) ──────┐
│ Screenshot              │  │ Read Backboard profile │  │ Identify product      │
│   → SerpApi Lens        │  │   → Compose query      │  │   → Extract signals   │
│   → Top 1 visual match  │  │   → SerpApi Shopping   │  │   → Write to Backboard│
│   → Cloudinary          │  │   → Top 3-5 picks      │  │ (fire-and-forget)     │
│   → current_product     │  │   → Cloudinary each    │  │                       │
└─────────────────────────┘  │   → taste_picks[]      │  └───────────────────────┘
                             └────────────────────────┘
        │                              │
        └──────────┬───────────────────┘
                   ▼
         DwellResponse returned
```

**Key design**: Gemini never blocks either card. It updates the Backboard profile for the *next* dwell's Cat 2 pipeline.

---

## Request / Response

### POST /dwell

```json
{
  "user_id": "anon-abc123",
  "screenshot_b64": "<base64 JPEG>",
  "page_url": "https://www.instagram.com/",
  "page_title": "Instagram",
  "dwell_duration_ms": 2400
}
```

### Response: DwellResponse

```json
{
  "user_id": "anon-abc123",
  "current_product": {
    "name": "Nike Air Force 1 '07",
    "price": "$110",
    "image_url": "https://...",
    "buy_url": "https://...",
    "source": "serpapi",
    "match_type": "visual_match"
  },
  "taste_picks": [
    {
      "name": "Adidas Samba OG",
      "price": "$100",
      "image_url": "https://...",
      "buy_url": "https://...",
      "source": "serpapi"
    },
    {
      "name": "New Balance 990v5",
      "price": "$185",
      "image_url": "https://...",
      "buy_url": "https://...",
      "source": "serpapi"
    }
  ],
  "profile_snapshot": {
    "preferred_styles": ["minimalist", "streetwear"],
    "preferred_colors": ["black", "white"],
    "price_range": "$50-$200",
    "preferred_brands": ["Nike", "Adidas"],
    "recent_interests": ["sneakers"]
  },
  "dwell_count": 3,
  "sourcing_mode": "serpapi"
}
```

**Null/empty semantics:**
- `current_product` is `null` when Cat 1 fails or no visual match found
- `taste_picks` is always an array (`[]` for new users, never `null`)

---

## Extension Integration

The extension receives a `DwellResponse` and renders two sidebar slots:

| Slot | Label | Data source | Update frequency |
|------|-------|-------------|-----------------|
| Top | "You looked at" | `current_product` | Every dwell |
| Bottom | "Based on your taste" | `taste_picks[]` | Every dwell (improves over time) |

### Minimum fields the extension needs:

**Cat 1 ("You looked at"):**
```
current_product.image_url   → card hero image
current_product.name        → product title
current_product.price       → price badge
current_product.buy_url     → tap/click target
```

**Cat 2 ("Based on your taste"):**
```
taste_picks[].image_url     → card hero image
taste_picks[].name          → product title
taste_picks[].price         → price badge
taste_picks[].buy_url       → tap/click target
```

**Profile debug info:**
```
dwell_count                 → show engagement counter
profile_snapshot            → debug panel / "why these picks" tooltip
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/dwell/` | Core pipeline — send dwell event, get two-category response |
| `GET` | `/health/` | Liveness check + service availability status |
| `GET` | `/profile/{user_id}` | View user's current taste profile |
| `DELETE` | `/profile/{user_id}` | Reset profile (demo reset) |

---

## File Structure

```
itrack-backend/
├── main.py                   # FastAPI app, CORS, router registration
├── run.py                    # Uvicorn server runner
├── test_pipeline.py          # Smoke test for v3 pipeline
├── requirements.txt
├── .env.example
├── config/
│   └── settings.py           # All env vars + feature flags
├── models/
│   └── schemas.py            # DwellEvent, DwellResponse, Cat1Product, TasteProfile
├── routes/
│   ├── dwell.py              # POST /dwell — two parallel pipelines + async Gemini
│   ├── profile.py            # GET/DELETE /profile/{user_id}
│   └── health.py             # GET /health — service availability
└── services/
    ├── gemini_service.py     # Gemini Vision (identify + write to Backboard)
    ├── backboard_service.py  # Taste profile persistence + in-memory cache
    ├── sourcing_service.py   # Cat 1 (Lens) + Cat 2 (Shopping) + hardcoded fallbacks
    └── cloudinary_service.py # Image animation + bg removal
```

---

## Demo Arc

1. Open Instagram → scroll to first reel
2. Cat 1 updates with "You looked at" (the product in the reel)
3. Cat 2 shows generic picks (profile is empty)
4. Scroll 2-3 more reels → Cat 2 visibly sharpens as profile builds
5. Check `profile_snapshot.dwell_count` climbing
6. Use `DELETE /profile/{user_id}` to reset and demo again
