# GenChat - Paul Corsino's Reusable General AI Assistant Starter Kit

A production-ready, modular, full-stack AI agent application template designed by Paul Corsino. GenChat features real-time token streaming (SSE), collapsible thought timelines, sequential activity badges, tool calling, and file attachment handling.

Built to serve as a clean, reusable foundation for future AI chat projects.

---

## Architecture Overview

```
genchat/
├── backend/                       # FastAPI + LangChain Agent
│   ├── app/
│   │   ├── routers/
│   │   │   ├── chat.py            # POST /api/chat/stream (SSE streaming)
│   │   │   └── upload.py          # POST /api/files/upload & GET /download
│   │   ├── schemas/chat.py        # Typed SSE event definitions
│   │   ├── services/
│   │   │   ├── agent_service.py   # Multi-turn LangChain agent with sequential activities
│   │   │   └── tool_executor.py   # Modular tool execution & deduplication
│   │   ├── tools/                 # Pluggable LangChain tools
│   │   └── prompts/agent.py       # System prompt & agent instructions
│   └── requirements.txt
│
└── frontend/                      # Next.js 16 (App Router) + Tailwind + Zustand
    ├── src/
    │   ├── app/                   # Full-screen responsive chat layout
    │   ├── features/chat/
    │   │   ├── components/        # ChatWindow, ChatInput, ExecutionTimeline, ChatMessage
    │   │   ├── hooks/useChat.ts   # Stream controller & execution timer
    │   │   ├── store/chat.store.ts# Message state & attached files store
    │   │   └── services/          # SSE stream reader
    │   └── shared/api/stream.ts   # Decoupled SSE event parser
    └── package.json
```

---

## Quickstart

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Open .env and add your GEMINI_API_KEY

# Start API server
uvicorn app.main:app --port 8000 --reload
```

Backend will be running at `http://localhost:8000`. Test the health check at `http://localhost:8000/health`.

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start Next.js development server
npm run dev
```

Frontend will be running at `http://localhost:3000`.

---

## Git Repository Setup

To initialize and connect to GitHub:

```bash
cd /Users/paulcorsino/Documents/GitHub/genchat
git init
git add .
git commit -m "Initial commit of GenChat"

# Connect to your GitHub remote:
# git remote add origin https://github.com/your-username/genchat.git
# git push -u origin main
```

---

## Features & Highlights

1. **Real-time Server-Sent Events (SSE)**: Streams tokens chunk-by-chunk using LangChain's `astream_events(version="v2")`.
2. **Sequential Activity Timeline**: Real-time status badges with activity lifecycle events that indicate when tools are executing.
3. **Collapsible Thought Duration**: Displays *"Thought for X.X seconds"* with expandable execution history.
4. **Modular Tool Architecture**: Pluggable tool executor designed to easily drop in custom tools for future projects.
5. **File Attachments**: Built-in file upload and download endpoints.
6. **No Database Required to Start**: Pure stateless session mode. Can easily plug in MongoDB / PostgreSQL whenever persistent chat history is needed.
