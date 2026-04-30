import os
import sys
import time
import asyncio
import subprocess
import threading
import http.server
import socketserver
import socket
import webbrowser
from functools import partial

import atexit
import httpx
import webview
from dotenv import load_dotenv
from livekit import api

load_dotenv(override=True)

# --- HTTP Server for local frontend ---
DEFAULT_FRONTEND_PORT = 5173
FALLBACK_UI_PORT = int(os.getenv("WHISPER_FALLBACK_UI_PORT", "7860"))
ROOM_NAME = os.getenv("LIVEKIT_ROOM_NAME", "whisper-room")
USER_IDENTITY = os.getenv("LIVEKIT_USER_IDENTITY", "user")
USER_NAME = os.getenv("LIVEKIT_USER_NAME", "MSA")
AGENT_NAME = os.getenv("LIVEKIT_AGENT_NAME", "whisper-assistant")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(
    BASE_DIR,
    "Frontend interface Ai assistant",
    "Ai UI interface",
    "dist",
)


def find_available_port(preferred_port: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", preferred_port))
        except OSError:
            sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


PORT = find_available_port(DEFAULT_FRONTEND_PORT)


def start_server():
    handler = partial(http.server.SimpleHTTPRequestHandler, directory=DIST_DIR)
    # Allow port reuse to avoid "Address already in use" on restarts
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"[Backend] Serving frontend at http://localhost:{PORT}")
        httpd.serve_forever()


