import os
from textwrap import dedent

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from livekit import api

# Import advanced features
from advanced_features_api import router as advanced_features_router
from models import init_db
from i18n import i18n_router, init_translator
from video_call_api import router as video_call_router

load_dotenv()

ROOM_NAME = os.getenv("LIVEKIT_ROOM_NAME", "whisper-room")
USER_IDENTITY = os.getenv("LIVEKIT_USER_IDENTITY", "user")
AGENT_NAME = os.getenv("LIVEKIT_AGENT_NAME", "whisper-assistant")

app = FastAPI(title="Whisper Cloud API")

# Initialize database on startup
try:
    init_db()
    print("[Whisper] Database initialized successfully")
except Exception as e:
    print(f"[Whisper] Database initialization warning: {e}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register advanced features router
app.include_router(advanced_features_router)

# Register i18n router
app.include_router(i18n_router)

# Register video call router with object detection
app.include_router(video_call_router)

# Initialize translator
init_translator("en")

VOICE_APP_HTML = dedent(
    """
    <!doctype html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Whisper AI</title>
        <style>
          :root {
            color-scheme: dark;
            --bg: #040507;
            --panel: rgba(14, 18, 28, 0.86);
            --panel-2: rgba(10, 14, 22, 0.92);
            --line: rgba(110, 176, 255, 0.18);
            --text: rgba(244, 248, 255, 0.94);
            --muted: rgba(244, 248, 255, 0.58);
            --cyan: #4de7ff;
            --violet: #9c7dff;
            --pink: #ff63d6;
            --amber: #ffc76b;
          }
          * { box-sizing: border-box; }
          html, body {
            margin: 0;
            min-height: 100%;
            background:
              radial-gradient(circle at top, rgba(59, 130, 246, 0.18), transparent 32%),
              radial-gradient(circle at 20% 20%, rgba(255, 99, 214, 0.14), transparent 18%),
              radial-gradient(circle at 80% 10%, rgba(77, 231, 255, 0.12), transparent 20%),
              var(--bg);
            color: var(--text);
            font-family: "Segoe UI", "Aptos", "Trebuchet MS", sans-serif;
          }
          body {
            display: grid;
            place-items: center;
            padding: 24px;
          }
          .shell {
            width: min(1100px, 100%);
            display: grid;
            gap: 18px;
          }
          .topbar {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            padding: 14px 18px;
            border: 1px solid var(--line);
            border-radius: 18px;
            background: linear-gradient(180deg, rgba(13, 17, 27, 0.92), rgba(8, 10, 16, 0.9));
            box-shadow: 0 20px 70px rgba(0, 0, 0, 0.45);
            backdrop-filter: blur(24px);
          }
          .brand {
            display: grid;
            gap: 4px;
          }
          .brand h1 {
            margin: 0;
            font-size: 13px;
            letter-spacing: 0.5em;
            text-transform: uppercase;
            color: rgba(255, 255, 255, 0.7);
          }
          .brand p {
            margin: 0;
            color: var(--muted);
            font-size: 13px;
          }
          .status {
            padding: 10px 14px;
            border-radius: 999px;
            border: 1px solid rgba(255,255,255,0.08);
            background: rgba(255,255,255,0.04);
            color: var(--muted);
            font-size: 12px;
            letter-spacing: 0.18em;
            text-transform: uppercase;
          }
          .status.ready { color: #8ef7b5; border-color: rgba(142, 247, 181, 0.2); }
          .status.listening { color: var(--cyan); border-color: rgba(77, 231, 255, 0.22); }
          .status.speaking { color: var(--pink); border-color: rgba(255, 99, 214, 0.22); }
          .status.error { color: #ff9b9b; border-color: rgba(255, 155, 155, 0.22); }
          .grid {
            display: grid;
            grid-template-columns: minmax(280px, 1.15fr) minmax(300px, 0.85fr);
            gap: 18px;
          }
          .hero, .card {
            border: 1px solid var(--line);
            border-radius: 24px;
            background: linear-gradient(180deg, rgba(13, 17, 27, 0.9), rgba(8, 10, 16, 0.94));
            box-shadow: 0 20px 70px rgba(0, 0, 0, 0.45);
            backdrop-filter: blur(24px);
          }
          .hero {
            min-height: 520px;
            padding: 24px;
            display: grid;
            gap: 18px;
            align-content: start;
          }
          .orb-wrap {
            display: grid;
            place-items: center;
            padding: 24px 0 10px;
          }
          .orb {
            width: min(42vw, 330px);
            aspect-ratio: 1;
            border-radius: 50%;
            position: relative;
            background:
              radial-gradient(circle at 35% 30%, rgba(255,255,255,0.18), transparent 28%),
              conic-gradient(from 0deg, #5ee0ff, #9c7dff, #ff63d6, #ffc76b, #5ee0ff);
            filter: blur(0.2px) saturate(140%);
            box-shadow:
              0 0 80px rgba(77, 231, 255, 0.18),
              inset 0 0 40px rgba(255,255,255,0.08);
            animation: spin 16s linear infinite;
          }
          .orb::before {
            content: "";
            position: absolute;
            inset: 18%;
            border-radius: 50%;
            background: radial-gradient(circle at 35% 30%, #2a2a2e 0%, #0a0a0c 58%, #000 100%);
            box-shadow: inset -16px -26px 50px rgba(0, 0, 0, 0.9), inset 16px 24px 50px rgba(130, 130, 190, 0.14);
          }
          .eyes {
            position: absolute;
            inset: 0;
            display: grid;
            place-items: center;
            pointer-events: none;
          }
          .eyes span {
            position: absolute;
            width: 18px;
            height: 28px;
            border-radius: 999px;
            background: #fff;
            box-shadow: 0 0 14px rgba(200, 220, 255, 0.8);
          }
          .eyes span:first-child { transform: translateX(-24px); }
          .eyes span:last-child { transform: translateX(24px); }
          .wave {
            height: 58px;
            position: relative;
            margin-top: -4px;
            overflow: hidden;
          }
          .wave::before,
          .wave::after {
            content: "";
            position: absolute;
            inset: 0;
            background:
              linear-gradient(90deg, transparent 0 4%, rgba(255,255,255,0.12) 4% 4.3%, transparent 4.3% 10%),
              linear-gradient(90deg, #4de7ff, #9c7dff, #ff63d6, #4de7ff);
            mask: radial-gradient(circle at center, transparent 0 46%, black 47% 100%);
            opacity: 0.78;
            filter: blur(0.1px);
            animation: wave 7s linear infinite;
          }
          .wave::after {
            animation-duration: 10s;
            opacity: 0.42;
            transform: translateY(10px);
          }
          .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
          }
          button {
            appearance: none;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.06);
            color: var(--text);
            border-radius: 999px;
            padding: 12px 16px;
            font: inherit;
            font-size: 12px;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            cursor: pointer;
            transition: transform 0.15s ease, background 0.2s ease, border-color 0.2s ease;
          }
          button:hover { transform: translateY(-1px); background: rgba(255,255,255,0.1); }
          button.primary {
            background: linear-gradient(135deg, rgba(77,231,255,0.16), rgba(156,125,255,0.16));
            border-color: rgba(77,231,255,0.22);
          }
          button.danger {
            background: rgba(255, 99, 214, 0.1);
            border-color: rgba(255, 99, 214, 0.18);
          }
          .note {
            color: var(--muted);
            font-size: 13px;
            line-height: 1.5;
          }
          .stack {
            display: grid;
            gap: 14px;
          }
          .message {
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 18px;
            padding: 14px 16px;
            background: rgba(255,255,255,0.03);
          }
          .message .label {
            margin-bottom: 6px;
            font-size: 10px;
            letter-spacing: 0.28em;
            text-transform: uppercase;
            color: rgba(255,255,255,0.42);
          }
          .message .text {
            margin: 0;
            font-size: 15px;
            line-height: 1.6;
            color: rgba(255,255,255,0.92);
            white-space: pre-wrap;
          }
          .message.user {
            border-color: rgba(77,231,255,0.2);
            background: rgba(77,231,255,0.06);
          }
          .message.agent {
            border-color: rgba(255,255,255,0.1);
            background: rgba(255,255,255,0.04);
          }
          .sidebar {
            display: grid;
            gap: 18px;
          }
          .card {
            padding: 18px;
          }
          .card h2 {
            margin: 0 0 12px;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.28em;
            color: rgba(255,255,255,0.48);
          }
          .meter {
            height: 8px;
            border-radius: 999px;
            background: rgba(255,255,255,0.05);
            overflow: hidden;
          }
          .meter > span {
            display: block;
            height: 100%;
            width: var(--pct, 0%);
            background: linear-gradient(90deg, var(--cyan), var(--violet), var(--pink));
          }
          .small {
            font-size: 12px;
            color: var(--muted);
            line-height: 1.5;
          }
          .footer {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: center;
            color: rgba(255,255,255,0.42);
            font-size: 12px;
          }
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          @keyframes wave {
            from { transform: translateX(0); }
            to { transform: translateX(10%); }
          }
          @media (max-width: 920px) {
            body { padding: 16px; }
            .grid { grid-template-columns: 1fr; }
            .hero { min-height: auto; }
            .orb { width: min(70vw, 320px); }
          }
        </style>
      </head>
      <body>
        <main class="shell">
          <section class="topbar">
            <div class="brand">
              <h1>Whisper AI Assistant</h1>
              <p>Browser voice console for Hugging Face deployments.</p>
            </div>
            <div id="status" class="status">Idle</div>
          </section>

          <section class="grid">
            <section class="hero">
              <div class="orb-wrap">
                <div class="orb">
                  <div class="eyes"><span></span><span></span></div>
                </div>
              </div>
              <div class="wave" aria-hidden="true"></div>

              <div class="controls">
                <button id="connect" class="primary">Connect</button>
                <button id="audio">Enable Audio</button>
                <button id="disconnect" class="danger">Disconnect</button>
              </div>

              <div class="note" id="hint">
                Press Connect, allow microphone access, and then speak naturally. The assistant will reply in the room audio and transcripts will appear here.
              </div>

              <div class="stack">
                <div class="message user">
                  <div class="label">You</div>
                  <p class="text" id="userText">Waiting for your first message...</p>
                </div>
                <div class="message agent">
                  <div class="label">Whisper</div>
                  <p class="text" id="agentText">The assistant reply will appear here.</p>
                </div>
              </div>
            </section>

            <aside class="sidebar">
              <section class="card">
                <h2>LiveKit</h2>
                <div class="small" id="livekitInfo">Not connected.</div>
              </section>
              <section class="card">
                <h2>Groq Usage</h2>
                <div class="small" id="groqText">Loading...</div>
                <div class="meter" style="margin-top: 10px;"><span id="groqMeter" style="--pct: 0%"></span></div>
              </section>
              <section class="card">
                <h2>ElevenLabs Usage</h2>
                <div class="small" id="elevenText">Loading...</div>
                <div class="meter" style="margin-top: 10px;"><span id="elevenMeter" style="--pct: 0%"></span></div>
              </section>
            </aside>
          </section>

          <div class="footer">
            <div>Whisper Cloud API</div>
            <div>/healthz · /livekit/config</div>
          </div>
        </main>

        <script type="module">
          let Room = null;
          let RoomEvent = null;
          let Track = null;

          async function loadLiveKit() {
            const sources = [
              "https://esm.sh/livekit-client@2.18.6?bundle",
              "https://cdn.jsdelivr.net/npm/livekit-client@2.18.6/+esm",
            ];

            for (const source of sources) {
              try {
                const mod = await import(source);
                Room = mod.Room;
                RoomEvent = mod.RoomEvent;
                Track = mod.Track;
                return;
              } catch (error) {
                console.warn("LiveKit import failed from", source, error);
              }
            }

            throw new Error("Unable to load LiveKit client from the CDN.");
          }

          const els = {
            status: document.getElementById("status"),
            connect: document.getElementById("connect"),
            audio: document.getElementById("audio"),
            disconnect: document.getElementById("disconnect"),
            hint: document.getElementById("hint"),
            userText: document.getElementById("userText"),
            agentText: document.getElementById("agentText"),
            livekitInfo: document.getElementById("livekitInfo"),
            groqText: document.getElementById("groqText"),
            groqMeter: document.getElementById("groqMeter"),
            elevenText: document.getElementById("elevenText"),
            elevenMeter: document.getElementById("elevenMeter"),
          };

          let room = null;
          let remoteAudioElement = null;
          let remoteAudioTrack = null;
          let audioCtx = null;
          let analyser = null;
          let rafId = null;
          let status = "idle";

          function setStatus(next, label) {
            status = next;
            els.status.className = `status ${next}`;
            els.status.textContent = label;
          }

          function setHint(text) {
            els.hint.textContent = text;
          }

          function classifyTranscriptSource(participant) {
            if (participant?.isLocal === true) return "user";
            if (participant?.isLocal === false) return "agent";
            return status === "listening" ? "user" : "agent";
          }

          function ensureRemoteAudioElement() {
            if (remoteAudioElement) return remoteAudioElement;
            remoteAudioElement = document.createElement("audio");
            remoteAudioElement.autoplay = true;
            remoteAudioElement.playsInline = true;
            remoteAudioElement.preload = "auto";
            remoteAudioElement.style.display = "none";
            document.body.appendChild(remoteAudioElement);
            return remoteAudioElement;
          }

          function detachRemoteAudio() {
            if (remoteAudioTrack) {
              remoteAudioTrack.detach();
              remoteAudioTrack = null;
            }
            if (remoteAudioElement) {
              remoteAudioElement.pause();
              remoteAudioElement.srcObject = null;
            }
          }

          function closeAudioContext() {
            if (audioCtx) {
              audioCtx.close().catch(() => {});
              audioCtx = null;
            }
          }

          function stopAnalyser() {
            if (rafId) cancelAnimationFrame(rafId);
            rafId = null;
            analyser = null;
          }

          function startAnalyser(track) {
            stopAnalyser();
            closeAudioContext();
            try {
              const Ctor = window.AudioContext || window.webkitAudioContext;
              const ctx = new Ctor();
              audioCtx = ctx;
              if (ctx.state === "suspended") {
                void ctx.resume();
              }
              const source = ctx.createMediaStreamSource(new MediaStream([track.mediaStreamTrack]));
              analyser = ctx.createAnalyser();
              analyser.fftSize = 512;
              source.connect(analyser);
              const data = new Uint8Array(analyser.frequencyBinCount);
              const tick = () => {
                if (!analyser) return;
                analyser.getByteTimeDomainData(data);
                let sum = 0;
                for (let i = 0; i < data.length; i += 1) {
                  const value = (data[i] - 128) / 128;
                  sum += value * value;
                }
                const level = Math.min(1, Math.sqrt(sum / data.length) * 5);
                document.documentElement.style.setProperty("--wave", `${10 + level * 30}px`);
                rafId = requestAnimationFrame(tick);
              };
              tick();
            } catch (error) {
              console.warn("Analyser error", error);
            }
          }

          async function loadConfig() {
            const response = await fetch("/livekit/config", { headers: { Accept: "application/json" } });
            if (!response.ok) {
              throw new Error(`Failed to load config: ${response.status}`);
            }
            return response.json();
          }

          async function updateUsage() {
            try {
              const groq = await fetch("/usage/groq").then((r) => r.json());
              if (groq?.remaining_requests !== undefined) {
                els.groqText.textContent = `Remaining requests: ${groq.remaining_requests} | tokens: ${groq.remaining_tokens}`;
              } else {
                els.groqText.textContent = groq?.error || "Unavailable";
              }
              const groqPct = groq?.remaining_requests && groq?.remaining_requests !== "unknown"
                ? Math.max(0, Math.min(100, 100 - (Number(groq.remaining_requests) / 30) * 100))
                : 0;
              els.groqMeter.style.setProperty("--pct", `${groqPct}%`);

              const eleven = await fetch("/usage/elevenlabs").then((r) => r.json());
              if (eleven?.character_count !== undefined) {
                els.elevenText.textContent = `Characters: ${eleven.character_count} / ${eleven.character_limit}`;
                const pct = Math.max(0, Math.min(100, (Number(eleven.character_count) / Math.max(1, Number(eleven.character_limit))) * 100));
                els.elevenMeter.style.setProperty("--pct", `${pct}%`);
              } else {
                els.elevenText.textContent = eleven?.error || "Unavailable";
                els.elevenMeter.style.setProperty("--pct", "0%");
              }
            } catch (error) {
              console.warn("Usage fetch failed", error);
            }
          }

          async function connect() {
            if (room) return;
            setStatus("connecting", "Connecting");
            setHint("Loading LiveKit config...");
            try {
              if (!Room) {
                await loadLiveKit();
              }
              const config = await loadConfig();
              const { url, token, room: roomName, agent_name: agentName } = config;
              if (!url || !token) {
                throw new Error("Missing LiveKit URL or token");
              }

              const lkRoom = new Room({
                adaptiveStream: true,
                dynacast: true,
                webAudioMix: false,
                audioCaptureDefaults: {
                  echoCancellation: true,
                  noiseSuppression: true,
                  autoGainControl: true,
                },
              });
              room = lkRoom;

              lkRoom.on(RoomEvent.TranscriptionReceived, (segments, participant) => {
                const text = segments.map((segment) => segment.text).join(" ").trim();
                if (!text) return;
                const isFinal = segments.every((segment) => segment.final);
                const source = classifyTranscriptSource(participant);
                if (source === "user") {
                  els.userText.textContent = isFinal ? text : text;
                  setStatus("listening", "Listening");
                  setHint("You can keep speaking. Whisper is listening.");
                  return;
                }
                els.agentText.textContent = text;
                setStatus("speaking", "Speaking");
                setHint("Whisper is replying now.");
              });

              lkRoom.on(RoomEvent.AudioPlaybackStatusChanged, (canPlay) => {
                if (!canPlay) {
                  setHint("Tap Enable Audio if your browser blocked playback.");
                }
              });

              lkRoom.on(RoomEvent.TrackSubscribed, (track, _publication, participant) => {
                if (track.kind === Track.Kind.Audio && !participant.isLocal) {
                  const audioElement = ensureRemoteAudioElement();
                  detachRemoteAudio();
                  remoteAudioTrack = track;
                  track.attach(audioElement);
                  audioElement.play().then(() => {
                    setStatus("speaking", "Speaking");
                  }).catch(() => {
                    setHint("Tap Enable Audio if playback is blocked.");
                  });
                  startAnalyser(track);
                }
              });

              lkRoom.on(RoomEvent.TrackUnsubscribed, (track) => {
                if (track.kind === Track.Kind.Audio) {
                  detachRemoteAudio();
                  stopAnalyser();
                  closeAudioContext();
                  if (status === "speaking") {
                    setStatus("idle", "Idle");
                  }
                }
              });

              lkRoom.on(RoomEvent.ParticipantConnected, (participant) => {
                if (!participant.isLocal) {
                  els.livekitInfo.textContent = `Connected to ${roomName || "whisper-room"} with ${participant.identity || agentName || "Whisper"}.`;
                }
              });

              lkRoom.on(RoomEvent.Disconnected, () => {
                detachRemoteAudio();
                stopAnalyser();
                closeAudioContext();
                room = null;
                setStatus("idle", "Idle");
                setHint("Disconnected. Press Connect to start again.");
                els.livekitInfo.textContent = "Not connected.";
              });

              await lkRoom.connect(url, token);
              await lkRoom.startAudio();
              try {
                await lkRoom.localParticipant.setMicrophoneEnabled(true);
              } catch (error) {
                console.warn("Microphone enable failed", error);
                setHint("Microphone permission is required for voice input.");
              }

              els.livekitInfo.textContent = `Connected to ${roomName || "whisper-room"}.`;
              setStatus("listening", "Listening");
              setHint("Whisper is ready. Speak naturally.");
              els.connect.textContent = "Reconnect";
              await updateUsage();
            } catch (error) {
              console.error("Connection failed", error);
              setStatus("error", "Error");
              setHint(String(error?.message || error));
              room = null;
            }
          }

          async function enableAudio() {
            if (!room) {
              setHint("Connect first, then enable audio if the browser blocks playback.");
              return;
            }
            try {
              await room.startAudio();
              if (remoteAudioElement) {
                await remoteAudioElement.play();
              }
              setHint("Audio playback enabled.");
            } catch (error) {
              console.warn("Audio enable failed", error);
              setHint("Your browser still blocked audio playback.");
            }
          }

          async function disconnect() {
            detachRemoteAudio();
            stopAnalyser();
            closeAudioContext();
            if (room) {
              await room.disconnect();
              room = null;
            }
            els.connect.textContent = "Connect";
            setStatus("idle", "Idle");
            setHint("Disconnected. Press Connect to talk again.");
            els.livekitInfo.textContent = "Not connected.";
            els.userText.textContent = "Waiting for your first message...";
            els.agentText.textContent = "The assistant reply will appear here.";
          }

          els.connect.addEventListener("click", () => {
            if (room) {
              void disconnect();
            } else {
              void connect();
            }
          });
          els.audio.addEventListener("click", () => void enableAudio());
          els.disconnect.addEventListener("click", () => void disconnect());

          setStatus("ready", "Ready");
          updateUsage();
          setInterval(updateUsage, 60000);
        </script>
      </body>
    </html>
    """
)


@app.get("/")
async def root():
    """Serve the browser voice console."""
    return HTMLResponse(VOICE_APP_HTML)


async def ensure_room_exists(lk_api: api.LiveKitAPI, room_name: str) -> tuple[bool, str]:
    """Create the room if it does not already exist."""
    try:
        rooms = await lk_api.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
        if rooms.rooms:
            return True, "existing"

        await lk_api.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=10 * 60,
                departure_timeout=20,
                max_participants=10,
            )
        )
        return True, "created"
    except Exception as e:
        return False, str(e)


