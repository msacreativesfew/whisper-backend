"""
Whisper AI Assistant — v6 (Stable + Key Rotation + Full Transcripts)
=====================================================================
• Auto Groq API key rotation when rate-limited
• Natural greeting with user profile awareness
• Transcription enabled for both user and agent
• Name/title update via save_user_profile tool
• livekit-agents v1.5.x API
"""

import os
import logging
import sys
import json
import asyncio
import webbrowser
import datetime
import subprocess
import shutil
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Force UTF-8 on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import multiprocessing
if sys.platform == "win32":
    try:
        multiprocessing.set_start_method('spawn', force=True)
    except RuntimeError:
        pass

from livekit.agents import JobContext, WorkerOptions, cli, room_io
from livekit.agents import llm as lk_llm
from livekit.agents.voice import Agent, AgentSession
from livekit.plugins import silero
from livekit.plugins import groq as lk_groq
from livekit.plugins import google as lk_google
from livekit.plugins import openai as lk_openai
from livekit.plugins import deepgram
import google_tools

load_dotenv(override=True)

logger = logging.getLogger("whisper-agent")
logger.setLevel(logging.INFO)
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

GROQ_LLM_MODEL   = os.getenv("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
GOOGLE_LLM_MODEL = os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash")
OPENAI_LLM_MODEL = os.getenv("OPENAI_LLM_MODEL", "gpt-4.1-mini")
LLM_PROVIDER     = os.getenv("LLM_PROVIDER", "auto").strip().lower()
ROOM_NAME        = os.getenv("LIVEKIT_ROOM_NAME", "whisper-room")
AGENT_NAME       = os.getenv("LIVEKIT_AGENT_NAME", "whisper-assistant")
DESKTOP_GREETING = os.getenv("DESKTOP_GREETING", "Whisper is online. How can I help you?")
WHATSAPP_DEFAULT_PHONE = os.getenv("WHATSAPP_DEFAULT_PHONE", "").strip()
MIN_LLM_ATTEMPT_TIMEOUT = 10.5
if LLM_PROVIDER == "fallback":
    LLM_PROVIDER = "auto"
if LLM_PROVIDER == "google":
    LLM_PROVIDER = "gemini"
PROFILE_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_profile.json")
SCREENSHOTS_DIR  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")

# Groq API key pool — rotated on rate-limit errors
_GROQ_KEYS = [k for k in [
    os.getenv("GROQ_API_KEY_1"),
    os.getenv("GROQ_API_KEY_2"),
    os.getenv("GROQ_API_KEY_3"),
    os.getenv("GROQ_API_KEY_4"),
    os.getenv("GROQ_API_KEY"),
] if k]
_groq_key_index = 0

def _get_groq_key() -> str:
    """Return current Groq API key."""
    global _groq_key_index
    return _GROQ_KEYS[_groq_key_index % len(_GROQ_KEYS)] if _GROQ_KEYS else ""

def _rotate_groq_key():
    """Switch to next Groq API key (called on rate limit)."""
    global _groq_key_index
    _groq_key_index = (_groq_key_index + 1) % max(1, len(_GROQ_KEYS))
    logger.warning("Groq key rotated to index %d", _groq_key_index)

SYSTEM_PROMPT = """
You are Whisper — a highly intelligent, calm, and warm personal AI assistant.

## LANGUAGE RULES (CRITICAL — follow exactly)
- Detect the language the user is speaking in.
- If the user speaks or writes in Urdu (even Urdu mixed with English), you MUST reply in ROMAN URDU.
  Roman Urdu means: Urdu language, but written entirely in English/Latin letters (a-z, no Arabic script).
  Examples of Roman Urdu:
    "Aap ka din mubarak ho, Sir!"
    "Ji haan, main aap ki madad kar sakta hoon."
  NEVER write Urdu in Arabic script. ONLY use English letters for Urdu responses.
- If the user speaks English, reply in English.
- Keep ALL responses SHORT, natural, and conversational. No markdown. No bullet points.

## YOUR CAPABILITIES
- Real-time weather for any city (use get_weather tool)
- Web search for current events, news, facts (use search_web tool)
- Open YouTube to search songs or videos (use search_youtube tool)
- Open desktop apps like WhatsApp, Chrome, Notepad, Calculator, Explorer, and Settings (use open_application tool)
- Open WhatsApp quickly (use open_whatsapp tool)
- Draft WhatsApp messages to a phone number or configured default number (use send_whatsapp_message tool)
- Start a best-effort WhatsApp call flow for a phone number or configured default number (use start_whatsapp_call tool)
- Take a screenshot of the screen (use take_screenshot tool)
- Remember the user's name and title (use save_user_profile tool). When asked to update name/title, ALWAYS call this tool first, then confirm verbally.
- Check remaining API limits and credits (use check_api_limits tool)
- Open World Monitor app and read current Pakistan news when the user asks (use open_world_monitor tool)
- Read recent Gmail messages and open a specific one in detail (use read_emails and read_email_detail tools)
- Send emails, mark them read or unread, archive or star them, and delete them when asked (use send_email, update_email_labels, and delete_email tools)
- Check upcoming Google Calendar events (use get_calendar_events tool)
- Add new events to the calendar (use add_calendar_event tool)
- Search Google Drive files (use list_drive_files tool)
- Read Google Fitness activity summaries like steps and calories (use get_fitness_summary tool)
- Give route guidance with traffic and destination weather for a place the user wants to go (use get_route_brief tool)
- Remember important long-term facts about the user (use store_memory tool)
- Recall past long-term memories when asked (use retrieve_memories tool)

## PERSONALITY
- Warm, witty, and efficient — like a trusted personal aide.
- Always address the user by their preferred title and name if known (e.g., "Sir Ahmed").
- Be brief. One or two sentences unless more detail is needed.
- Never say "I cannot" — always try to help.
""".strip()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_profile() -> dict:
    try:
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"name": None, "title": None}

