"""
Orchestrator — coordinates the four marketing agents in sequence:

  Step 1 — Chat Agent:    multi-turn conversation to collect user inputs
  Step 2 — Planner Agent: decide post format, tone, key messages
  Step 3 — Caption Agent: generate three caption variations
  Step 4 — Image Agent:   analyse uploaded image OR generate a new one

The orchestrator holds session state and exposes two public functions:
  - run_chat_turn()     : called on every user message during the chat phase
  - run_content_pipeline(): called once all chat data is collected
"""

from typing import Any
from agents import chat_agent, planner_agent, caption_agent, image_agent, validation_agent, refine_caption, refine_image_prompt


class MarketingOrchestrator:
    """Stateful orchestrator for one content-generation session."""

    def __init__(self) -> None:
        self.conversation_history: list[dict[str, Any]] = []
        self.collected_data: dict[str, Any] | None = None
        self.content_plan: dict[str, Any] | None = None
        self.captions: list[dict[str, Any]] | None = None
        self.image_result: dict[str, Any] | None = None
        self.validation_result: dict[str, Any] | None = None
        self.phase: str = "chat"  # "chat" | "pipeline_ready" | "complete"
        # Revision histories keyed by variation index (0/1/2) or "image"
        self.revision_histories: dict[str, list[dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Phase 1 — Chat
    # ------------------------------------------------------------------

    def run_chat_turn(self, user_message: str) -> dict[str, Any]:
        """
        Process one user message through the chat agent.

        Returns:
            {
                "reply": str,
                "phase": "chat" | "pipeline_ready",
                "collected": dict | None,
            }
        """
        result = chat_agent(self.conversation_history, user_message)

        self.conversation_history = result["history"]

        if result["collected"]:
            self.collected_data = result["collected"]
            self.phase = "pipeline_ready"

        return {
            "reply": result["reply"],
            "phase": self.phase,
            "collected": self.collected_data,
        }

    # ------------------------------------------------------------------
    # Phase 2-4 — Content pipeline
    # ------------------------------------------------------------------

    def run_content_pipeline(
        self,
        uploaded_image_b64: str | None = None,
        uploaded_media_type: str = "image/jpeg",
    ) -> dict[str, Any]:
        """
        Runs planner → caption → image agents sequentially.

        Must be called after run_chat_turn() has returned phase == "pipeline_ready".

        Args:
            uploaded_image_b64:  base64-encoded image (optional)
            uploaded_media_type: MIME type of the uploaded image

        Returns full pipeline result dict.
        """
        if not self.collected_data:
            raise ValueError("No collected data yet. Complete the chat phase first.")

        # Step 2 — Plan
        print("[Orchestrator] Step 2: Running planner agent...")
        self.content_plan = planner_agent(self.collected_data)

        # Step 3 — Captions
        print("[Orchestrator] Step 3: Running caption agent...")
        self.captions = caption_agent(self.collected_data, self.content_plan)

        # Step 4 — Image
        print("[Orchestrator] Step 4: Running image agent...")
        self.image_result = image_agent(
            self.collected_data,
            self.content_plan,
            uploaded_image_b64=uploaded_image_b64,
            uploaded_media_type=uploaded_media_type,
        )

        # Step 5 — Validate
        print("[Orchestrator] Step 5: Running validation agent...")
        platform = self.collected_data.get("platform", "Instagram")
        self.validation_result = validation_agent(
            platform,
            self.captions,
            self.image_result,
        )

        self.phase = "complete"

        return self._build_output()

    # ------------------------------------------------------------------
    # Phase 3 — Refinement (feedback loop)
    # ------------------------------------------------------------------

    def refine_caption_variation(self, variation_index: int, feedback: str) -> dict[str, Any]:
        """
        Refines one caption variation based on user feedback.

        Args:
            variation_index: 0 = Variation A, 1 = B, 2 = C
            feedback:        user's natural language change request

        Returns updated captions list + revision history for this variation.
        """
        if self.phase != "complete":
            raise ValueError("Run the content pipeline first.")

        key = str(variation_index)
        history = self.revision_histories.setdefault(key, [])

        current = self.captions[variation_index]
        # Save current version to history before overwriting
        history.append(current.copy())

        refined = refine_caption(
            current_caption=current,
            feedback=feedback,
            collected_data=self.collected_data,
            content_plan=self.content_plan,
            revision_history=history,
        )

        self.captions[variation_index] = refined

        # Re-run validation with updated captions
        self.validation_result = validation_agent(
            self.collected_data.get("platform", "Instagram"),
            self.captions,
            self.image_result,
        )

        return {
            "captions": self.captions,
            "validation": self.validation_result,
            "revision_history": {key: history},
        }

    def refine_image(self, feedback: str) -> dict[str, Any]:
        """
        Refines the image by updating the generation prompt and calling DALL-E again.

        Args:
            feedback: user's natural language change request for the image

        Returns updated image_result.
        """
        if self.phase != "complete":
            raise ValueError("Run the content pipeline first.")

        history = self.revision_histories.setdefault("image", [])
        current_prompt = self.image_result.get("prompt_used", "")

        # Save current image to history
        history.append(self.image_result.copy())

        revised_prompt = refine_image_prompt(
            current_prompt=current_prompt,
            feedback=feedback,
            collected_data=self.collected_data,
            content_plan=self.content_plan,
            revision_history=history,
        )

        # Generate new image with revised prompt
        from agents.image_agent import _call_image_generation_api
        new_image = _call_image_generation_api(revised_prompt)
        new_image["mode"] = "generate"
        self.image_result = new_image

        # Re-run validation
        self.validation_result = validation_agent(
            self.collected_data.get("platform", "Instagram"),
            self.captions,
            self.image_result,
        )

        return {
            "image": self.image_result,
            "validation": self.validation_result,
            "revision_history": {"image": history},
        }

    def _build_output(self) -> dict[str, Any]:
        """Assembles the final output package."""
        return {
            "phase": self.phase,
            "collected_data": self.collected_data,
            "content_plan": self.content_plan,
            "captions": self.captions,
            "image": self.image_result,
            "validation": self.validation_result,
            "revision_histories": self.revision_histories,
        }


# ---------------------------------------------------------------------------
# Convenience function for testing without the HTTP layer
# ---------------------------------------------------------------------------

def run_full_session_interactive() -> None:
    """CLI walkthrough — for manual testing."""
    orchestrator = MarketingOrchestrator()

    print("=== Marketing Content Generator ===")
    print("Type your message to start. The assistant will guide you.\n")

    # Chat phase
    while orchestrator.phase == "chat":
        user_input = input("You: ").strip()
        if not user_input:
            continue

        turn = orchestrator.run_chat_turn(user_input)
        print(f"\nAssistant: {turn['reply']}\n")

        if turn["phase"] == "pipeline_ready":
            print("\n[All data collected! Running content pipeline...]\n")
            break

    # Image upload prompt (CLI only)
    image_b64 = None
    media_type = "image/jpeg"
    upload_path = input("Enter image path to upload (or press Enter to skip): ").strip()
    if upload_path:
        import base64
        with open(upload_path, "rb") as f:
            image_b64 = base64.b64encode(f.read()).decode()
        if upload_path.lower().endswith(".png"):
            media_type = "image/png"

    # Pipeline
    result = orchestrator.run_content_pipeline(image_b64, media_type)

    print("\n=== CONTENT PLAN ===")
    for k, v in result["content_plan"].items():
        print(f"  {k}: {v}")

    print("\n=== CAPTIONS ===")
    for cap in result["captions"]:
        print(f"\n--- {cap['label']} ---")
        print(f"Hook: {cap['hook']}")
        print(f"Caption ({cap['char_count']} chars):\n{cap['caption']}")

    print("\n=== IMAGE ===")
    img = result["image"]
    print(f"  Mode: {img['mode']}")
    if img["mode"] == "analyse":
        for k, v in img["analysis"].items():
            print(f"  {k}: {v}")
    else:
        print(f"  Prompt used: {img.get('prompt_used', '')[:120]}...")
        if img.get("note"):
            print(f"  Note: {img['note']}")


if __name__ == "__main__":
    run_full_session_interactive()
