# Presentation Script — Marketing Content Generator
### Agentic AI Capstone Project Demo
**Estimated time: 15–20 minutes**

---

## SLIDE 1 — Opening (1 minute)

> "Good [morning/afternoon] everyone. Today I'm presenting my capstone project: a **multi-agent AI system that generates complete, ready-to-post social media content** — from a simple conversation to a validated image-and-caption package, in under two minutes.
>
> It's a pipeline of **six specialized AI agents**, each with a clear job, coordinated by a central orchestrator


> Let me show you how it works."

---

## SLIDE 2 — Problem Statement (1 minute)

> "Creating professional social media content is time-consuming. A marketer needs to:
> - Decide the right format for the platform
> - Write multiple caption variations
> - Source or generate an on-brand image
> - Check that everything meets platform guidelines
>
> This normally takes hours and requires multiple tools. My system compresses all of that into a **single guided conversation** — using agents that each specialize in one piece of the problem."

---

## SLIDE 3 — System Architecture Overview (2 minutes)

> "Here's the full pipeline. Six agents, running in sequence:"

```
User
 │
 ▼
[1] Chat Agent          → Collects product details through conversation
 │
 ▼
[2] Planner Agent       → Decides post format, tone, key messages
 │
 ▼
[3] Caption Agent       → Generates 3 caption variations
 │
 ▼
[4] Image Agent         → Analyses uploaded image OR generates one
 │
 ▼
[5] Validation Agent    → Checks platform guidelines
 │
 ▼
[6] Refinement Agent    → Iterates on any output based on feedback
 │
 ▼
Ready-to-Post Package
```

> "Each agent has a **single responsibility**, a **clear input/output contract**, and can be swapped or reused independently. This is the core principle of modular agentic design.
>
<!-- > All agents sit behind a **FastAPI backend** and are coordinated by a **stateful orchestrator class**. The user interacts through a **React frontend** — but the same agents could be called from any system." -->

---

## SLIDE 4 — Tech Stack (30 seconds)

| Layer | Technology |
|-------|-----------|
| LLM | GPT-4o (OpenAI) |
| Image Generation | DALL-E 3 |
| Backend | Python + FastAPI |
| Frontend | React |
| Agent Coordination | Custom Python Orchestrator |
| Image Validation | Pillow (PIL) |

> "Entirely Python on the backend. No LangChain, no AutoGen — the orchestration logic is hand-written, so we have full control over every decision point."

---
Engineering Decisions
Four deliberate architectural choices


## SLIDE 5 — LIVE DEMO: Start Here (2 minutes)

<!-- > "Let me run the live demo. I have the backend server running on port 8000 and the React app on port 3000." -->

**[Open browser → localhost:3000]**

> "You can see the two-column layout. On the left, the chat interface. On the right, where the results will appear.
>
> This is the opening message from the **Chat Agent** — notice how it's already acting like a creative director, not just asking for a form fill."

---

## SLIDE 6 — Agent 1: Chat Agent (2 minutes)

**[Demo: have a short conversation — type something like "I sell handmade soy candles"]**

> "Let's talk about what's happening technically.
>
> The Chat Agent uses **GPT-4o** with a carefully designed system prompt. It's not a simple form — it's a genuine multi-turn conversation. The system prompt tells the model to:
> - Act as a creative marketing director
> - Ask 1–2 questions at a time — never overwhelming the user
> - Build on previous answers with vivid, specific language
> - Offer options when the user is unsure
>
> I collect **six pieces of information**: product type, platform, image availability, mood and style, target audience, and visual theme.
>
<!-- > The key technical trick: when all six fields are confirmed, the model outputs a special XML block — `<collected_data>` — containing a JSON object. My backend **parses this tag** to know when the conversation is complete and extraction should happen. The frontend strips this tag and shows a friendly completion message instead." -->

**[Show the chat reaching the "pipeline ready" state]**

---

## SLIDE 7 — Agent 2: Planner Agent (1 minute)

> "Once I have the collected data, I click Generate. The orchestrator immediately runs the next three agents in sequence.
>
> First — the **Planner Agent**. It receives the collected data and outputs a structured content strategy.
>
<!-- > Technically: I use OpenAI's `response_format: json_object` parameter — this is **structured output mode**, which guarantees the model returns valid JSON every time. No parsing errors, no markdown fences to strip. -->
>
> The plan includes: post format (carousel, single image, video script, text-only), tone, three key messages, a hashtag strategy, a CTA, and a platform-specific tip."

**[Show the Content Plan card on the right side]**

---

## SLIDE 8 — Agent 3: Caption Agent (2 minutes)

