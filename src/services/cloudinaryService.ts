import { v2 as cloudinary } from "cloudinary";

import { settings } from "../config/settings.js";

cloudinary.config({
  cloud_name: settings.CLOUDINARY_CLOUD_NAME,
  api_key: settings.CLOUDINARY_API_KEY,
  api_secret: settings.CLOUDINARY_API_SECRET,
  secure: true,
});

export const transformProductImage = async (imageUrl: string): Promise<string> => {
  if (!settings.CLOUDINARY_ENABLED) {
    console.log("[Cloudinary] Disabled — returning raw URL");
    return imageUrl;
  }

  let publicId: string | undefined;

  try {
    const uploadResult = await cloudinary.uploader.upload(imageUrl, {
      folder: "itrack/products",
      overwrite: false,
    });
    publicId = uploadResult.public_id;

    const animatedUrl = cloudinary.url(publicId, {
      resource_type: "video",
      transformation: [
        { effect: "zoompan:1.2:3" },
        { effect: "loop" },
        { effect: "background_removal" },
        { width: 600, height: 800, crop: "fill", gravity: "auto" },
        { quality: "auto", fetch_format: "auto" },
      ],
    });

    return animatedUrl;
  } catch {
    // Fall through to fallback path.
  }

  try {
    if (!publicId) {
      const uploadResult = await cloudinary.uploader.upload(imageUrl, {
        folder: "itrack/products",
        overwrite: false,
      });
      publicId = uploadResult.public_id;
    }

    const fallbackUrl = cloudinary.url(publicId, {
      transformation: [
        { effect: "background_removal" },
        { width: 600, height: 800, crop: "fill", gravity: "auto" },
        { quality: "auto", fetch_format: "auto" },
      ],
    });

    return fallbackUrl;
  } catch (error) {
    console.error("[Cloudinary] Fallback also failed", error);
    return imageUrl;
  }
};