def _save_profile(profile: dict):
    try:
        with open(PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=4)
    except Exception as e:
        logger.error("Failed to save profile: %s", e)


def _open_target(target: str) -> None:
    if sys.platform == "win32":
        os.startfile(target)
        return
    webbrowser.open(target)


def _clean_phone_number(phone_number: str | None) -> str:
    raw = (phone_number or WHATSAPP_DEFAULT_PHONE or "").strip()
    return "".join(ch for ch in raw if ch.isdigit())


def _launch_app(app_name: str) -> tuple[bool, str]:
    name = app_name.strip().lower()

    app_map = {
        "whatsapp": [("uri", "whatsapp:"), ("url", "https://web.whatsapp.com/")],
        "chrome": [("exe", "chrome.exe"), ("url", "https://www.google.com/")],
        "browser": [("url", "https://www.google.com/")],
        "youtube": [("url", "https://www.youtube.com/")],
        "notepad": [("exe", "notepad.exe")],
        "calculator": [("exe", "calc.exe")],
        "calc": [("exe", "calc.exe")],
        "explorer": [("exe", "explorer.exe")],
        "files": [("exe", "explorer.exe")],
        "settings": [("uri", "ms-settings:")],
    }

    candidates = app_map.get(name)
    if not candidates:
        return False, f"I don't have a launcher preset for {app_name} yet."

    last_error = None
    for kind, value in candidates:
        try:
            if kind == "exe":
                exe = shutil.which(value) or value
                subprocess.Popen([exe])
            else:
                _open_target(value)
            return True, f"Opened {app_name}."
        except Exception as e:
            last_error = e

    return False, f"Failed to open {app_name}: {last_error}"

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@lk_llm.function_tool
async def save_user_profile(
    name: str | None = None,
    title: str | None = None,
) -> str:
    """Save or update the user's name and preferred title (e.g. Sir, Ma'am, Doctor, etc.)."""
    profile = _load_profile()
    if name:  profile["name"]  = name.strip()
    if title: profile["title"] = title.strip()
    _save_profile(profile)
    logger.info("Profile updated: %s", profile)
    return f"Profile saved. Name: {profile.get('name')}, Title: {profile.get('title')}."

