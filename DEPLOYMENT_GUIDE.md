# Deployment Guide — Marketing Content Generator

A detailed walkthrough of how this app was deployed to AWS, written for frontend engineers who are new to cloud deployment.

---

## The Big Picture: What Does "Deploying to AWS" Mean?

When you run your app locally, it lives entirely on your laptop:
- `npm start` runs the React app at `localhost:3000`
- `python main.py` runs the API at `localhost:8000`
- Both disappear the moment you close your terminal

**Deploying** means moving your app to computers that run 24/7 in Amazon's data centers, so anyone with a browser can access it — not just you.

AWS (Amazon Web Services) is essentially a massive collection of on-demand services. Instead of buying your own servers, you rent exactly what you need and pay only for usage.

---

## Our App Has Two Parts — Each Needs Its Own Home

```
Your App
├── Frontend  (React)   → Static files: HTML, CSS, JavaScript
└── Backend   (Python)  → A running server that executes code
```

These two parts have very different needs:

| | Frontend | Backend |
|--|----------|---------|
| What it is | HTML/CSS/JS files | A live Python process |
| Needs a server? | No — just file hosting | Yes — must run 24/7 |
| AWS service used | **S3** | **EC2** |

---

## AWS Services Involved

### 1. Amazon EC2 — Elastic Compute Cloud
> "A computer you rent in the cloud"

EC2 gives you a virtual machine — essentially a computer running in Amazon's data center. You choose the operating system (we used Amazon Linux), the size (we used `t2.micro`, 1 CPU + 1GB RAM), and it stays on 24/7.

This is where the Python/FastAPI backend runs.

### 2. Amazon S3 — Simple Storage Service
> "A hard drive in the cloud, that can also serve websites"

S3 is normally used to store files (images, backups, etc.). But it has a feature called **Static Website Hosting** — when turned on, S3 serves your HTML/CSS/JS files directly to browsers, acting like a simple web server. No Python or Node needed.

This is where the React frontend lives after `npm run build`.

### 3. AWS SSM Parameter Store — Systems Manager
> "A secure vault for secrets like API keys"

Instead of hardcoding your `ANTHROPIC_API_KEY` into the code (which would be dangerous if pushed to GitHub), we stored it in SSM Parameter Store. It's like a secure password manager built into AWS. The EC2 server fetches the key when it starts up.

### 4. AWS IAM — Identity and Access Management
> "The permission system that controls who can do what"

IAM is AWS's security layer. Every action in AWS requires permission. We created an **IAM Role** for the EC2 instance that says:
- "This EC2 machine is allowed to read secrets from SSM"
- "This EC2 machine is allowed to download files from S3"

Without this role, the EC2 machine would be blocked from accessing those services.

### 5. Security Groups
> "A firewall for your EC2 instance"

By default, an EC2 instance blocks all incoming traffic. A Security Group is a set of rules that opens specific ports. We opened:

| Port | Purpose |
|------|---------|
| 22 | SSH — so we can connect and manage the server |
| 80 | HTTP — standard web traffic |
| 8000 | Our FastAPI backend API |

---

## Step-by-Step: How the Deployment Happened

### Step 1 — Store API Keys Securely in SSM

Before touching any servers, we stored the API keys in AWS:

```
Your .env file (local, never pushed to GitHub)
    ANTHROPIC_API_KEY=sk-ant-...
    OPENAI_API_KEY=sk-...
         │
         ▼
AWS SSM Parameter Store
    /capstone/ANTHROPIC_API_KEY  (encrypted, SecureString)
    /capstone/OPENAI_API_KEY     (encrypted, SecureString)
```

The keys are now safely stored in AWS. The EC2 server will fetch them at startup — your actual key values never appear in any code file or GitHub repo.

---

### Step 2 — Create a Security Group (Firewall Rules)

We created a Security Group that allows:
- Port 22 → SSH access (so we can log in and manage the server)
- Port 80 → HTTP web traffic
- Port 8000 → Our FastAPI API

Think of it like configuring which doors are unlocked on the building.

---

### Step 3 — Create an IAM Role for EC2

We created a Role (a set of permissions) and attached it to the EC2 instance. This role says:

> "The machine running this app is allowed to:
> - Read secrets from SSM Parameter Store
> - Download files from our S3 bucket"

Without this, when the EC2 machine tries to fetch your API key from SSM, AWS would respond: `Access Denied`.

---

### Step 4 — Package the Backend Code

We zipped the backend Python code (excluding `.env`, `__pycache__`, and the virtual environment):

```
backend/
├── agents/          ✅ included
├── main.py          ✅ included
├── orchestrator.py  ✅ included
├── requirements.txt ✅ included
├── .env             ❌ excluded (contains secrets)
└── .venv/           ❌ excluded (too large, reinstalled on server)
```

The zip was uploaded to S3 so the EC2 instance could download it.

---

### Step 5 — Launch the EC2 Instance

We launched a `t2.micro` EC2 instance (Amazon Linux 2023) with a **User Data script**.

User Data is a shell script that runs automatically the first time an EC2 instance boots. It's how you automate server setup without logging in manually. Ours did the following automatically on first boot:

