"""
Planner Agent — decides the best content plan given the collected user inputs.

Outputs a structured content plan:
  - post_format   : e.g. "single_image", "carousel", "text_only", "reel_video_script"
  - tone          : e.g. "professional", "casual", "playful", "inspirational"
  - key_messages  : list of 3 bullet-point messages
  - hashtag_theme : thematic hashtag cluster suggestion
  - cta            : recommended call-to-action text
"""

import json
from typing import Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert social media content strategist.

Given information about a product/service, target platform, and context, produce a
detailed content plan as a JSON object with exactly these fields:

{
  "post_format": "single_image | carousel | text_only | reel_video_script",
  "tone": "professional | casual | playful | inspirational | educational",
  "key_messages": ["message 1", "message 2", "message 3"],
  "hashtag_theme": "brief description of hashtag strategy (5-8 suggested hashtags)",
  "cta": "short call-to-action sentence",
  "platform_tips": "one sentence of platform-specific best practice"
}

Respond ONLY with the JSON object — no extra text."""


def planner_agent(collected_data: dict[str, Any]) -> dict[str, Any]:
    """
    Decides post format and content structure based on collected user data.

    Args:
        collected_data: output from chat_agent's "collected" field

    Returns:
        content_plan dict with keys: post_format, tone, key_messages,
        hashtag_theme, cta, platform_tips
    """
    client = OpenAI()

    user_prompt = (
        f"Product/Service: {collected_data.get('product_type', 'unknown')}\n"
        f"Platform: {collected_data.get('platform', 'Instagram')}\n"
        f"Image availability: {collected_data.get('image_available', 'none')}\n"
        f"Additional context: {collected_data.get('extra_context', 'none')}"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content.strip()
    content_plan: dict[str, Any] = json.loads(raw)
    return content_plan