> "Next — the **Caption Agent**. This is where the creative writing happens.
>
> I generate **three distinct variations** simultaneously — not just three versions of the same caption, but three fundamentally different angles:
> - **Variation A** — Emotion and storytelling
> - **Variation B** — Features and benefits
> - **Variation C** — Social proof, urgency, FOMO
>
<!-- > Technically, I use **custom delimiter parsing** — the model outputs blocks like `---VARIATION_A---` and `---END_A---`. My parser extracts the hook line and full caption body from each block. This is more robust than asking for JSON when the content itself contains special characters like quotes and hashtags. -->
>
<!-- > Each caption comes with: the opening hook (max 15 words), the full body with hashtags, and a character count." -->

**[Show the tabbed captions view — click through A, B, C]**

---

## SLIDE 9 — Agent 4: Image Agent (2 minutes)

> "The **Image Agent** handles two completely different scenarios with the same interface.
>
> **Scenario 1 — User uploads an image:**
> I send the base64-encoded image to **GPT-4o Vision** along with the content plan as context. The model returns: an image assessment, overlay text suggestions, crop recommendations for the target platform, a color palette in hex codes, and SEO alt text.
>
> **Scenario 2 — No image:**
> First, GPT-4o writes a detailed **image generation prompt** — up to 200 words describing the scene, lighting, composition, and mood. Then that prompt is sent to **DALL-E 3**, which returns a 1024x1024 image.
>
> GPT-4o understands the marketing context and product strategy — it writes a much better prompt than any human would type directly into an image generator."

**[Show the image result — either analysis cards or generated image]**

---

## SLIDE 10 — Agent 5: Validation Agent (2 minutes)

<!-- > "Now the part that makes this production-ready — the **Validation Agent**. -->
>
> This agent uses **no LLM at all**. It's pure Python logic, which is an important design choice. For deterministic rule-checking — things like character limits or file sizes — you don't want a model that might hallucinate a number. I want to have hard rules.
>
> It checks:

**Captions:**
> - Character count against the platform's hard limit (Instagram: 2,200 / Twitter: 280 / LinkedIn: 3,000)
> - Whether the caption exceeds the above-the-fold cutoff (125 chars for Instagram)
> - Hashtag count against platform maximums (Instagram: 30 / Twitter: 2)

**Images:**
> - Minimum resolution using **Pillow** to inspect actual pixel dimensions Pillow is a Python image processing library. In this project it's used purely as an image inspector — we never draw or edit anything, we just open the image and read its metadata.
> - File size (max 8MB for Instagram)
> - Aspect ratio (Instagram enforces between 4:5 portrait and 1.91:1 landscape)
> - Format compatibility

> Finally, it **auto-selects the best caption** — the one closest to the recommended length — and assembles the **ready-to-post package**: caption + image, ready to copy and upload."

**[Show the Validation card — green banner if passing]**

---

## SLIDE 11 — Agent 6: Refinement Agent + Feedback Loop (2 minutes)

<!-- > "This is my favourite feature — the **feedback loop**. -->
>
> After seeing the results, the user can iterate on any caption or image using natural language. Watch this."

**[Demo: click "✦ Refine this caption" on Variation A, type "Make it shorter and punchier" or click the quick chip]**

> "Here's what happens technically:
> 1. The current caption and user feedback go to the **Refinement Agent** (GPT-4o)
> 2. The system prompt tells it to apply the feedback precisely — changing what was asked, keeping what wasn't
> 3. The response is parsed, the caption is updated, and a **revision number** is incremented (v2, v3...)
> 4. The **Validation Agent re-runs automatically** on the updated content
> 5. The previous version is saved to a **revision history** — the user can expand it to compare
>
> For images, the same loop works but ends with a new DALL-E 3 call.
>
> Quick-prompt chips like 'Make it shorter' or 'More dramatic lighting' make this instant — no typing required."

**[Show revision history expanding]**

---

## SLIDE 17 — Closing (30 seconds)

> "To summarize: I built a six-agent pipeline that takes a user from a blank slate to a validated, ready-to-post social media package through natural conversation. Each agent has a single responsibility, clean interfaces, and can be reused or replaced without touching the rest of the system.
>
> The project demonstrates multi-agent orchestration, structured LLM outputs, human-in-the-loop refinement, and deterministic validation — all the core patterns of production agentic AI systems.







## SLIDE 12 — Orchestrator: The Coordination Layer (1 minute)

> "Let me show you the architecture that ties all of this together — the **MarketingOrchestrator** class.

```python
class MarketingOrchestrator:
    def run_chat_turn(self, user_message)      # Phase 1
    def run_content_pipeline(self, image=None) # Phase 2–5
    def refine_caption_variation(self, i, fb)  # Feedback loop
    def refine_image(self, feedback)            # Feedback loop
```

