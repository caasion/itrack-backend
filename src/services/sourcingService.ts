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
    price: "$110",
    image_url:
      "https://static.nike.com/a/images/t_PDP_1280_v1/f_auto/af20ff4c-7aa2-4d68-b16e-a28a6c96aba8/air-force-1-07-shoes-WrLlWX.png",
    buy_url: "https://www.nike.com/t/air-force-1-07-shoes",
    tags: ["sneakers", "minimalist", "white", "streetwear", "nike"],
  },
  {
    name: "Aritzia TNA Super Puff Jacket",
    price: "$325",
    image_url:
      "https://images.aritzia.com/media/catalog/product/cache/7/image/480x/9df78eab33525d08d6e5fb8d27136e95/a/r/ar_00000000000000000003388_s_a.jpg",
    buy_url: "https://www.aritzia.com/en/product/super-puff-jacket",
    tags: ["jacket", "minimalist", "black", "aritzia", "outerwear"],
  },
  {
    name: "Carhartt WIP Chase Hoodie",
    price: "$120",
    image_url: "https://images.carhartt-wip.com/media/catalog/product/i/0/i026384_0c_01_fv.jpg",
    buy_url: "https://www.carhartt-wip.com/en/sweatshirts/chase-hoodie",
    tags: ["hoodie", "streetwear", "earth tones", "oversized", "carhartt"],
  },
  {
    name: "Hydro Flask 32 oz Wide Mouth",
    price: "$55",
    image_url: "https://www.hydroflask.com/media/catalog/product/w/h/wh32bts001_a_1200x1200.jpg",
    buy_url: "https://www.hydroflask.com/32-oz-wide-mouth",
    tags: ["water bottle", "accessories", "black", "minimalist"],
  },
  {
    name: "New Balance 990v5",
    price: "$185",
    image_url:
      "https://nb.scene7.com/is/image/NB/m990gl5_nb_02_i?$pdpflexf2$&qlt=80&fmt=webp&wid=440&hei=440",
    buy_url: "https://www.newbalance.com/pd/made-in-usa-990v5",
    tags: ["sneakers", "grey", "minimalist", "new balance", "dad shoes"],
  },
  {
    name: "Lululemon Everywhere Belt Bag",
    price: "$38",
    image_url: "https://images.lululemon.com/is/image/lululemon/LU9AFBS_0001_1",
    buy_url: "https://shop.lululemon.com/p/bags/Everywhere-Belt-Bag",
    tags: ["bag", "accessories", "black", "minimalist", "lululemon"],
  },
  {
    name: "Arc'teryx Atom LT Hoody",
    price: "$260",
    image_url: "https://arcteryx.com/media/catalog/product/A/r/Atom-LT-Hoody-Mens-Black-24.jpg",
    buy_url: "https://arcteryx.com/us/en/shop/mens/atom-lt-hoody",
    tags: ["jacket", "minimalist", "black", "technical", "arcteryx"],
  },
  {
    name: "Uniqlo Ultra Light Down Jacket",
    price: "$70",
    image_url:
      "https://image.uniqlo.com/UQ/ST3/us/imagesgoods/467870/item/usgoods_09_467870.jpg",
    buy_url: "https://www.uniqlo.com/us/en/products/E467870-000",
    tags: ["jacket", "minimalist", "packable", "affordable", "uniqlo"],
  },
  {
    name: "Adidas Samba OG",
    price: "$100",
    image_url:
      "https://assets.adidas.com/images/h_840,f_auto,q_auto,fl_lossy,c_fill,g_auto/7ed0855435194229a525aad6009a0497_9366/Samba_OG_Shoes_White_B75806_01_standard.jpg",
    buy_url: "https://www.adidas.com/us/samba-og-shoes",
    tags: ["sneakers", "white", "minimalist", "adidas", "retro"],
  },
  {
    name: "Patagonia Better Sweater Fleece",
    price: "$139",
    image_url:
      "https://www.patagonia.com/dw/image/v2/BDJB_PRD/on/demandware.static/-/Sites-patagonia-master/default/dw5be1d9a0/images/hi-res/25528_BLK.jpg",
    buy_url: "https://www.patagonia.com/product/mens-better-sweater-fleece-jacket",
    tags: ["fleece", "earth tones", "minimalist", "patagonia", "outdoor"],
  },
  {
    name: "Ray-Ban Wayfarer Classic",
    price: "$163",
    image_url: "https://www.ray-ban.com/media/catalog/product/R/B/RB2140__901_58__P21.png",
    buy_url: "https://www.ray-ban.com/usa/sunglasses/RB2140%20UNISEX%20004-wayfarer",
    tags: ["sunglasses", "accessories", "black", "classic", "ray-ban"],
  },
  {
    name: "Supreme Box Logo Tee",
    price: "$44",
    image_url: "https://via.placeholder.com/400x400/FF0000/FFFFFF?text=Supreme+Tee",
    buy_url: "https://www.supremenewyork.com",
    tags: ["t-shirt", "streetwear", "supreme", "graphic"],
  },
  {
    name: "Stanley Quencher 40 oz",
    price: "$45",
    image_url:
      "https://www.stanley1913.com/cdn/shop/files/SS-10-09849-001-The-Quencher-H2.0-FlowState-Tumbler-40OZ-Cream_3f7b9c4a-2c2a-4db3-8f73-03b7ea6b3b9f.jpg",
    buy_url: "https://www.stanley1913.com/products/the-quencher-h2-0-flowstate-tumbler-40-oz",
    tags: ["water bottle", "accessories", "cream", "trending"],
  },
  {
    name: "Zara Oversized Blazer",
    price: "$90",
    image_url:
      "https://static.zara.net/photos///2023/V/0/2/p/2718/272/712/2/w/750/2718272712_1_1_1.jpg",
    buy_url: "https://www.zara.com/us/en/oversized-blazer",
    tags: ["blazer", "minimalist", "earth tones", "oversized", "zara"],
  },
  {
    name: "Dr. Martens 1460 Boots",
    price: "$150",
    image_url: "https://i1.adis.ws/i/drmartens/10072004.90.jpg",
    buy_url: "https://www.drmartens.com/us/en/1460-smooth-leather-lace-up-boots",
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