@lk_llm.function_tool
async def store_memory(fact: str) -> str:
    """Store an important fact about the user for long-term memory."""
    import httpx
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_API_KEY")
    if not supabase_url or not supabase_key:
        return "Supabase credentials are not configured."
    
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    data = {"fact": fact}
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(f"{supabase_url}/rest/v1/memories", headers=headers, json=data)
            if resp.status_code in [200, 201]:
                return f"Memory stored successfully: {fact}"
            else:
                return f"Failed to store memory. Status code: {resp.status_code}"
    except Exception as e:
        return f"Memory storage failed: {e}"

@lk_llm.function_tool
async def retrieve_memories() -> str:
    """Retrieve the most recent facts and memories about the user."""
    import httpx
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_API_KEY")
    if not supabase_url or not supabase_key:
        return "Supabase credentials are not configured."
    
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}",
    }
    
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{supabase_url}/rest/v1/memories?select=fact,created_at&order=created_at.desc&limit=20",
                headers=headers
            )
            if resp.status_code == 200:
                memories = resp.json()
                if not memories:
                    return "No long-term memories found."
                
                output = "Recent memories:\n"
                for m in memories:
                    output += f"- {m['fact']} (stored at {m['created_at']})\n"
                return output
            else:
                return f"Failed to retrieve memories. Status code: {resp.status_code}"
    except Exception as e:
        return f"Memory retrieval failed: {e}"


