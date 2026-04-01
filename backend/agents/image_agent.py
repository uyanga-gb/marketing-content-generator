"""
Image Agent — handles two scenarios:

1. User uploads an image:
   - Sends it to GPT-4o Vision with the content plan for analysis + overlay suggestions.
   - Returns the original image (base64) + analysis.

2. No image / user wants one generated:
   - Builds a detailed image generation prompt using GPT-4o.
   - Calls DALL-E 3 to generate the image.
   - Returns the generated image URL + the prompt used.
"""

import base64
import json
from typing import Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Vision analysis (user uploads an image)
# ---------------------------------------------------------------------------

VISION_SYSTEM_PROMPT = """You are a visual marketing expert.
Analyse the provided image in the context of the social media content plan below.
Return a JSON object with exactly these fields:

{
  "image_assessment": "2-3 sentence evaluation of the image for this campaign",
  "overlay_suggestions": ["suggestion 1", "suggestion 2", "suggestion 3"],
  "crop_recommendation": "aspect ratio and crop advice for the target platform",
  "color_palette": ["#hex1", "#hex2", "#hex3"],
  "alt_text": "SEO-friendly alt text for the image"
}

Respond ONLY with the JSON."""


def _analyse_uploaded_image(
    image_b64: str,
    media_type: str,
    collected_data: dict[str, Any],
    content_plan: dict[str, Any],
) -> dict[str, Any]:
    """Uses GPT-4o Vision to analyse an uploaded image."""
    client = OpenAI()

    context = (
        f"Platform: {collected_data.get('platform')}\n"
        f"Product: {collected_data.get('product_type')}\n"
        f"Tone: {content_plan.get('tone')}\n"
        f"Post format: {content_plan.get('post_format')}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": VISION_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{media_type};base64,{image_b64}"
                        },
                    },
                    {"type": "text", "text": context},
                ],
            },
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    analysis: dict[str, Any] = json.loads(raw)
    return analysis


# ---------------------------------------------------------------------------
# Image-prompt generation + DALL-E 3 generation
# ---------------------------------------------------------------------------

PROMPT_GEN_SYSTEM = """You are an expert at writing image generation prompts.
Given a content plan and product details, write a single, richly detailed
image generation prompt (max 200 words) optimised for photorealistic AI image
generation. Return ONLY the prompt text — nothing else."""


def _build_generation_prompt(
    collected_data: dict[str, Any],
    content_plan: dict[str, Any],
) -> str:
    """Asks GPT-4o to write an optimal DALL-E image generation prompt."""
    client = OpenAI()

    user_msg = (
        f"Product: {collected_data.get('product_type')}\n"
        f"Platform: {collected_data.get('platform')}\n"
        f"Tone: {content_plan.get('tone')}\n"
        f"Key messages: {', '.join(content_plan.get('key_messages', []))}\n"
        f"Post format: {content_plan.get('post_format')}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": PROMPT_GEN_SYSTEM},
            {"role": "user", "content": user_msg},
        ],
    )

    return response.choices[0].message.content.strip()


def _call_image_generation_api(prompt: str) -> dict[str, Any]:
    """Calls DALL-E 3 to generate an image."""
    client = OpenAI()

    response = client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    revised_prompt = response.data[0].revised_prompt or prompt

    return {
        "url": image_url,
        "image_b64": None,
        "media_type": "image/png",
        "prompt_used": revised_prompt,
    }


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def image_agent(
    collected_data: dict[str, Any],
    content_plan: dict[str, Any],
    uploaded_image_b64: str | None = None,
    uploaded_media_type: str = "image/jpeg",
) -> dict[str, Any]:
    """
    Main image agent function.

    Args:
        collected_data:       output from chat_agent ("collected" field)
        content_plan:         output from planner_agent
        uploaded_image_b64:   base64-encoded image if user uploaded one
        uploaded_media_type:  MIME type of the uploaded image

    Returns:
        {
            "mode": "analyse" | "generate",
            "image_b64": str | None,
            "media_type": str,
            # analyse mode:
            "analysis": dict,
            # generate mode:
            "prompt_used": str,
            "url": str | None,
        }
    """
    if uploaded_image_b64:
        analysis = _analyse_uploaded_image(
            uploaded_image_b64,
            uploaded_media_type,
            collected_data,
            content_plan,
        )
        return {
            "mode": "analyse",
            "analysis": analysis,
            "image_b64": uploaded_image_b64,
            "media_type": uploaded_media_type,
        }

    # No image uploaded — generate one with DALL-E 3
    prompt = _build_generation_prompt(collected_data, content_plan)
    gen_result = _call_image_generation_api(prompt)
    return {
        "mode": "generate",
        **gen_result,
    }
