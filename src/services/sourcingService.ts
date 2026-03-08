import { settings } from "../config/settings.js";
import type { ProductCandidate, TasteProfile } from "../models/schemas.js";
import type { GeminiSignals } from "./backboardService.js";

type CatalogEntry = {
  name: string;
  price: string;
  image_url: string;
  buy_url: string;
  tags: string[];
};

const HARDCODED_CATALOG: CatalogEntry[] = [
  {
    name: "Nike Air Force 1 '07",
    price: "$115",
    image_url:
      "https://images.unsplash.com/photo-1608231387042-66d1773070a5?q=80&w=1074&auto=format&fit=crop&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D",
    buy_url: "https://www.nike.com/t/air-force-1-07-mens-shoes-jBrhbr",
    tags: ["sneakers", "minimalist", "white", "streetwear", "nike"],
  },
  {
    name: "Lululemon Everywhere Belt Bag",
    price: "$38",
    image_url: 
      "https://images.lululemon.com/is/image/lululemon/LU9B78S_0001_1",
    buy_url: "https://shop.lululemon.com/p/bags/Everywhere-Belt-Bag/_/prod8900747",
    tags: ["bag", "accessories", "black", "minimalist", "lululemon"],
  },
  {
    name: "Adidas Samba OG",
    price: "$100",
    image_url:
      "https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/3bbecbdf584e40398446a8bf0117cf62_9366/Samba_OG_Shoes_White_B75806_01_standard.jpg",
    buy_url: "https://www.adidas.com/us/samba-og-shoes/B75806.html",
    tags: ["sneakers", "white", "minimalist", "adidas", "retro"],
  },
  {
    name: "Patagonia Better Sweater Fleece",
    price: "$139",
    image_url:
      "https://www.patagonia.ca/dw/image/v2/BDJB_PRD/on/demandware.static/-/Sites-patagonia-master/default/dw3e340922/images/hi-res/25882_GRBN.jpg?sw=512&sh=512&sfrm=png&q=95&bgcolor=f3f4ef",
    buy_url: "https://www.patagonia.com/product/mens-better-sweater-fleece-jacket/25528.html",
    tags: ["fleece", "earth tones", "minimalist", "patagonia", "outdoor"],
  },
  {
    name: "Dr. Martens 1460 Boots",
    price: "$170",
    image_url: 
      "https://i1.adis.ws/i/drmartens/11822006.80.jpg",
    buy_url: "https://www.drmartens.com/us/en/1460-smooth-leather-lace-up-boots-black/p/11822006",
    tags: ["boots", "black", "streetwear", "dr martens", "chunky"],
  },
];

export const composeQueryFromProfile = (profile: TasteProfile): string => {
  const parts = [
    profile.preferred_styles[0],
    profile.preferred_colors[0],
    profile.recent_interests[0],
    profile.preferred_brands[0],
    profile.price_range,
  ]
    .map((value) => value?.trim())
    .filter((value): value is string => Boolean(value && value.toLowerCase() !== "unknown"));

  return parts.join(" ");
};

export const scoreCandidate = (
  candidate: { tags?: string[] },
  signals: Partial<GeminiSignals>,
): number => {
  let score = 0;
  const tags = new Set((candidate.tags ?? []).map((tag) => tag.toLowerCase()));

  for (const signal of [...(signals.style_signals ?? []), ...(signals.color_signals ?? [])]) {
    if (tags.has(signal.toLowerCase())) {
      score += 1;
    }
  }

  const brand = signals.brand_guess?.toLowerCase();
  if (brand && tags.has(brand)) {
    score += 3;
  }

  const category = signals.product_category?.toLowerCase();
  if (category && [...tags].some((tag) => tag.includes(category))) {
    score += 2;
  }

  return score;
};

const toProduct = (
  candidate: CatalogEntry,
  source: ProductCandidate["source"],
): ProductCandidate => ({
  name: candidate.name,
  price: candidate.price,
  image_url: candidate.image_url,
  buy_url: candidate.buy_url,
  source,
});