> The orchestrator holds **all session state**: conversation history, collected data, content plan, captions, image result, validation result, and revision histories.
>
> Phase transitions are explicit: `chat` → `pipeline_ready` → `complete`. The API layer enforces these — if you try to refine before generating, you get a clear error.
>
> Each user session gets its own orchestrator instance, identified by a UUID. In production, these would live in a database or Redis — right now they're in-memory for the demo."

---

## SLIDE 13 — API Layer (30 seconds)

> "The FastAPI backend exposes seven endpoints:"

| Endpoint | Purpose |
|----------|---------|
| `POST /session/start` | Create session, return UUID |
| `POST /session/{id}/chat` | One chat turn |
| `POST /session/{id}/generate` | Run full pipeline |
| `GET /session/{id}/result` | Retrieve cached result |
| `POST /session/{id}/refine/caption` | Refine a caption variation |
| `POST /session/{id}/refine/image` | Regenerate the image |
| `GET /health` | Health check |

> "Clean REST design — each endpoint maps to exactly one orchestrator method. The React frontend calls these via the `api.js` service layer."

---

## SLIDE 14 — Key Engineering Decisions (2 minutes)

> "Let me highlight four architectural decisions I made deliberately."

**1. One agent = one responsibility**
> "Each agent does exactly one thing. The Planner doesn't write captions. The Caption agent doesn't validate. This makes each agent independently testable and reusable in other projects."

**2. Validation without LLMs**
> "The Validation Agent uses zero AI. Platform rules are deterministic — a caption is either over 2,200 characters or it isn't. Using an LLM for this would be slower, more expensive, and potentially wrong."

**3. Structured output strategies vary by agent**
> "I used three different structured output approaches:
> - `response_format: json_object` for the Planner (strict JSON)
> - Custom delimiters (`---VARIATION_A---`) for the Caption Agent (content contains special chars)
> - XML tags (`<collected_data>`) for the Chat Agent (embedded in conversational text)"

**4. Two-step image generation**
> "I don't send a raw user description to DALL-E. I first ask GPT-4o to write a professional prompt enriched with the product strategy and platform context. The resulting images are significantly better."

---

## SLIDE 15 — Agentic AI Concepts Demonstrated (1 minute)

> "This project demonstrates the core concepts from our course:"

| Concept | Where Used |
|---------|-----------|
| **Multi-agent orchestration** | 6 agents coordinated by orchestrator |
| **Agent specialization** | Each agent has a single, focused role |
| **Tool use** | DALL-E 3, GPT-4o Vision as agent tools |
| **Structured outputs** | JSON mode, XML parsing, delimiter parsing |
| **State management** | Session-based stateful orchestrator |
| **Human-in-the-loop** | Feedback loop / refinement cycle |
| **Validation layer** | Rule-based guardrails post-generation |
| **Modular design** | Agents are independently reusable |

---

## SLIDE 16 — What I Would Add Next (30 seconds)

> "If I were taking this to production, the next steps would be:
> 1. **Message queue** between agents (RabbitMQ/Redis) so each agent runs as an independent microservice
> 2. **Persistent sessions** in a database — right now sessions disappear when the server restarts
> 3. **Real image upload to a CDN** — DALL-E URLs expire after one hour
> 4. **Expanded platform support** — TikTok video scripts, Pinterest boards
> 5. **A/B testing feedback** — track which caption variation gets the most engagement and feed that back into the planner"

---


>
> Thank you — I'm happy to take questions or do a deeper dive into any part of the architecture."

---

## Q&A CHEAT SHEET

**Q: Why not use LangChain or AutoGen?**
> "I wanted full transparency and control over every agent decision. Hand-written orchestration means I can see exactly what's happening at each step — no black boxes. It also helped me understand the patterns more deeply."

**Q: How do you handle errors mid-pipeline?**
> "Right now, a failure in any agent raises a Python exception that the FastAPI layer returns as a 500 error. In production, I'd add retry logic with exponential backoff for the LLM calls and graceful degradation — for example, if the image agent fails, still return the captions."

**Q: Can this work with Claude or other models?**
> "Yes — the original version was built with Claude (claude-opus-4-6). The agent logic is model-agnostic; you just swap the client initialization and the API call format. I switched to GPT-4o to use an existing API key."

**Q: How much does one run cost?**
> "A full pipeline run uses roughly 3,000–5,000 input tokens and 1,500 output tokens across all LLM agents, plus one DALL-E 3 call ($0.04). Total cost per run is roughly $0.08–$0.12 — well under 15 cents."

**Q: What makes this 'agentic' vs. just a series of API calls?**
> "Three things: each agent has autonomous decision-making within its domain, agents can be iterated on via the feedback loop without restarting the pipeline, and the orchestrator manages state and transitions between agents — it decides when to move forward and what data to pass. That's the core of agentic design."

---

*Script prepared for Agentic AI capstone presentation — March 2026*
