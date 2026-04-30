---
title: Whisper Backend
emoji: ⚡
colorFrom: blue
colorTo: red
sdk: docker
pinned: false
---

# Whisper AI

> *"Fully Responsive Intelligent Digital Assistant for You"*

A Tony Stark-inspired AI assistant split into two cooperating pieces:

| Component | What it is |
|-----------|-----------|
| **MCP Server** (`uv run whisper`) | A [FastMCP](https://github.com/jlowin/fastmcp) server that exposes tools (news, web search, system info, …) over SSE. It acts as Whisper's tool backend. |
| **Voice Agent** (`uv run whisper_voice`) | A [LiveKit Agents](https://github.com/livekit/agents) voice pipeline that listens to your microphone, reasons with an LLM, and speaks back while pullin[...]  

Demo: [Instagram reel](https://www.instagram.com/p/DW2HjYtkwg_/)  

[![Demo Video Guide](https://img.youtube.com/vi/mMY9swqe3BI/maxresdefault.jpg)](https://www.youtube.com/watch?v=mMY9swqe3BI)

---

## How it works

```
Microphone ──► STT (Sarvam Saaras v3)
                     │
                     ▼
              LLM (Gemini 2.5 Flash)  ◄──────► MCP Server (FastMCP / SSE)
                     │                              ├─ get_world_news
                     ▼                              ├─ open_world_monitor
              TTS (OpenAI nova)                     ├─ search_web
                     │                              └─ …more tools
                     ▼
              Speaker / LiveKit room
```

The voice agent connects to the MCP server via SSE at `http://127.0.0.1:8000/sse` (auto-resolved to the Windows host IP when running inside WSL).

---

## Project structure

```
Whisper_AI/
├── server.py           # uv run whisper  → starts the MCP server (SSE on :8000)
├── whisper_agent.py    # uv run whisper_voice → starts the LiveKit voice agent
├── pyproject.toml
├── .env.example        # copy → .env and fill in your keys
│
└── whisper/            # MCP server package
    ├── config.py       # env-var loading & app-wide settings
    ├── tools/          # MCP tools (callable by the LLM)
    │   ├── web.py      # search_web, fetch_url, get_world_news, open_world_monitor
    │   ├── system.py   # get_current_time, get_system_info
    │   └── utils.py    # format_json, word_count
    ├── prompts/        # MCP prompt templates (summarize, explain_code, …)
    └── resources/      # MCP resources exposed to clients (whisper://info)
```

---

## Quick start

### 1. Prerequisites

- Python ≥ 3.11
- [`uv`](https://github.com/astral-sh/uv) — `pip install uv` or `curl -Lsf https://astral.sh/uv/install.sh | sh`
- A [LiveKit Cloud](https://cloud.livekit.io) project (free tier works)

### 2. Clone & install

```bash
git clone <your-repo-url>
cd Whisper_AI
uv sync          # creates .venv and installs all dependencies
```

### 3. Set up environment

```bash
cp .env.example .env
# Open .env and fill in your API keys (see the section below)
```

### 4. Run — two terminals

**Terminal 1 — MCP server** (must start first)

```bash
uv run whisper
```

Starts the FastMCP server on `http://127.0.0.1:8000/sse`. The voice agent connects here to fetch its tools.

**Terminal 2 — Voice agent**

```bash
uv run whisper_voice
```

Starts the LiveKit voice agent in **dev mode** — it joins a LiveKit room and begins listening. Open the [LiveKit Agents Playground](https://agents-playground.livekit.io) and connect to your room[...]  

---

## `uv run whisper` vs `uv run whisper_voice`

| Command | Entry point | What it does |
|---------|------------|--------------|
| `uv run whisper` | `server.py → main()` | Launches the **FastMCP server** over SSE transport on port 8000. This is the backend that registers the tools, prompts, and resources Whisper can cal[...]  
| `uv run whisper_voice` | `whisper_agent.py → dev()` | Launches the **LiveKit voice agent**. It builds the STT / LLM / TTS pipeline, connects to your LiveKit room, and wires up the MCP server [...]  

> Both processes must run **simultaneously**. The voice agent calls the MCP server in real time whenever it needs a tool (e.g. fetching news).

---

## Environment variables

Copy `.env.example` → `.env` and fill in the values below.

| Variable | Required | Where to get it |
|----------|----------|----------------|
| `LIVEKIT_URL` | ✅ | [LiveKit Cloud dashboard](https://cloud.livekit.io) → your project URL |
| `LIVEKIT_API_KEY` | ✅ | LiveKit Cloud → API Keys |
| `LIVEKIT_API_SECRET` | ✅ | LiveKit Cloud → API Keys |
| `GROQ_API_KEY` | optional | [console.groq.com](https://console.groq.com) — only needed if you switch `LLM_PROVIDER` to `groq` |
| `SARVAM_API_KEY` | ✅ (default STT) | [dashboard.sarvam.ai](https://dashboard.sarvam.ai) |
| `OPENAI_API_KEY` | ✅ (default TTS) | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| `DEEPGRAM_API_KEY` | optional | [console.deepgram.com](https://console.deepgram.com) |
| `GOOGLE_APPLICATION_CREDENTIALS` | optional | GCP service-account JSON path — only for `STT_PROVIDER = "google"` |
| `GOOGLE_API_KEY` | ✅ (default LLM) | [aistudio.google.com](https://aistudio.google.com/projects) |
| `SUPABASE_URL` | optional | [supabase.com](https://supabase.com) — for the ticketing tool |
| `SUPABASE_API_KEY` | optional | Supabase project → API settings |

---

## Switching providers

Open `whisper_agent.py` and change the provider constants at the top:

```python
STT_PROVIDER = "sarvam"   # "sarvam" | "whisper"
LLM_PROVIDER = "gemini"   # "gemini" | "openai"
TTS_PROVIDER = "openai"   # "openai" | "sarvam"
```

---

## Adding a new tool

1. Create or open a file in `whisper/tools/`
2. Define a `register(mcp)` function and decorate tools with `@mcp.tool()`
3. Import and call `register(mcp)` inside `whisper/tools/__init__.py`

The MCP server will pick it up on next start.

---

## Tech stack

- **[FastMCP](https://github.com/jlowin/fastmcp)** — MCP server framework
- **[LiveKit Agents](https://github.com/livekit/agents)** — real-time voice pipeline
- **Sarvam Saaras v3** — STT (Indian-English optimised)
- **Google Gemini 2.5 Flash** — LLM
- **OpenAI TTS** (`nova` voice) — TTS
- **[uv](https://github.com/astral-sh/uv)** — fast Python package manager

---

## License

MIT