class Api:
    def __init__(self):
        self.base_dir = BASE_DIR
        self.server_process = None
        self.agent_process = None
        self.cloud_process = None
        self.server_log_handle = None
        self.agent_log_handle = None
        self.cloud_log_handle = None
        self._connecting = False
        self._started = False  # Guard: only start services once

    def _desktop_agent_mode(self) -> str:
        mode = (os.getenv("DESKTOP_AGENT_MODE") or "auto").strip().lower()
        return mode if mode in {"auto", "cloud", "local"} else "auto"

    def _cloud_backend_url(self) -> str:
        return (os.getenv("CLOUD_BACKEND_URL") or "").strip()

    def _cloud_health_url(self) -> str:
        cloud_url = self._cloud_backend_url()
        return f"{cloud_url.rstrip('/')}/healthz" if cloud_url else ""

    def _cloud_backend_available(self) -> bool:
        health_url = self._cloud_health_url()
        if not health_url:
            return False
        try:
            with httpx.Client(timeout=2.0) as client:
                resp = client.get(health_url)
            return resp.status_code == 200
        except Exception:
            return False

    def _use_cloud_backend(self) -> bool:
        mode = self._desktop_agent_mode()
        if mode == "local":
            return False
        if mode == "cloud":
            return self._cloud_backend_available()
        return self._cloud_backend_available()

    def _python_executable(self) -> str:
        if os.name == "nt":
            candidate = os.path.join(self.base_dir, ".venv", "Scripts", "python.exe")
        else:
            candidate = os.path.join(self.base_dir, ".venv", "bin", "python")
        return candidate if os.path.exists(candidate) else sys.executable

    def _run_async(self, coro):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(coro)
        finally:
            asyncio.set_event_loop(None)
            loop.close()

    async def _ensure_room_exists_async(self, lk_api: api.LiveKitAPI, room_name: str) -> bool:
        try:
            rooms = await lk_api.room.list_rooms(api.ListRoomsRequest(names=[room_name]))
            if rooms.rooms:
                return True

            await lk_api.room.create_room(
                api.CreateRoomRequest(
                    name=room_name,
                    empty_timeout=10 * 60,
                    departure_timeout=20,
                    max_participants=10,
                )
            )
            print(f"[Backend] Created LiveKit room '{room_name}'.")
            return True
        except Exception as e:
            print(f"[Backend] Failed to ensure room exists: {e}")
            return False

    async def _ensure_agent_dispatch_async(self, room_name: str) -> bool:
        lk_url = os.getenv("LIVEKIT_URL")
        lk_key = os.getenv("LIVEKIT_API_KEY")
        lk_secret = os.getenv("LIVEKIT_API_SECRET")
        if not all([lk_url, lk_key, lk_secret]):
            print("[Backend] Skipping dispatch: LiveKit credentials are incomplete.")
            return False

        lk_api = api.LiveKitAPI(lk_url, lk_key, lk_secret)
        try:
            room_ready = await self._ensure_room_exists_async(lk_api, room_name)
            if not room_ready:
                return False

            try:
                existing = await lk_api.agent_dispatch.list_dispatch(room_name)
            except Exception as e:
                if "requested room does not exist" in str(e).lower():
                    existing = []
                else:
                    raise e

            for dispatch in existing:
                if dispatch.agent_name == AGENT_NAME:
                    print(f"[Backend] Agent dispatch already exists for room '{room_name}'.")
                    return True

            for attempt in range(2):
                try:
                    await lk_api.agent_dispatch.create_dispatch(
                        api.CreateAgentDispatchRequest(
                            agent_name=AGENT_NAME,
                            room=room_name,
                            metadata="desktop-auto-dispatch",
                        )
                    )
                    print(f"[Backend] Created agent dispatch '{AGENT_NAME}' for room '{room_name}'.")
                    return True
                except Exception as e:
                    if "requested room does not exist" in str(e).lower() and attempt == 0:
                        await asyncio.sleep(0.35)
                        continue
                    print(f"[Backend] Failed to ensure agent dispatch: {e}")
                    return False
            return False
        finally:
            await lk_api.aclose()

    def _ensure_agent_dispatch(self, room_name: str = ROOM_NAME) -> bool:
        return bool(self._run_async(self._ensure_agent_dispatch_async(room_name)))

    def _clear_logs(self):
        for log_name in ("server.log", "agent.log"):
            try:
                with open(os.path.join(self.base_dir, log_name), "w", encoding="utf-8"):
                    pass
            except Exception as e:
                print(f"[Backend] Failed to clear {log_name}: {e}")

    def _close_log_handles(self):
        if self.cloud_log_handle and not self.cloud_log_handle.closed:
            self.cloud_log_handle.flush()
            self.cloud_log_handle.close()
        if self.agent_log_handle and not self.agent_log_handle.closed:
            self.agent_log_handle.flush()
            self.agent_log_handle.close()
        if self.server_log_handle and not self.server_log_handle.closed:
            self.server_log_handle.flush()
            self.server_log_handle.close()
        self.agent_log_handle = None
        self.server_log_handle = None
        self.cloud_log_handle = None

    def _start_cloud_fallback_ui(self):
        if self.cloud_process and self.cloud_process.poll() is None:
            return True

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["PYTHONUNBUFFERED"] = "1"
        python_exe = self._python_executable()

        if self.cloud_log_handle is None or self.cloud_log_handle.closed:
            self.cloud_log_handle = open(
                os.path.join(self.base_dir, "cloud_api.log"),
                "a",
                encoding="utf-8",
            )

        self.cloud_process = subprocess.Popen(
            [python_exe, "-u", "-m", "uvicorn", "cloud_api:app", "--host", "127.0.0.1", "--port", str(FALLBACK_UI_PORT)],
            cwd=self.base_dir,
            stdout=self.cloud_log_handle,
            stderr=self.cloud_log_handle,
            env=env,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return True

    def _frontend_url(self) -> str:
        return f"http://127.0.0.1:{PORT}"

    def _kill_stale_processes(self):
        try:
            import psutil
        except Exception:
            print("[Backend] psutil not available; skipping stale process cleanup.")
            return

        targets = []
        base_lower = self.base_dir.lower()
        current_pid = os.getpid()

        for proc in psutil.process_iter(attrs=["pid", "name", "cmdline", "cwd"]):
            info = proc.info
            pid = info.get("pid")
            if not pid or pid == current_pid:
                continue

            cmdline = " ".join(info.get("cmdline") or []).lower()
            cwd = (info.get("cwd") or "").lower()
            proc_name = (info.get("name") or "").lower()
            if "python" not in proc_name and "python" not in cmdline:
                continue

            in_project = base_lower in cmdline or base_lower in cwd
            if not in_project:
                continue

            is_server = "server.py" in cmdline
            is_agent = "whisper_agent.py" in cmdline
            if is_server or is_agent:
                targets.append(proc)

        if not targets:
            return

        for proc in targets:
            try:
                print(f"[Backend] Terminating stale process PID={proc.pid}")
                proc.terminate()
            except Exception:
                pass

        try:
            import psutil

            _, alive = psutil.wait_procs(targets, timeout=3)
            for proc in alive:
                try:
                    print(f"[Backend] Killing stale process PID={proc.pid}")
                    proc.kill()
                except Exception:
                    pass
        except Exception:
            pass

    def _process_healthy(self, proc, label: str) -> bool:
        if not proc:
            print(f"[Backend] {label} did not start.")
            return False
        code = proc.poll()
        if code is None:
            return True
        print(f"[Backend] {label} exited early with code {code}.")
        return False

    def get_livekit_config(self):
        """Called by the React frontend to get LiveKit connection credentials only.
        Services are started once at app launch, not per credential request."""
        print("[Backend] get_livekit_config called")
        return self.get_credentials()

    def get_credentials(self):
        """Generate a token for the frontend to connect to the LiveKit room.
        If CLOUD_BACKEND_URL is set in .env, fetch config from the cloud."""
        cloud_url = self._cloud_backend_url()
        if cloud_url and self._use_cloud_backend():
            print(f"[Backend] Attempting to fetch cloud credentials from: {cloud_url}")
            try:
                with httpx.Client(timeout=6.0) as client:
                    resp = client.get(f"{cloud_url.rstrip('/')}/livekit/config")
                    if resp.status_code == 200:
                        data = resp.json()
                        print(f"[Backend] Cloud credentials received: {data.get('url')}")
                        return data
                    print(f"[Backend] Cloud config error: {resp.status_code}")
            except Exception as e:
                print(f"[Backend] Cloud fetch failed (falling back to local): {e}")

        print("[Backend] Using local credentials")
        api_key = os.getenv("LIVEKIT_API_KEY")
        api_secret = os.getenv("LIVEKIT_API_SECRET")
        url = os.getenv("LIVEKIT_URL")

        if not all([api_key, api_secret, url]):
            print("[Backend] ERROR: Local LiveKit credentials incomplete!")
            return {"error": "Incomplete credentials"}

        self._ensure_agent_dispatch(room_name=ROOM_NAME)

        token = (
            api.AccessToken(api_key, api_secret)
            .with_identity(USER_IDENTITY)
            .with_name(USER_NAME)
            .with_grants(api.VideoGrants(room_join=True, room=ROOM_NAME))
            .to_jwt()
        )
        return {
            "url": url,
            "token": token,
        }

    def get_groq_usage(self):
        """Fetch Groq rate limit info."""
        cloud_url = os.getenv("CLOUD_BACKEND_URL")
        if cloud_url:
            try:
                with httpx.Client(timeout=6) as client:
                    resp = client.get(f"{cloud_url.rstrip('/')}/usage/groq")
                    if resp.status_code == 200:
                        data = resp.json()
                        if "remaining_requests" in data:
                            return {
                                "ok": True,
                                "requests": {
                                    "limit": 30,
                                    "remaining": int(data["remaining_requests"]) if data["remaining_requests"] != "unknown" else 30,
                                    "used": 0,
                                    "pct": 50,
                                },
                            }
                        return data
            except Exception:
                pass

        try:
            api_key = os.getenv("GROQ_API_KEY_1") or os.getenv("GROQ_API_KEY")
            with httpx.Client(timeout=6) as client:
                resp = client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                h = resp.headers
                limit_req = int(h.get("x-ratelimit-limit-requests", 30))
                remaining_req = int(h.get("x-ratelimit-remaining-requests", 30))
                limit_tok = int(h.get("x-ratelimit-limit-tokens", 6000))
                remaining_tok = int(h.get("x-ratelimit-remaining-tokens", 6000))
                return {
                    "ok": True,
                    "requests": {
                        "limit": limit_req,
                        "remaining": remaining_req,
                        "used": max(0, limit_req - remaining_req),
                        "pct": round((max(0, limit_req - remaining_req) / max(1, limit_req)) * 100),
                    },
                    "tokens": {
                        "limit": limit_tok,
                        "remaining": remaining_tok,
                        "used": max(0, limit_tok - remaining_tok),
                        "pct": round((max(0, limit_tok - remaining_tok) / max(1, limit_tok)) * 100),
                    },
                }
        except Exception as e:
            return {
                "ok": False,
                "error": str(e),
                "requests": {"pct": 0, "used": 0, "limit": 30, "remaining": 30},
                "tokens": {"pct": 0, "used": 0, "limit": 6000, "remaining": 6000},
            }

    def get_elevenlabs_usage(self):
        """Fetch ElevenLabs character usage."""
        cloud_url = os.getenv("CLOUD_BACKEND_URL")
        if cloud_url:
            try:
                with httpx.Client(timeout=6) as client:
                    resp = client.get(f"{cloud_url.rstrip('/')}/usage/elevenlabs")
                    if resp.status_code == 200:
                        data = resp.json()
                        used = data.get("character_count", 0)
                        limit = data.get("character_limit", 10000)
                        return {
                            "ok": True,
                            "used": used,
                            "limit": limit,
                            "remaining": max(0, limit - used),
                            "pct": round((used / max(1, limit)) * 100),
                        }
            except Exception:
                pass

        try:
            api_key = os.getenv("ELEVENLABS_API_KEY")
            with httpx.Client(timeout=6) as client:
                resp = client.get(
                    "https://api.elevenlabs.io/v1/user/subscription",
                    headers={"xi-api-key": api_key},
                )
                data = resp.json()
                used = data.get("character_count", 0)
                limit = data.get("character_limit", 10000)
                return {
                    "ok": True,
                    "used": used,
                    "limit": limit,
                    "remaining": max(0, limit - used),
                    "pct": round((used / max(1, limit)) * 100),
                }
        except Exception as e:
            return {"ok": False, "error": str(e), "used": 0, "limit": 10000, "remaining": 10000, "pct": 0}

    def connect(self):
        """Start backend services with stale-process cleanup."""
        if self._use_cloud_backend():
            if self._started:
                print("[Backend] Cloud backend already selected, skipping restart.")
                return True
            self._kill_stale_processes()
            self._close_log_handles()
            print(
                f"[Backend] Desktop agent mode is '{self._desktop_agent_mode()}'; "
                f"using cloud backend at {self._cloud_backend_url()}. Local backend services will stay off."
            )
            self._started = True
            return True

        server_running = self.server_process and self.server_process.poll() is None
        agent_running = self.agent_process and self.agent_process.poll() is None
        if self._started and server_running and agent_running:
            print("[Backend] Services already running, skipping restart.")
            return True
        if self._connecting:
            return True

        self._connecting = True
        self._started = False
        try:
            self._kill_stale_processes()

            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            env["PYTHONUTF8"] = "1"
            env["PYTHONUNBUFFERED"] = "1"
            python_exe = self._python_executable()

            print("Starting MCP Server...")
            if self.server_log_handle is None or self.server_log_handle.closed:
                self.server_log_handle = open(
                    os.path.join(self.base_dir, "server.log"),
                    "a",
                    encoding="utf-8",
                )
            self.server_process = subprocess.Popen(
                [python_exe, "-u", "server.py"],
                cwd=self.base_dir,
                stdout=self.server_log_handle,
                stderr=self.server_log_handle,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            print("Starting Whisper Agent...")
            if self.agent_log_handle is None or self.agent_log_handle.closed:
                self.agent_log_handle = open(
                    os.path.join(self.base_dir, "agent.log"),
                    "a",
                    encoding="utf-8",
                )
            self.agent_process = subprocess.Popen(
                [python_exe, "-u", "whisper_agent.py", "dev"],
                cwd=self.base_dir,
                stdout=self.agent_log_handle,
                stderr=self.agent_log_handle,
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )

            time.sleep(1.5)
            server_ok = self._process_healthy(self.server_process, "MCP server")
            agent_ok = self._process_healthy(self.agent_process, "Whisper agent")
            self._started = bool(server_ok and agent_ok)

            if self._started:
                self._ensure_agent_dispatch(room_name=ROOM_NAME)
                self._start_cloud_fallback_ui()  # Ensure HTTP fallback is available
                return True

            self.disconnect(clear_logs=False)
            return False
        finally:
            self._connecting = False

    def disconnect(self, clear_logs: bool = False):
        print("[Backend] Stopping backend services...")
        for proc_name in ("agent_process", "server_process", "cloud_process"):
            proc = getattr(self, proc_name)
            if not proc:
                continue

            print(f"[Backend] Terminating {proc_name} (PID: {proc.pid})")
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print(f"[Backend] Force killing {proc_name}")
                    proc.kill()
                    proc.wait(timeout=2)
            setattr(self, proc_name, None)

        self._kill_stale_processes()
        self._close_log_handles()
        if clear_logs:
            self._clear_logs()

        self._started = False
        self._connecting = False
        print("[Backend] Services stopped successfully.")
        return True

    def open_url(self, url: str):
        """Open a URL in the default browser."""
        print(f"[API] Opening URL: {url}")
        webbrowser.open(url)
        return True

    def open_app(self, name: str):
        """Open a local application."""
        print(f"[API] Opening App: {name}")
        import shutil
        app_name = name.lower().strip()
        
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

        candidates = app_map.get(app_name)
        if not candidates:
            return False

        for kind, value in candidates:
            try:
                if kind == "exe":
                    exe = shutil.which(value) or value
                    subprocess.Popen([exe])
                elif kind == "uri":
                    os.startfile(value)
                else:
                    webbrowser.open(value)
                return True
            except Exception as e:
                print(f"[API] Error opening {name}: {e}")
                continue
        return False

    def take_screenshot(self):
        """Take a screenshot and save it locally."""
        print("[API] Taking screenshot")
        try:
            from PIL import ImageGrab
            import datetime
            shot_dir = os.path.join(self.base_dir, "screenshots")
            os.makedirs(shot_dir, exist_ok=True)
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            path = os.path.join(shot_dir, f"screenshot_{ts}.png")
            img = ImageGrab.grab()
            img.save(path)
            print(f"[API] Screenshot saved to {path}")
            return True
        except Exception as e:
            print(f"[API] Screenshot failed: {e}")
            return False

    def restart(self):
        print("[Backend] Restart requested.")
        self.disconnect(clear_logs=True)
        return self.connect()

    def cleanup(self):
        self.disconnect()


# Initialize API backend
app_api = Api()
atexit.register(app_api.cleanup)

if __name__ == "__main__":
    # Start the local frontend server in a daemon thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Start backend services once before the window opens
    app_api.connect()

    window = webview.create_window(
        "Whisper AI System",
        url=app_api._frontend_url(),
        js_api=app_api,
        width=1100,
        height=850,
        min_size=(800, 600),
        frameless=False,
        background_color="#000000",
        text_select=False,
        confirm_close=True,
    )
    # webview.start(debug=True)  # Uncomment for DevTools
    gui_backend = (os.getenv("WEBVIEW_GUI") or "").strip().lower() or None

    try:
        if gui_backend:
            webview.start(gui=gui_backend, debug=True)
        else:
            webview.start(debug=True)
    except Exception as e:
        print(f"[Backend] WebView failed, switching to browser UI: {e}")
        if app_api._use_cloud_backend():
            webbrowser.open(app_api._frontend_url())
        else:
            app_api._start_cloud_fallback_ui()
            webbrowser.open(f"http://127.0.0.1:{FALLBACK_UI_PORT}")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
