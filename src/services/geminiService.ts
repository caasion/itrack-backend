import { GoogleGenerativeAI } from "@google/generative-ai";
import { z } from "zod";

import { settings } from "../config/settings.js";
import * as backboardService from "./backboardService.js";
import type { GeminiSignals } from "./backboardService.js";

const genAI = new GoogleGenerativeAI(settings.GEMINI_API_KEY);
const MODEL_CANDIDATES = [
  "gemini-1.5-flash",
  "gemini-1.5-flash-latest",
  "gemini-2.0-flash",
  "gemini-2.0-flash-lite",
  "gemini-2.0-flash-exp",
];

let selectedModelName: string | undefined;

const GeminiSignalsSchema = z.object({
  product_name: z.string(),
  product_category: z.string(),
  style_signals: z.array(z.string()),
  color_signals: z.array(z.string()),
  estimated_price_range: z.string(),
  brand_guess: z.string(),
});

const FALLBACK_SIGNALS: GeminiSignals = {
  product_name: "unknown",
  product_category: "unknown",
  style_signals: [],
  color_signals: [],
  estimated_price_range: "unknown",
  brand_guess: "unknown",
};

const IDENTIFY_PROMPT = `You are analyzing a screenshot from a social media feed (Instagram or TikTok).
Identify the primary product visible and extract taste signals.
Respond ONLY with valid JSON - no markdown, no explanation.
{
  product_name, product_category, style_signals, color_signals,
  estimated_price_range, brand_guess
}
Page URL: {pageUrl}
Page title: {pageTitle}`;

const stripMarkdownFences = (text: string): string => {
  const trimmed = text.trim();
  if (!trimmed.startsWith("```")) {
    return trimmed;
  }

  const noStart = trimmed.replace(/^```(?:json)?\s*/i, "");
  return noStart.replace(/\s*```$/, "").trim();
};

const isMissingModelError = (error: unknown): boolean => {
  if (typeof error !== "object" || error === null) {
    return false;
  }

  const maybeStatus = "status" in error ? (error as { status?: unknown }).status : undefined;
  if (maybeStatus === 404) {
    return true;
  }

  const maybeMessage =
    "message" in error ? (error as { message?: unknown }).message : undefined;
  return typeof maybeMessage === "string" && maybeMessage.toLowerCase().includes("not found");
};

const generateWithModelFallback = async (
  parts: Array<{ inlineData: { mimeType: string; data: string } } | string>,
): Promise<string> => {
  const orderedCandidates = selectedModelName
    ? [selectedModelName, ...MODEL_CANDIDATES.filter((name) => name !== selectedModelName)]
    : MODEL_CANDIDATES;

  let lastError: unknown;

  for (const modelName of orderedCandidates) {
    try {
      const model = genAI.getGenerativeModel({ model: modelName });
      const result = await model.generateContent(parts);
      if (selectedModelName !== modelName) {
        console.log(`[Gemini] Using model: ${modelName}`);
      }
      selectedModelName = modelName;
      return result.response.text();
    } catch (error) {
      lastError = error;
      if (isMissingModelError(error)) {
        console.warn(`[Gemini] Model unavailable, trying next: ${modelName}`);
        continue;
      }
      throw error;
    }
  }

  throw lastError ?? new Error("No working Gemini model found");
};

export const identifyAndUpdate = async (
  screenshotB64: string,
  userId: string,
  pageUrl: string,
  pageTitle?: string,
): Promise<void> => {
  let signals: GeminiSignals = FALLBACK_SIGNALS;

  try {
    const imagePart = {
      inlineData: {
        mimeType: "image/jpeg",
        data: screenshotB64,
      },
    };

    const prompt = IDENTIFY_PROMPT.replace("{pageUrl}", pageUrl).replace(
      "{pageTitle}",
      pageTitle ?? "unknown",
    );

    const rawText = await generateWithModelFallback([imagePart, prompt]);
    const jsonText = stripMarkdownFences(rawText);

    const parsedJson: unknown = JSON.parse(jsonText);
    signals = GeminiSignalsSchema.parse(parsedJson);
  } catch (error) {
    console.warn("[Gemini] identifyAndUpdate failed", error);
  }

  try {
    await backboardService.updateProfile(userId, signals);
  } catch (error) {
    console.warn("[Gemini] Backboard update failed", error);
  }
};