@lk_llm.function_tool
async def get_weather(city: str) -> str:
    """Get current real-time weather for any city in the world."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            geo_r = await client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={"name": city, "count": 1, "format": "json"},
            )
            geo = geo_r.json().get("results", [])
            if not geo:
                return f"City not found: {city}"
            r         = geo[0]
            lat, lon  = r["latitude"], r["longitude"]
            city_name = r["name"]
            country   = r.get("country", "")

            w_r = await client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": lat, "longitude": lon,
                    "current": "temperature_2m,weather_code,wind_speed_10m,relative_humidity_2m",
                    "timezone": "auto",
                },
            )
            w        = w_r.json()["current"]
            temp     = w["temperature_2m"]
            humidity = w["relative_humidity_2m"]
            wind     = w["wind_speed_10m"]
            code     = w["weather_code"]

            WX = {
                0: "clear sky", 1: "mainly clear", 2: "partly cloudy", 3: "overcast",
                45: "foggy", 48: "icy fog", 51: "light drizzle", 53: "drizzle",
                61: "light rain", 63: "rain", 65: "heavy rain",
                71: "light snow", 73: "snow", 75: "heavy snow",
                80: "rain showers", 81: "showers", 82: "heavy showers",
                95: "thunderstorm", 96: "thunderstorm with hail", 99: "heavy thunderstorm",
            }
            desc = WX.get(code, "mixed conditions")

            return (
                f"Weather in {city_name}, {country}: {desc}. "
                f"Temperature {temp}°C, humidity {humidity}%, wind {wind} km/h."
            )
    except Exception as e:
        return f"Weather fetch failed: {e}"


@lk_llm.function_tool
async def search_web(query: str) -> str:
    """Search the web for real-time information, news, or facts."""
    try:
        from duckduckgo_search import DDGS
        snippets = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=3):
                snippets.append(f"{r['title']}: {r['body'][:250]}")
        return " | ".join(snippets) if snippets else "No results found."
    except Exception as e:
        return f"Web search failed: {e}"


@lk_llm.function_tool
async def search_youtube(query: str) -> str:
    """Search for a song or video on YouTube by opening the browser."""
    import urllib.parse
    url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    webbrowser.open(url)
    logger.info("Opened YouTube: %s", url)
    return f"Opened YouTube search for: {query}"


@lk_llm.function_tool
async def open_application(app_name: str) -> str:
    """Open a supported desktop application such as WhatsApp, Chrome, Notepad, Calculator, Explorer, or Settings."""
    ok, message = _launch_app(app_name)
    return message


@lk_llm.function_tool
async def open_whatsapp() -> str:
    """Open WhatsApp Desktop or WhatsApp Web."""
    ok, message = _launch_app("whatsapp")
    return message


@lk_llm.function_tool
async def send_whatsapp_message(message: str, phone_number: str | None = None) -> str:
    """Open a WhatsApp chat with a prefilled message for the given phone number or configured default number."""
    phone = _clean_phone_number(phone_number)
    if not phone:
        return "No WhatsApp phone number is configured. Set WHATSAPP_DEFAULT_PHONE or provide a phone number."

    text = urllib.parse.quote(message.strip())
    url = f"https://wa.me/{phone}?text={text}"
    try:
        _open_target(url)
        return f"Opened WhatsApp message draft for {phone}."
    except Exception as e:
        return f"Failed to open WhatsApp message draft: {e}"


@lk_llm.function_tool
async def start_whatsapp_call(phone_number: str | None = None, video: bool = False) -> str:
    """Best-effort WhatsApp call helper. Opens the target chat or app for a voice or video call."""
    phone = _clean_phone_number(phone_number)
    if not phone:
        return "No WhatsApp phone number is configured. Set WHATSAPP_DEFAULT_PHONE or provide a phone number."

    deep_links = [
        f"whatsapp://send?phone={phone}",
        f"https://wa.me/{phone}",
    ]
    for link in deep_links:
        try:
            _open_target(link)
            call_type = "video" if video else "voice"
            return f"Opened WhatsApp for a {call_type} call with {phone}. You may need one manual click inside WhatsApp to place the call."
        except Exception:
            continue
    return f"Failed to open WhatsApp call flow for {phone}."


@lk_llm.function_tool
async def take_screenshot() -> str:
    """Take a screenshot of the current screen and save it to the screenshots folder."""
    try:
        from PIL import ImageGrab
        Path(SCREENSHOTS_DIR).mkdir(parents=True, exist_ok=True)
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(SCREENSHOTS_DIR, f"screenshot_{ts}.png")
        img      = ImageGrab.grab()
        img.save(filepath)
        logger.info("Screenshot saved: %s", filepath)
        return f"Screenshot saved as screenshot_{ts}.png"
    except Exception as e:
        return f"Screenshot failed: {e}"


@lk_llm.function_tool
async def check_api_limits() -> str:
    """Check remaining API credits for Groq and Deepgram."""
    import httpx
    response = []

    groq_api_key = _get_groq_key()
    if groq_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {groq_api_key}"}
                )
                h = resp.headers
                remaining_req = int(h.get("x-ratelimit-remaining-requests", 0))
                remaining_tok = int(h.get("x-ratelimit-remaining-tokens", 0))
                response.append(f"Groq API: {remaining_req} requests and {remaining_tok} tokens remaining.")
        except Exception as e:
            response.append(f"Groq API error: {str(e)}")

    dg_api_key = os.getenv("DEEPGRAM_API_KEY")
    if dg_api_key:
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                headers = {"Authorization": f"Token {dg_api_key}", "Content-Type": "application/json"}
                proj_r = await client.get("https://api.deepgram.com/v1/projects", headers=headers)
                if proj_r.status_code == 200:
                    projects = proj_r.json().get("projects", [])
                    if projects:
                        proj_id = projects[0]["project_id"]
                        bal_r = await client.get(
                            f"https://api.deepgram.com/v1/projects/{proj_id}/balances",
                            headers=headers
                        )
                        if bal_r.status_code == 200:
                            balances = bal_r.json().get("balances", [])
                            if balances:
                                bal    = balances[0]
                                amount = bal.get("amount", 0)
                                units  = bal.get("units", "USD")
                                response.append(f"Deepgram API: {amount} {units} remaining.")
                            else:
                                response.append("Deepgram API: No balance info found.")
                        else:
                            response.append("Deepgram API: Failed to fetch balances.")
                    else:
                        response.append("Deepgram API: No projects found.")
                else:
                    response.append("Deepgram API: Failed to fetch projects.")
        except Exception as e:
            response.append(f"Deepgram API error: {str(e)}")
    else:
        response.append("Deepgram API key not configured.")

    return " ".join(response)


@lk_llm.function_tool
async def open_world_monitor() -> str:
    """Open the World Monitor app and read the most current news from Pakistan."""
    import subprocess
    from duckduckgo_search import DDGS

    try:
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_world_monitor.py")
        subprocess.Popen([sys.executable, script_path])
        logger.info("Launched World Monitor UI")
    except Exception as e:
        logger.error(f"Failed to launch world monitor: {e}")

    try:
        snippets = []
        with DDGS() as ddgs:
            for r in ddgs.text("latest current news Pakistan today", max_results=3):
                snippets.append(f"{r['title']}")
        news = " | ".join(snippets) if snippets else "No news found."
        return f"I've opened the World Monitor app. Latest Pakistan news: {news}"
    except Exception as e:
        return f"I've opened the World Monitor app, but failed to fetch news: {e}"


# ---------------------------------------------------------------------------
# LLM factory with key rotation
# ---------------------------------------------------------------------------

def _make_groq_llm(api_key: str | None = None, key_index: int | None = None) -> lk_groq.LLM:
    """Create a Groq LLM instance with the current key."""
    key = api_key or _get_groq_key()
    if not key:
        raise RuntimeError("Groq LLM requested but no Groq API key is configured.")

    index_for_log = _groq_key_index if key_index is None else key_index
    logger.info(
        "Creating Groq LLM with key index %d using model %s",
        index_for_log,
        GROQ_LLM_MODEL,
    )
    return lk_groq.LLM(
        model=GROQ_LLM_MODEL,
        api_key=key,
    )


def _make_google_llm() -> lk_google.LLM:
    """Create a Gemini LLM instance using GOOGLE_API_KEY."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("Gemini LLM requested but GOOGLE_API_KEY is not configured.")

    logger.info("Creating Gemini LLM using model %s", GOOGLE_LLM_MODEL)
    return lk_google.LLM(
        model=GOOGLE_LLM_MODEL,
        api_key=api_key,
    )