const profileAsSignals = (profile: TasteProfile): Partial<GeminiSignals> => ({
  style_signals: profile.preferred_styles,
  color_signals: profile.preferred_colors,
  brand_guess: profile.preferred_brands[0],
  product_category: profile.recent_interests[0],
  estimated_price_range: profile.price_range,
});

const fetchWithTimeout = async (
  url: string,
  init: RequestInit,
  timeoutMs: number,
): Promise<Response> => {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...init, signal: controller.signal });
  } finally {
    clearTimeout(timeout);
  }
};

export const sourceViaHardcoded = async (
  signals?: Partial<GeminiSignals>,
): Promise<ProductCandidate[]> => {
  const scored = HARDCODED_CATALOG.map((candidate) => ({
    candidate,
    score: scoreCandidate(candidate, signals ?? {}),
  })).sort((a, b) => b.score - a.score);

  return scored.slice(0, 5).map(({ candidate }) => toProduct(candidate, "hardcoded"));
};

export const sourceCat1 = async (screenshotB64: string): Promise<ProductCandidate> => {
  if (settings.PRODUCT_SOURCING_MODE === "hardcoded") {
    return toProduct(HARDCODED_CATALOG[0], "hardcoded");
  }

  try {
    const response = await fetchWithTimeout(
      "https://serpapi.com/search",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          engine: "google_lens",
          api_key: settings.SERPAPI_KEY,
          url: `data:image/jpeg;base64,${screenshotB64}`,
        }),
      },
      10000,
    );

    if (response.ok) {
      const data = (await response.json()) as { visual_matches?: Array<Record<string, unknown>> };
      const top = data.visual_matches?.[0];
      if (top) {
        return {
          name: typeof top.title === "string" ? top.title : "Unknown Product",
          price:
            typeof top.price === "object" &&
            top.price !== null &&
            "value" in top.price &&
            typeof (top.price as { value: unknown }).value === "string"
              ? (top.price as { value: string }).value
              : "See site",
          image_url: typeof top.thumbnail === "string" ? top.thumbnail : "",
          buy_url: typeof top.link === "string" ? top.link : "#",
          source: "serpapi_lens",
        };
      }
    }
  } catch {
    // Fall back below.
  }

  return toProduct(HARDCODED_CATALOG[0], "hardcoded");
};

export const sourceCat2 = async (profile: TasteProfile): Promise<ProductCandidate[]> => {
  const query = composeQueryFromProfile(profile);

  if (settings.PRODUCT_SOURCING_MODE === "hardcoded" || !query) {
    const scored = HARDCODED_CATALOG.map((candidate) => ({
      candidate,
      score: scoreCandidate(candidate, profileAsSignals(profile)),
    })).sort((a, b) => b.score - a.score);
    return scored.slice(0, 3).map(({ candidate }) => toProduct(candidate, "hardcoded"));
  }

  try {
    const response = await fetchWithTimeout(
      `https://serpapi.com/search?engine=google_shopping&q=${encodeURIComponent(query)}&api_key=${encodeURIComponent(settings.SERPAPI_KEY)}`,
      {
        method: "GET",
      },
      10000,
    );

    if (response.ok) {
      const data = (await response.json()) as {
        shopping_results?: Array<Record<string, unknown>>;
      };
      const picks = (data.shopping_results ?? []).slice(0, 5).map((item) => ({
        name: typeof item.title === "string" ? item.title : "Unknown Product",
        price: typeof item.price === "string" ? item.price : "See site",
        image_url: typeof item.thumbnail === "string" ? item.thumbnail : "",
        buy_url: typeof item.link === "string" ? item.link : "#",
        source: "serpapi_shopping" as const,
      }));

      if (picks.length > 0) {
        return picks;
      }
    }
  } catch {
    // Fall back below.
  }

  const scored = HARDCODED_CATALOG.map((candidate) => ({
    candidate,
    score: scoreCandidate(candidate, profileAsSignals(profile)),
  })).sort((a, b) => b.score - a.score);
  return scored.slice(0, 3).map(({ candidate }) => toProduct(candidate, "hardcoded"));
};
