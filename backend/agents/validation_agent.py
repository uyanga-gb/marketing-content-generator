"""
Validation Agent — ensures the content package meets platform guidelines
before handing off the final ready-to-post package.

Checks:
  Image:
    - Minimum resolution: 1080x1080 (square), 1080x1350 (portrait), 1080x566 (landscape)
    - Maximum file size: 8 MB
    - Supported formats: JPEG, PNG
    - Aspect ratio: between 4:5 and 1.91:1

  Caption:
    - Maximum length: 2200 characters (Instagram limit)
    - Recommended length: under 125 characters for above-the-fold display
    - Hashtag count: max 30 hashtags
    - No banned/spammy patterns

  Final package:
    - Assembles best caption + image into a ready-to-post dict
    - Flags any warnings the user should know about
"""

import base64
import io
import re
from typing import Any

# ---------------------------------------------------------------------------
# Platform rules (currently Instagram — extend for other platforms)
# ---------------------------------------------------------------------------

PLATFORM_RULES = {
    "Instagram": {
        "caption_max_chars": 2200,
        "caption_recommended_chars": 125,
        "max_hashtags": 30,
        "max_file_size_mb": 8,
        "min_width": 320,
        "min_height": 320,
        "supported_formats": ["JPEG", "PNG", "JPG"],
        "min_aspect_ratio": 0.8,   # 4:5  portrait
        "max_aspect_ratio": 1.91,  # 1.91:1 landscape
    },
    "Twitter/X": {
        "caption_max_chars": 280,
        "caption_recommended_chars": 200,
        "max_hashtags": 2,
        "max_file_size_mb": 5,
        "min_width": 600,
        "min_height": 335,
        "supported_formats": ["JPEG", "PNG", "GIF", "WEBP"],
        "min_aspect_ratio": 0.5,
        "max_aspect_ratio": 3.0,
    },
    "LinkedIn": {
        "caption_max_chars": 3000,
        "caption_recommended_chars": 150,
        "max_hashtags": 5,
        "max_file_size_mb": 5,
        "min_width": 552,
        "min_height": 276,
        "supported_formats": ["JPEG", "PNG"],
        "min_aspect_ratio": 0.5,
        "max_aspect_ratio": 3.0,
    },
}

DEFAULT_RULES = PLATFORM_RULES["Instagram"]


# ---------------------------------------------------------------------------
# Caption validation
# ---------------------------------------------------------------------------

def _validate_caption(caption: str, rules: dict) -> dict[str, Any]:
    """Validates a caption string against platform rules."""
    errors = []
    warnings = []

    char_count = len(caption)
    hashtag_count = len(re.findall(r"#\w+", caption))

    if char_count > rules["caption_max_chars"]:
        errors.append(
            f"Caption too long: {char_count} chars "
            f"(max {rules['caption_max_chars']})"
        )
    elif char_count > rules["caption_recommended_chars"]:
        warnings.append(
            f"Caption is {char_count} chars — only the first "
            f"{rules['caption_recommended_chars']} show above the fold"
        )

    if hashtag_count > rules["max_hashtags"]:
        errors.append(
            f"Too many hashtags: {hashtag_count} "
            f"(max {rules['max_hashtags']})"
        )
    elif hashtag_count == 0:
        warnings.append("No hashtags found — consider adding some for reach")

    return {
        "char_count": char_count,
        "hashtag_count": hashtag_count,
        "errors": errors,
        "warnings": warnings,
        "passed": len(errors) == 0,
    }


# ---------------------------------------------------------------------------
# Image validation
# ---------------------------------------------------------------------------