def _make_openai_llm() -> lk_openai.LLM:
    """Create an OpenAI LLM instance using OPENAI_API_KEY."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI LLM requested but OPENAI_API_KEY is not configured.")

    logger.info("Creating OpenAI LLM using model %s", OPENAI_LLM_MODEL)
    return lk_openai.LLM(
        model=OPENAI_LLM_MODEL,
        api_key=api_key,
    )


def _make_llm():
    """Create the configured LLM with fallback so quota/rate-limit issues don't stall turns."""
    has_google = bool(os.getenv("GOOGLE_API_KEY"))
    has_groq = bool(_GROQ_KEYS)
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    if not has_google and not has_groq and not has_openai:
        raise RuntimeError(
            "No LLM provider configured. Set GOOGLE_API_KEY, OPENAI_API_KEY, or GROQ_API_KEY/GROQ_API_KEY_1."
        )

    preferred_order: list[str]
    if LLM_PROVIDER == "gemini":
        preferred_order = ["gemini", "groq", "openai"]
    elif LLM_PROVIDER == "groq":
        preferred_order = ["groq", "openai", "gemini"]
    elif LLM_PROVIDER == "openai":
        preferred_order = ["openai", "groq", "gemini"]
    else:
        if has_groq:
            preferred_order = ["groq", "openai", "gemini"]
        elif has_openai:
            preferred_order = ["openai", "groq", "gemini"]
        else:
            preferred_order = ["gemini", "groq", "openai"]

    llms: list = []
    for provider_name in preferred_order:
        if provider_name == "groq" and has_groq:
            for idx, key in enumerate(_GROQ_KEYS):
                llms.append(_make_groq_llm(api_key=key, key_index=idx))
        elif provider_name == "gemini" and has_google:
            llms.append(_make_google_llm())
        elif provider_name == "openai" and has_openai:
            llms.append(_make_openai_llm())

    if not llms:
        raise RuntimeError("Unable to build LLM configuration from environment settings.")

    if len(llms) == 1:
        return llms[0]

    timeout_raw = os.getenv("LLM_ATTEMPT_TIMEOUT", "12.0")
    try:
        attempt_timeout = max(MIN_LLM_ATTEMPT_TIMEOUT, float(timeout_raw))
    except ValueError:
        attempt_timeout = 12.0

    chain = " -> ".join(f"{llm.provider}:{llm.model}" for llm in llms)
    logger.warning(
        "LLM failover chain enabled (%s). Preferred provider: %s. Attempt timeout: %.1fs",
        chain,
        LLM_PROVIDER,
        attempt_timeout,
    )
    return lk_llm.FallbackAdapter(
        llm=llms,
        attempt_timeout=attempt_timeout,
        max_retry_per_llm=0,
        retry_interval=0.2,
        retry_on_chunk_sent=False,
    )


