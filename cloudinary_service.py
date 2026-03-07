"""
Cloudinary Service
------------------
Transforms product images to be visually competitive with Reels.

PRIMARY:   Upload image → generate looping animation
FALLBACK:  Background removal + smart crop only

Controlled by settings.CLOUDINARY_ENABLED.
If False, raw image URL is returned unchanged (useful during dev).
"""

import cloudinary
import cloudinary.uploader
import cloudinary.api
from config.settings import settings

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


async def transform_product_image(image_url: str) -> str:
    """
    Takes a raw product image URL, applies Cloudinary transforms,
    returns the transformed URL.

    If CLOUDINARY_ENABLED is False, returns the original URL unchanged.
    """
    if not settings.CLOUDINARY_ENABLED:
        print("[Cloudinary] Disabled — returning raw URL")
        return image_url

    try:
        # Upload the product image to Cloudinary
        upload_result = cloudinary.uploader.upload(
            image_url,
            folder="itrack/products",
            overwrite=False,
            resource_type="image",
        )
        public_id = upload_result["public_id"]

        # PRIMARY: Try to generate a short looping animation
        # Uses Cloudinary's AI "zoompan" effect to simulate motion from still image
        animated_url = cloudinary.CloudinaryImage(public_id).build_url(
            transformation=[
                {"effect": "zoompan", "zoom": "1.2", "duration": 3},
                {"effect": "loop"},
                {"background_removal": "cloudinary_ai"},
                {"width": 600, "height": 800, "crop": "fill", "gravity": "auto"},
                {"quality": "auto", "fetch_format": "auto"},
            ],
            resource_type="video",  # Animation output
        )
        print(f"[Cloudinary] Animated URL: {animated_url}")
        return animated_url

    except Exception as e:
        print(f"[Cloudinary] Animation failed: {e} — trying background removal fallback")

    try:
        # FALLBACK: Background removal + smart crop
        fallback_url = cloudinary.CloudinaryImage(public_id).build_url(
            transformation=[
                {"effect": "background_removal"},
                {"width": 600, "height": 800, "crop": "fill", "gravity": "auto"},
                {"quality": "auto", "fetch_format": "auto"},
            ],
        )
        print(f"[Cloudinary] Fallback URL: {fallback_url}")
        return fallback_url

    except Exception as e:
        print(f"[Cloudinary] Fallback also failed: {e} — returning raw URL")
        return image_url