```
EC2 boots for the first time
        │
        ▼
1. Install Python 3.11
        │
        ▼
2. Download backend.zip from S3
        │
        ▼
3. Unzip the backend code
        │
        ▼
4. Create a Python virtual environment
        │
        ▼
5. pip install -r requirements.txt
        │
        ▼
6. Fetch API keys from SSM Parameter Store → write to .env
        │
        ▼
7. Register FastAPI as a system service (so it auto-starts)
        │
        ▼
8. Start the FastAPI server on port 8000
```

After this, the backend is live at `http://<EC2-IP>:8000`.

---

### Step 6 — Fix Python Version Compatibility

Amazon Linux comes with Python 3.9 by default. Our code uses `str | None` syntax (union types) which requires **Python 3.10+**. So we installed Python 3.11 on the EC2 instance and rebuilt the virtual environment with it.

This is a common real-world issue — the Python version on the server must match what the code was written for.

---

### Step 7 — Register the Server as a System Service

We registered the FastAPI app as a **systemd service**. Systemd is Linux's process manager — it controls what programs start automatically and restarts them if they crash.

The service file we created tells Linux:
- Run `uvicorn main:app --host 0.0.0.0 --port 8000`
- As the `ec2-user` user
- Load environment variables from `.env`
- Restart automatically if it crashes
- Start on every system reboot

This means the backend keeps running even if no one is SSH'd into the server.

---

### Step 8 — Update CORS in the Backend

CORS (Cross-Origin Resource Sharing) is a browser security rule. When your React app (served from S3) makes API calls to the FastAPI server (running on EC2), the browser checks: "Is this server allowing requests from this origin?"

We updated `main.py` to explicitly allow the S3 website URL:

```python
# Before (only localhost was allowed)
allow_origins=["http://localhost:3000"]

# After (S3 URL added)
allow_origins=[
    "http://localhost:3000",
    "http://capstone-frontend-088441258688.s3-website-us-east-1.amazonaws.com",
]
```

Without this change, the browser would block all API calls with a CORS error — even though the server is running fine.

---

### Step 9 — Build the React Frontend

```bash
npm run build
```

This command compiles your React app into plain static files:

```
frontend/build/
├── index.html              ← the single HTML file
├── static/
│   ├── js/main.xxx.js      ← all your React components, bundled + minified
│   └── css/main.xxx.css    ← all your styles
└── asset-manifest.json
```

These files have zero dependencies — no Node, no npm, no React runtime needed. Any web server (including S3) can serve them.

---

### Step 10 — Update the Frontend API URL

In development, the React app talks to the backend via a proxy (`localhost:8000`). In production, it needs to talk to the real EC2 server.

```js
// frontend/src/services/api.js

// Before (local development)
const BASE = "";  // proxied to localhost:8000 by Create React App

// After (production — points to EC2)
const BASE = "http://54.147.163.175:8000";
```

This change was made before running `npm run build`, so the production bundle contains the correct EC2 address.

---

### Step 11 — Deploy Frontend to S3

We created an S3 bucket, enabled Static Website Hosting, and set a public read policy so anyone can access the files:

```bash
# Upload the build folder to S3
aws s3 sync frontend/build/ s3://capstone-frontend-088441258688/
```

S3 then serves `index.html` as the homepage of the website. When a user visits the S3 URL, S3 returns that HTML file, which loads the JavaScript bundle, which boots your React app in the browser.

---

## How It All Connects — The Full Flow

```
User types the URL in browser
           │
           ▼
  S3 Static Website
  Returns index.html + main.js
           │
           │  React app boots in the browser
           │
           ▼
  User chats / fills in details
           │
           │  JavaScript fetch() call
           ▼
  EC2 Instance (54.147.163.175:8000)
  FastAPI receives the request
           │
           ├──► Chat Agent (Claude API)
           ├──► Planner Agent (Claude API)
           ├──► Caption Agent (Claude API)
           └──► Image Agent (Claude Vision / DALL-E)
                      │
                      ▼
           Response sent back to browser
                      │
                      ▼
           React renders the generated content
```

---

## What Stays Where

| Item | Location |
|------|----------|
| React app (UI) | S3 bucket (static website) |
| FastAPI server | EC2 instance, running as a system service |
| API keys | AWS SSM Parameter Store (encrypted) |
| Backend code | EC2 instance at `/home/ec2-user/backend/` |
| SSH key | Your Mac at `~/.ssh/capstone-key.pem` |

---

## Useful Commands

### SSH into the EC2 server
```bash
ssh -i ~/.ssh/capstone-key.pem ec2-user@54.147.163.175
```

### View live backend logs
```bash
ssh -i ~/.ssh/capstone-key.pem ec2-user@54.147.163.175 \
  "sudo journalctl -u capstone -f"
```

### Restart the backend after a code change
```bash
# 1. Copy the updated file to EC2
scp -i ~/.ssh/capstone-key.pem backend/main.py ec2-user@54.147.163.175:/home/ec2-user/backend/

# 2. Restart the service
ssh -i ~/.ssh/capstone-key.pem ec2-user@54.147.163.175 \
  "sudo systemctl restart capstone"
```

### Redeploy the frontend after a change
```bash
cd frontend
npm run build
aws s3 sync build/ s3://capstone-frontend-088441258688/ --region us-east-1 --delete
```

---

## Live URLs

| | URL |
|-|-----|
| **Frontend** | http://capstone-frontend-088441258688.s3-website-us-east-1.amazonaws.com |
| **Backend API** | http://54.147.163.175:8000 |
| **Health Check** | http://54.147.163.175:8000/health |