async def ensure_agent_dispatch(room_name: str) -> tuple[bool, str]:
    """Make sure the configured LiveKit agent is dispatched to this room."""
    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not all([url, api_key, api_secret]):
        return False, "LiveKit credentials not configured for dispatch"

    lk_api = api.LiveKitAPI(url, api_key, api_secret)
    try:
        room_ok, room_info = await ensure_room_exists(lk_api, room_name)
        if not room_ok:
            return False, f"room_error: {room_info}"

        existing = await lk_api.agent_dispatch.list_dispatch(room_name)
        for dispatch in existing:
            if dispatch.agent_name == AGENT_NAME:
                return True, f"dispatch_existing ({room_info})"

        for attempt in range(2):
            try:
                await lk_api.agent_dispatch.create_dispatch(
                    api.CreateAgentDispatchRequest(
                        agent_name=AGENT_NAME,
                        room=room_name,
                        metadata="cloud-auto-dispatch",
                    )
                )
                return True, f"dispatch_created ({room_info})"
            except Exception as e:
                if "requested room does not exist" in str(e).lower() and attempt == 0:
                    import asyncio

                    await asyncio.sleep(0.35)
                    continue
                return False, str(e)
        return False, "dispatch_failed"
    except Exception as e:
        return False, str(e)
    finally:
        await lk_api.aclose()