def _validate_image(
    image_b64: str | None,
    media_type: str,
    image_url: str | None,
    rules: dict,
) -> dict[str, Any]:
    """Validates image dimensions, size and format."""
    errors = []
    warnings = []
    width = height = None

    # Format check
    fmt = media_type.split("/")[-1].upper().replace("JPEG", "JPEG")
    if fmt not in [f.upper() for f in rules["supported_formats"]]:
        errors.append(f"Unsupported format: {fmt}")

    # If we have base64 data, check dimensions and size
    if image_b64:
        try:
            from PIL import Image as PILImage

            raw = base64.b64decode(image_b64)
            size_mb = len(raw) / (1024 * 1024)

            if size_mb > rules["max_file_size_mb"]:
                errors.append(
                    f"File too large: {size_mb:.1f} MB "
                    f"(max {rules['max_file_size_mb']} MB)"
                )

            img = PILImage.open(io.BytesIO(raw))
            width, height = img.size

            if width < rules["min_width"] or height < rules["min_height"]:
                errors.append(
                    f"Resolution too low: {width}x{height} "
                    f"(min {rules['min_width']}x{rules['min_height']})"
                )

            aspect = width / height
            if aspect < rules["min_aspect_ratio"]:
                errors.append(
                    f"Aspect ratio too tall: {aspect:.2f} "
                    f"(min {rules['min_aspect_ratio']})"
                )
            elif aspect > rules["max_aspect_ratio"]:
                errors.append(
                    f"Aspect ratio too wide: {aspect:.2f} "
                    f"(max {rules['max_aspect_ratio']})"
                )

            if width != height:
                warnings.append(
                    f"Non-square image ({width}x{height}) — "
                    "square (1:1) gets best reach on Instagram feed"
                )

        except Exception as e:
            warnings.append(f"Could not fully validate image: {e}")

    elif image_url:
        # URL-based image (DALL-E output) — we can't check dimensions without downloading
        warnings.append(
            "Image is a URL (DALL-E output) — dimensions not verified locally. "
            "Download and check before posting."
        )
    else:
        errors.append("No image data provided")

    return {
        "width": width,
        "height": height,
        "errors": errors,
        "warnings": warnings,
        "passed": len(errors) == 0,
    }


# ---------------------------------------------------------------------------
# Package assembly
# ---------------------------------------------------------------------------

def _pick_best_caption(captions: list[dict]) -> dict:
    """
    Picks the caption closest to the recommended length
    that has no obvious issues.
    """
    # Prefer captions under 2200 chars, sorted by how close they are to 125
    valid = [c for c in captions if c.get("char_count", 9999) <= 2200]
    if not valid:
        return captions[0]
    return min(valid, key=lambda c: abs(c.get("char_count", 0) - 125))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def validation_agent(
    platform: str,
    captions: list[dict[str, Any]],
    image_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Validates captions and image against platform guidelines,
    then assembles the final ready-to-post package.

    Args:
        platform:     e.g. "Instagram", "Twitter/X", "LinkedIn"
        captions:     list of caption dicts from caption_agent
        image_result: dict from image_agent

    Returns:
        {
            "platform": str,
            "ready_to_post": bool,
            "caption_validations": list[dict],   # one per variation
            "image_validation": dict,
            "best_caption": dict,                # recommended caption
            "package": {                         # final ready-to-post bundle
                "caption": str,
                "image_url": str | None,
                "image_b64": str | None,
                "media_type": str,
            },
            "all_warnings": list[str],
            "all_errors": list[str],
        }
    """
    rules = PLATFORM_RULES.get(platform, DEFAULT_RULES)

    # --- Validate all caption variations ---
    caption_validations = []
    for cap in captions:
        result = _validate_caption(cap.get("caption", ""), rules)
        result["label"] = cap.get("label", "")
        caption_validations.append(result)

    # --- Validate image ---
    image_validation = _validate_image(
        image_b64=image_result.get("image_b64"),
        media_type=image_result.get("media_type", "image/jpeg"),
        image_url=image_result.get("url"),
        rules=rules,
    )

    # --- Pick best caption ---
    best_caption = _pick_best_caption(captions)

    # --- Collect all errors and warnings ---
    all_errors = image_validation["errors"].copy()
    all_warnings = image_validation["warnings"].copy()

    best_cap_validation = next(
        (v for v in caption_validations if v["label"] == best_caption.get("label")),
        caption_validations[0] if caption_validations else {},
    )
    all_errors += best_cap_validation.get("errors", [])
    all_warnings += best_cap_validation.get("warnings", [])

    ready = len(all_errors) == 0

    return {
        "platform": platform,
        "ready_to_post": ready,
        "caption_validations": caption_validations,
        "image_validation": image_validation,
        "best_caption": best_caption,
        "package": {
            "caption": best_caption.get("caption", ""),
            "image_url": image_result.get("url"),
            "image_b64": image_result.get("image_b64"),
            "media_type": image_result.get("media_type", "image/jpeg"),
        },
        "all_warnings": all_warnings,
        "all_errors": all_errors,
    }
