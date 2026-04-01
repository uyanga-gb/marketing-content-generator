"""
Integration test — runs the full pipeline with mock collected data,
bypassing the chat agent (so you don't need an interactive terminal).

Usage:
    cd backend
    python test_pipeline.py
"""

import base64
import json
from agents.planner_agent import planner_agent
from agents.caption_agent import caption_agent
from agents.image_agent import image_agent
from agents.validation_agent import validation_agent


MOCK_COLLECTED = {
    "product_type": "eco-friendly reusable water bottle",
    "platform": "Instagram",
    "image_available": "generate",
    "extra_context": "Target audience is fitness enthusiasts aged 20-35. The brand values sustainability and minimalist design.",
}


def separator(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def test_planner() -> dict:
    separator("STEP 2 — PLANNER AGENT")
    plan = planner_agent(MOCK_COLLECTED)
    print(json.dumps(plan, indent=2))
    assert "post_format" in plan, "Missing post_format"
    assert "tone" in plan, "Missing tone"
    assert "key_messages" in plan, "Missing key_messages"
    print("\n✓ Planner agent passed")
    return plan


def test_captions(plan: dict) -> list:
    separator("STEP 3 — CAPTION AGENT")
    captions = caption_agent(MOCK_COLLECTED, plan)
    assert len(captions) == 3, f"Expected 3 captions, got {len(captions)}"
    for cap in captions:
        print(f"\n--- {cap['label']} ---")
        print(f"  Hook: {cap['hook']}")
        print(f"  Caption ({cap['char_count']} chars):\n  {cap['caption'][:200]}…")
    print("\n✓ Caption agent passed")
    return captions


def test_image_generate(plan: dict) -> dict:
    separator("STEP 4 — IMAGE AGENT (generate mode)")
    result = image_agent(MOCK_COLLECTED, plan)
    assert result["mode"] == "generate", f"Expected generate mode, got {result['mode']}"
    print(f"  Mode: {result['mode']}")
    print(f"  Prompt: {result.get('prompt_used', '')[:200]}…")
    if result.get("note"):
        print(f"  Note: {result['note']}")
    print("\n✓ Image agent (generate) passed")
    return result


def test_image_analyse(plan: dict) -> dict:
    separator("STEP 4 — IMAGE AGENT (analyse mode)")
    # Generate a valid 100x100 green PNG programmatically
    import io
    from PIL import Image as PILImage
    img = PILImage.new("RGB", (100, 100), color=(34, 139, 34))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    test_png = base64.b64encode(buf.getvalue()).decode()

    result = image_agent(MOCK_COLLECTED, plan, uploaded_image_b64=test_png, uploaded_media_type="image/png")
    assert result["mode"] == "analyse", f"Expected analyse mode, got {result['mode']}"
    print(f"  Mode: {result['mode']}")
    print(f"  Analysis: {json.dumps(result.get('analysis', {}), indent=4)}")
    print("\n✓ Image agent (analyse) passed")
    return result


def test_validation(captions: list, image_result: dict) -> dict:
    separator("STEP 5 — VALIDATION AGENT")
    result = validation_agent(
        platform=MOCK_COLLECTED["platform"],
        captions=captions,
        image_result=image_result,
    )
    print(f"  Ready to post: {result['ready_to_post']}")
    print(f"  Errors:   {result['all_errors'] or 'none'}")
    print(f"  Warnings: {result['all_warnings'] or 'none'}")
    print(f"  Best caption: {result['best_caption']['label']} ({result['best_caption']['char_count']} chars)")
    print(f"  Package image: {'URL' if result['package']['image_url'] else 'base64'}")
    print("\n✓ Validation agent passed")
    return result


if __name__ == "__main__":
    print("\n🚀  Marketing Content Generator — Integration Test")
    print("    Mock data:", json.dumps(MOCK_COLLECTED, indent=2))

    plan = test_planner()
    captions = test_captions(plan)
    image_gen = test_image_generate(plan)
    test_image_analyse(plan)
    test_validation(captions, image_gen)

    separator("ALL TESTS PASSED ✓")
