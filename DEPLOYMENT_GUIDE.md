# Whisper AI Packaging and Cloud Deployment Guide

## Target Architecture

Whisper should run as one product with three layers:

1. `Cloud backend`
   The LiveKit voice agent and API stay online in the cloud so replies keep working even when the desktop app is closed.

2. `Desktop package`
   The installable Windows app uses `desktop_app.py` as a native shell around the built frontend. In cloud mode it should not start a local voice backend.

3. `Mobile package`
   The same responsive frontend can be wrapped as an Android or iPhone app with a native WebView wrapper while still talking to the same cloud backend.

## Current Direction in This Repo

- `desktop_app.py`
  Native desktop shell for the packaged app.
- `Frontend interface Ai assistant/Ai UI interface`
  Main responsive frontend for desktop and mobile layouts.
- `cloud_api.py`
  Cloud HTTP API for LiveKit room config and usage endpoints.
- `whisper_agent.py`
  Voice agent process that should run in the cloud.

## Cloud-Only Backend Mode

For a packaged desktop app that depends on the cloud backend:

- Set `DESKTOP_AGENT_MODE=cloud`
- Set `CLOUD_BACKEND_URL` to your deployed backend URL

In this mode the desktop app should:

- serve the local packaged frontend
- fetch LiveKit config from the cloud
- fetch usage info from the cloud
- avoid starting local `server.py`
- avoid starting local `whisper_agent.py`

## Desktop Packaging

Recommended Windows packaging path:

1. Build the frontend:
   `cd "Frontend interface Ai assistant/Ai UI interface"`
   `vite build`

2. Package `desktop_app.py` into an executable with PyInstaller:
   `pyinstaller --noconfirm --windowed desktop_app.py`

3. Include these runtime assets in the packaged build:
   - `Frontend interface Ai assistant/Ai UI interface/dist`
   - `.env`
   - any credential files required by the desktop shell

The desktop app is intended to act as a native shell, not as the voice backend itself when cloud mode is enabled.

## Mobile Packaging

Recommended mobile path:

1. Keep using the same responsive frontend.
2. Wrap it with a native shell such as Capacitor.
3. Point the mobile app to the same cloud backend URL.
4. Request microphone permission on first launch.

The mobile package should not contain the Python backend. It should only contain the frontend shell and talk to the cloud backend.

## Voice Requirements

For voice input and reply to work correctly, all of these must be healthy:

- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- at least one working LLM provider
- working Deepgram STT/TTS or other configured providers
- microphone permission granted in the app shell

## Notes

- If the cloud backend is offline, the desktop and mobile shells can still open, but voice will not work.
- If LiveKit room dispatch fails, the frontend may connect without hearing a response.
- If the LLM provider chain fails, transcripts may stop and the agent can end the session unexpectedly.
