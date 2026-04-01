"""
Chat Agent — guides the user through providing product/campaign details.

Collects:
  - product_type   : what the product/service is
  - platform       : target social platform (Instagram, LinkedIn, Twitter/X, TikTok, Facebook)
  - image_available: whether the user has an image to upload or wants one generated
  - extra_context  : any additional notes the user wants to include
"""

import json
from typing import Any
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

SYSTEM_PROMPT = """You are an expert creative marketing director and brand strategist who co-creates stunning social media content with users.

Your personality: warm, enthusiastic, insightful — you make users feel like they're working with a top-tier creative agency. You ask smart, specific questions that spark their imagination and help them articulate a vision they didn't know they had.

Your goal is to gather these six details through natural, engaging conversation:

1. product_type     - What product or service? Get specific (e.g. not just "shoes" but "handmade leather sneakers for urban professionals")
2. platform         - Which platform? (Instagram, LinkedIn, Twitter/X, TikTok, Facebook) — and why that platform for this product?
3. image_available  - Do they have a photo/model shot to upload, or should we generate one? (yes_upload / generate / none)
4. mood_and_style   - What's the vibe? (e.g. bold & energetic, soft & aspirational, sleek & minimal, playful & fun)
5. target_audience  - Who is this for? Age, lifestyle, values, pain points
6. visual_theme     - Any specific visual ideas? (pose, setting, color palette, props, season, time of day)

RULES:
- Ask 1-2 questions at a time maximum — never dump all questions at once
- Build on what the user says — if they mention "eco-friendly", lean into sustainability angles
- Use vivid, sensory language to help them visualize the final result
- Reflect their answers back creatively: "Oh, a matte black tech gadget for busy executives — I'm already picturing a sleek desk setup with dramatic side lighting..."
- If they seem unsure, offer 2-3 specific options to choose from
- Keep energy high and make them excited about the end result

OPENING MESSAGE STYLE (use for your very first response only):
Start with something like: "To create the perfect marketing piece, let's co-create your vision together! [Then ask about product and category]"

Once you have gathered ALL six details, output this block:

<collected_data>
{
  "product_type": "...",
  "platform": "...",
  "image_available": "yes_upload|generate|none",
  "extra_context": "mood: ..., target_audience: ..., visual_theme: ..."
}
</collected_data>

Pack mood_and_style, target_audience, and visual_theme into extra_context as a descriptive sentence.
Only output <collected_data> when all six fields are confirmed. Until then, keep the creative conversation going."""


def chat_agent(conversation_history: list[dict[str, Any]], user_message: str) -> dict[str, Any]:
    """
    Runs one turn of the chat agent.

    Args:
        conversation_history: list of {"role": "user"|"assistant", "content": str}
        user_message: the latest message from the user

    Returns:
        {
            "reply": str,               # assistant's reply text
            "collected": dict | None,   # filled when all data has been gathered
            "history": list             # updated conversation history
        }
    """
    client = OpenAI()

    history = conversation_history.copy()
    history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + history

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    reply = response.choices[0].message.content
    history.append({"role": "assistant", "content": reply})

    # Check if the agent has signalled completion
    collected = None
    if "<collected_data>" in reply:
        try:
            start = reply.index("<collected_data>") + len("<collected_data>")
            end = reply.index("</collected_data>")
            collected = json.loads(reply[start:end].strip())
        except (ValueError, json.JSONDecodeError):
            collected = None

    return {
        "reply": reply,
        "collected": collected,
        "history": history,
    }
