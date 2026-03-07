# iTrack Backend (V3)

Fastify + TypeScript server for passive gaze commerce with a two-pipeline architecture.

## Requirements

- Node.js 18+ (native `fetch` required)
- npm

## Setup

```bash
cd itrack-backend
npm install

cp .env.example .env
# Fill in .env with your API keys (or leave hardcoded mode for local dev)

npm run dev
```

Confirm it's running: http://localhost:8000/health

---

## Local Development (Zero-Config Mode)

The backend runs end-to-end with fallback mode:

```env
PRODUCT_SOURCING_MODE=hardcoded
CLOUDINARY_ENABLED=false
```

| Service | What happens without a key |
|---------|---------------------------|
| **Gemini** | Failures are non-fatal; the recommendation pipeline still returns cards |
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
│   → Top visual match    │  │   → SerpApi Shopping   │  │   → Write to Backboard│
│   → Cloudinary          │  │   → Top picks          │  │ (fire-and-forget)     │
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
  "current_product": {
    "name": "Nike Air Force 1 '07",
    "price": "$110",
    "image_url": "https://...",
    "buy_url": "https://...",
    "source": "serpapi_lens"
  },
  "taste_picks": [
    {
      "name": "Adidas Samba OG",
      "price": "$100",
      "image_url": "https://...",
      "buy_url": "https://...",
      "source": "serpapi_shopping"
    },
    {
      "name": "New Balance 990v5",
      "price": "$185",
      "image_url": "https://...",
      "buy_url": "https://...",
      "source": "serpapi_shopping"
    }
  ],
  "profile_snapshot": {
    "preferred_styles": ["minimalist", "streetwear"],
    "preferred_colors": ["black", "white"],
    "price_range": "$50-$200",
    "preferred_brands": ["Nike", "Adidas"],
    "recent_interests": ["sneakers"],
    "dwell_count": 3
  }
}
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
├── src/
│   ├── main.ts               # Fastify app, CORS, route registration
│   ├── config/
│   │   └── settings.ts       # Env schema + runtime settings
│   ├── models/
│   │   └── schemas.ts        # Zod request/response schemas
│   ├── routes/
│   │   ├── dwell.ts          # POST /dwell
│   │   ├── profile.ts        # GET/DELETE /profile/:userId
│   │   └── health.ts         # GET /health
│   └── services/
│       ├── geminiService.ts
│       ├── backboardService.ts
│       ├── sourcingService.ts
│       └── cloudinaryService.ts
├── package.json
├── tsconfig.json
├── .env.example
└── README.md
```

## Build and Run

```bash
npm run build
npm start
```