def _make_stt() -> deepgram.STT:
    """Build a streaming-safe STT config for the installed Deepgram plugin."""
    return deepgram.STT(
        model="nova-3",
        language="en-US",
        detect_language=False,
        interim_results=True,
        punctuate=True,
        smart_format=True,
        no_delay=True,
    )


def _make_tts() -> deepgram.TTS:
    """Build a stable TTS config for room audio + transcript sync."""
    return deepgram.TTS(
        model="aura-2-helena-en",
        sample_rate=24000,
    )


async def _wait_for_frontend_participant(ctx: JobContext, timeout: float = 2.0) -> bool:
    """Wait briefly for the desktop/web client to join before sending the greeting."""
    if ctx.room.remote_participants:
        return True

    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        if ctx.room.remote_participants:
            return True
        await asyncio.sleep(0.25)
    return False


def dev() -> None:
    """Project entry point used by `uv run whisper_voice`."""
    cli.run_app(
        WorkerOptions(
            entrypoint_fnc=entrypoint,
            agent_name=AGENT_NAME,
        )
    )


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

async def entrypoint(ctx: JobContext):
    print(f"\n[Agent] JOINING ROOM: {ctx.room.name}\n")
    logger.info("Agent: connecting to room %s", ctx.room.name)
    if ROOM_NAME and ctx.room.name != ROOM_NAME:
        logger.warning("Expected room %s but got %s", ROOM_NAME, ctx.room.name)

    stt = _make_stt()
    llm = _make_llm()
    tts = _make_tts()
    vad = silero.VAD.load()

    agent = Agent(
        instructions=SYSTEM_PROMPT,
        stt=stt,
        llm=llm,
        tts=tts,
        vad=vad,
        tools=[
            save_user_profile,
            get_weather,
            search_web,
            search_youtube,
            open_application,
            open_whatsapp,
            send_whatsapp_message,
            start_whatsapp_call,
            take_screenshot,
            check_api_limits,
            open_world_monitor,
            store_memory,
            retrieve_memories,
            google_tools.read_emails,
            google_tools.read_email_detail,
            google_tools.send_email,
            google_tools.update_email_labels,
            google_tools.delete_email,
            google_tools.get_calendar_events,
            google_tools.add_calendar_event,
            google_tools.list_drive_files,
            google_tools.get_fitness_summary,
            google_tools.get_route_brief,
        ],
    )

    session = AgentSession(
        turn_detection="vad",
        min_endpointing_delay=0.15,
        max_endpointing_delay=1.2,
    )

    # ── Session event logging ────────────────────────────────────────────────
    @session.on("user_speech_committed")
    def on_user_speech(msg):
        text = getattr(msg, "content", str(msg))
        logger.info("USER SAID: %s", text)

    @session.on("agent_speech_committed")
    def on_agent_speech(msg):
        text = getattr(msg, "content", str(msg))
        logger.info("AGENT SAID: %s", text)

    @session.on("agent_speech_interrupted")
    def on_interrupted():
        logger.info("Agent speech was interrupted by user")

    # ── Start session ────────────────────────────────────────────────────────
    await session.start(
        agent=agent,
        room=ctx.room,
        room_input_options=room_io.RoomInputOptions(
            text_enabled=True,
            audio_enabled=True,
            close_on_disconnect=False,
            # Send user STT transcripts to the room so frontend sees them
            noise_cancellation=None,
        ),
        room_output_options=room_io.RoomOutputOptions(
            audio_enabled=True,
            transcription_enabled=True,
            sync_transcription=True,
        ),
    )

    logger.info("Session started — waiting for frontend to subscribe…")
    frontend_ready = await _wait_for_frontend_participant(ctx)
    if not frontend_ready:
        logger.warning("Frontend participant did not appear before greeting timeout")

    # ── Greeting ─────────────────────────────────────────────────────────────
    greeting = DESKTOP_GREETING.strip() or "Whisper is online. How can I help you?"

    logger.info("Sending greeting: %s", greeting)
    try:
        await session.say(greeting, allow_interruptions=True)
        logger.info("Greeting sent successfully.")
    except Exception as e:
        logger.error("Failed to send greeting: %s", e)



if __name__ == "__main__":
    dev()
