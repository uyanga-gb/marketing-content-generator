# Marketing Content Generator — Multi-Agent AI System

A multi-agent AI pipeline that turns a conversation into a complete social media content package. Built with FastAPI, React, and the Anthropic Claude API.

```
User ──► Chat Agent ──► Planner Agent ──► Caption Agent ──► Image Agent
          (collect)       (strategy)      (3 variations)    (analyse/gen)
```

## Live Demo (AWS Deployment)

| Component | URL |
|-----------|-----|
| **Frontend** | http://capstone-frontend-088441258688.s3-website-us-east-1.amazonaws.com |
| **Backend API** | http://54.147.163.175:8000 |
| **Health Check** | http://54.147.163.175:8000/health |

## Architecture

### Agent Pipeline

| Agent | File | Role |
|-------|------|------|
| Chat Agent | `backend/agents/chat_agent.py` | Multi-turn conversation; collects product, platform, image availability |
| Planner Agent | `backend/agents/planner_agent.py` | Decides post format, tone, key messages, and CTA |
| Caption Agent | `backend/agents/caption_agent.py` | Generates 3 caption variations via Claude (uses adaptive thinking) |
| Image Agent | `backend/agents/image_agent.py` | Analyses uploaded image with Claude Vision OR generates a new one |
| Refinement Agent | `backend/agents/refinement_agent.py` | Refines captions and images based on user feedback |
| Validation Agent | `backend/agents/validation_agent.py` | Quality validation of generated content |
| Orchestrator | `backend/orchestrator.py` | Coordinates the pipeline; holds session state |
| API Server | `backend/main.py` | FastAPI HTTP layer for the React frontend |

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, Create React App |
| Backend | Python 3.11, FastAPI, Uvicorn |
| AI | Anthropic Claude API (claude-sonnet-4-6) |
| Image Generation | OpenAI DALL-E (optional) |
| Deployment | AWS EC2 (t2.micro) + S3 Static Hosting |

### AWS Deployment Architecture

```
Browser
  │
  ▼
S3 Static Website (React Build)
  │  (API calls)
  ▼
EC2 t2.micro — FastAPI + Uvicorn (port 8000)
  │
  ├── Anthropic Claude API  (captions, planning, chat)
  └── OpenAI DALL-E API     (image generation, optional)
```

## Project Structure

```
capstone_project1/
├── backend/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── chat_agent.py         # Multi-turn conversation agent
│   │   ├── planner_agent.py      # Content strategy agent
│   │   ├── caption_agent.py      # Caption generation agent
│   │   ├── image_agent.py        # Image analysis/generation agent
│   │   ├── refinement_agent.py   # Refinement agent
│   │   └── validation_agent.py   # Validation agent
│   ├── main.py                   # FastAPI server
│   ├── orchestrator.py           # Pipeline orchestrator
│   ├── test_pipeline.py          # Integration tests
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── public/
    │   └── index.html
    └── src/
        ├── App.jsx
        ├── index.js
        ├── components/
        │   ├── ChatInterface.jsx
        │   ├── ContentPreview.jsx
        │   └── ImagePreview.jsx
        └── services/
            └── api.js
```

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)
- (Optional) An OpenAI API key for DALL-E image generation

### Backend

```bash
cd backend

# Create and activate virtual environment
python3.11 -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY (and optionally OPENAI_API_KEY)

# Run integration test (no UI needed)
python test_pipeline.py

# Start the API server
python main.py
# Server runs at http://localhost:8000
```

### Frontend

```bash
cd frontend
npm install
npm start          # Opens http://localhost:3000
```

The React dev server proxies API calls to `http://localhost:8000` automatically.

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/session/start` | Create a new session |
| `POST` | `/session/{id}/chat` | Send a chat message to the chat agent |
| `POST` | `/session/{id}/generate` | Run the full content pipeline (optional image upload) |
| `GET` | `/session/{id}/result` | Retrieve completed pipeline results |
| `POST` | `/session/{id}/refine/caption` | Refine a caption variation with feedback |
| `POST` | `/session/{id}/refine/image` | Regenerate image with feedback |

## How It Works

1. **Chat Phase** — The Chat Agent collects product details, target platform, tone, and whether an image is available through a multi-turn conversation.
2. **Planning Phase** — The Planner Agent analyses the collected data and decides the optimal post format, tone, key messages, and call-to-action.
3. **Caption Generation** — The Caption Agent generates 3 distinct caption variations using Claude with adaptive thinking.
4. **Image Handling** — If an image was uploaded, the Image Agent analyses it with Claude Vision. Otherwise, it generates a prompt for DALL-E.
5. **Validation & Refinement** — Results are validated and users can refine individual captions or the image with feedback.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key from [console.anthropic.com](https://console.anthropic.com/) |
| `OPENAI_API_KEY` | No | OpenAI API key for DALL-E image generation |

## AWS Deployment Guide

This project is deployed on AWS using EC2 (backend) and S3 (frontend).

### Prerequisites
- AWS CLI configured with appropriate permissions
- An EC2 key pair

### Steps

1. **Store secrets in SSM Parameter Store**
   ```bash
   aws ssm put-parameter --name "/capstone/ANTHROPIC_API_KEY" --value "your-key" --type SecureString --region us-east-1
   ```

2. **Deploy backend to EC2**
   ```bash
   # Package code (exclude .env and .venv)
   zip -r backend.zip backend/ --exclude "backend/.env" --exclude "backend/.venv/*"
   # Upload to S3 and launch EC2 t2.micro with user data script
   ```

3. **Deploy frontend to S3**
   ```bash
   cd frontend
   npm run build
   aws s3 sync build/ s3://your-bucket/ --region us-east-1
   ```

4. **Enable S3 static website hosting** and set bucket policy for public read access.
