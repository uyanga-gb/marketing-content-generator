"""
Refinement Agent — iterates on a caption or image prompt based on user feedback.

Supports:
  - caption refinement : user feedback on tone, length, hooks, hashtags, CTA
  - image prompt refinement : user feedback on style, subject, mood, composition

Keeps a revision history so the user can see how content evolved.
"""

from typing import Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

CAPTION_SYSTEM_PROMPT = """You are an expert social media copywriter refining content based on user feedback.

You will receive:
- The original caption
- The content context (product, platform, tone)
- The user's specific feedback / change request

Your job:
1. Apply the feedback precisely — if they say "shorter", cut it down. If they say "more playful", adjust the tone.
2. Keep what's working — don't throw away good elements the user didn't ask to change.
3. Preserve the same structure: HOOK line + full caption body + hashtags.

Respond in this exact format:

HOOK: <revised opening hook, max 15 words>
CAPTION:
<revised full caption including hashtags>"""


IMAGE_PROMPT_SYSTEM = """You are an expert AI image generation prompt engineer refining prompts based on user feedback.

You will receive:
- The original image generation prompt
- The content context (product, platform, tone)
- The user's specific feedback / change request

Your job:
1. Apply the feedback precisely — adjust subject, style, lighting, composition, colors as requested.
2. Keep all elements the user didn't ask to change.
3. Return ONLY the revised prompt text — no explanation, no extra text."""


def _parse_caption_response(text: str) -> dict[str, Any]:
    """Parses HOOK + CAPTION from the refinement response."""
    hook = ""
    caption = ""
    for line in text.splitlines():
        if line.startswith("HOOK:"):
            hook = line[len("HOOK:"):].strip()
        elif line.startswith("CAPTION:"):
            idx = text.index("CAPTION:")
            caption = text[idx + len("CAPTION:"):].strip()
            break
    return {"hook": hook, "caption": caption, "char_count": len(caption)}


def refine_caption(
    current_caption: dict[str, Any],
    feedback: str,
    collected_data: dict[str, Any],
    content_plan: dict[str, Any],
    revision_history: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Refines a caption based on user feedback.

    Args:
        current_caption:  the caption dict being refined {hook, caption, char_count, label}
        feedback:         user's natural language feedback
        collected_data:   original session context
        content_plan:     original content plan
        revision_history: list of previous revisions for this variation

    Returns:
        Refined caption dict with updated hook, caption, char_count + revision metadata
    """
    client = OpenAI()

    context = (
        f"Product: {collected_data.get('product_type')}\n"
        f"Platform: {collected_data.get('platform')}\n"
        f"Tone: {content_plan.get('tone')}\n"
        f"CTA: {content_plan.get('cta')}"
    )

    revision_num = len(revision_history) + 2  # v1 is original, so next is v2+

    user_prompt = f"""CONTEXT:
{context}

CURRENT CAPTION (revision {revision_num - 1}):
HOOK: {current_caption.get('hook')}
CAPTION:
{current_caption.get('caption')}

USER FEEDBACK:
{feedback}

Please apply this feedback and return the revised caption."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": CAPTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    parsed = _parse_caption_response(response.choices[0].message.content)

    return {
        "label": current_caption.get("label"),
        "hook": parsed["hook"],
        "caption": parsed["caption"],
        "char_count": parsed["char_count"],
        "revision": revision_num,
        "feedback_applied": feedback,
    }


def refine_image_prompt(
    current_prompt: str,
    feedback: str,
    collected_data: dict[str, Any],
    content_plan: dict[str, Any],
    revision_history: list[dict[str, Any]],
) -> str:
    """
    Refines an image generation prompt based on user feedback,
    then returns the revised prompt string.
    """
    client = OpenAI()

    context = (
        f"Product: {collected_data.get('product_type')}\n"
        f"Platform: {collected_data.get('platform')}\n"
        f"Tone: {content_plan.get('tone')}"
    )

    revision_num = len(revision_history) + 2

    user_prompt = f"""CONTEXT:
{context}

CURRENT IMAGE PROMPT (revision {revision_num - 1}):
{current_prompt}

USER FEEDBACK:
{feedback}

Please apply this feedback and return the revised image generation prompt."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": IMAGE_PROMPT_SYSTEM},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content.strip()
