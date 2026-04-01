"""
Caption Agent — calls GPT-4o to generate three distinct caption variations
based on the content plan and collected user data.

Returns a list of three captions, each with:
  - label      : "Variation A / B / C"
  - caption    : the full caption text
  - hook       : the opening hook line
  - char_count : character count (useful for platform limits)
"""

from typing import Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are a creative social media copywriter.

You will receive a content plan and product details. Generate exactly THREE caption
variations for a social media post. Each variation should have a different approach:
  - Variation A: focus on emotion / storytelling
  - Variation B: focus on benefits / features
  - Variation C: focus on social proof / urgency / FOMO

Format your response EXACTLY as follows (no extra text outside this structure):

---VARIATION_A---
HOOK: <opening hook line, max 15 words>
CAPTION:
<full caption including hashtags>
---END_A---

---VARIATION_B---
HOOK: <opening hook line, max 15 words>
CAPTION:
<full caption including hashtags>
---END_B---

---VARIATION_C---
HOOK: <opening hook line, max 15 words>
CAPTION:
<full caption including hashtags>
---END_C---"""


def _parse_variations(text: str) -> list[dict[str, Any]]:
    """Parses the structured response into a list of caption dicts."""
    variations = []
    blocks = [
        ("A", "---VARIATION_A---", "---END_A---"),
        ("B", "---VARIATION_B---", "---END_B---"),
        ("C", "---VARIATION_C---", "---END_C---"),
    ]

    for label, start_tag, end_tag in blocks:
        if start_tag in text and end_tag in text:
            block = text[text.index(start_tag) + len(start_tag): text.index(end_tag)].strip()
            hook = ""
            caption = ""

            for line in block.splitlines():
                if line.startswith("HOOK:"):
                    hook = line[len("HOOK:"):].strip()
                elif line.startswith("CAPTION:"):
                    idx = block.index("CAPTION:")
                    caption = block[idx + len("CAPTION:"):].strip()
                    break

            variations.append(
                {
                    "label": f"Variation {label}",
                    "hook": hook,
                    "caption": caption,
                    "char_count": len(caption),
                }
            )

    return variations


def caption_agent(
    collected_data: dict[str, Any],
    content_plan: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Generates three caption variations using GPT-4o.

    Args:
        collected_data: output from chat_agent ("collected" field)
        content_plan:   output from planner_agent

    Returns:
        List of three caption dicts: label, hook, caption, char_count
    """
    client = OpenAI()

    user_prompt = f"""Product/Service: {collected_data.get('product_type')}
Platform: {collected_data.get('platform')}
Extra context: {collected_data.get('extra_context', 'none')}

Content Plan:
- Post format: {content_plan.get('post_format')}
- Tone: {content_plan.get('tone')}
- Key messages: {', '.join(content_plan.get('key_messages', []))}
- Hashtag theme: {content_plan.get('hashtag_theme')}
- CTA: {content_plan.get('cta')}
- Platform tip: {content_plan.get('platform_tips', '')}

Generate three caption variations following the exact format specified."""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw_text = response.choices[0].message.content
    return _parse_variations(raw_text)