@app.get("/healthz")
async def healthz():
    """Health check for deployment probes."""
    return {"status": "ok"}


@app.get("/livekit/config")
async def get_livekit_config():
    """Generate room token and ensure agent dispatch for the frontend session."""
    room_name = ROOM_NAME
    participant_name = USER_IDENTITY

    url = os.getenv("LIVEKIT_URL")
    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not url or not api_key or not api_secret:
        raise HTTPException(status_code=500, detail="LiveKit credentials not configured.")

    dispatch_ok, dispatch_info = await ensure_agent_dispatch(room_name)

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(participant_name)
        .with_name(participant_name)
        .with_grants(api.VideoGrants(room_join=True, room=room_name))
        .to_jwt()
    )

    return {
        "url": url,
        "token": token,
        "room": room_name,
        "agent_name": AGENT_NAME,
        "dispatch_ok": dispatch_ok,
        "dispatch_info": dispatch_info,
    }


@app.get("/usage/groq")
async def get_groq_usage():
    """Fetch remaining Groq API requests and tokens."""
    groq_api_key = os.getenv("GROQ_API_KEY_1") or os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        return {"error": "Groq API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {groq_api_key}"},
            )
            h = resp.headers
            remaining_req = h.get("x-ratelimit-remaining-requests", "unknown")
            remaining_tok = h.get("x-ratelimit-remaining-tokens", "unknown")
            return {
                "remaining_requests": remaining_req,
                "remaining_tokens": remaining_tok,
            }
    except Exception as e:
        return {"error": str(e)}


@app.get("/usage/elevenlabs")
async def get_elevenlabs_usage():
    """Fetch ElevenLabs character usage."""
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return {"error": "ElevenLabs API key not configured"}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.elevenlabs.io/v1/user",
                headers={"xi-api-key": api_key},
            )
            if resp.status_code == 200:
                data = resp.json()
                sub = data.get("subscription", {})
                return {
                    "character_count": sub.get("character_count"),
                    "character_limit": sub.get("character_limit"),
                }
            return {"error": f"Failed to fetch: {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
