#!/bin/bash
set -e

# Railway/Render provides the $PORT environment variable. Default to 8000 if not set.
PORT="${PORT:-8000}"

echo "Starting Whisper Cloud API on port $PORT..."
echo "Listening on 0.0.0.0:$PORT"

# Start the FastAPI web service in the background
uv run uvicorn cloud_api:app --host 0.0.0.0 --port $PORT --log-level info &
API_PID=$!

echo "Starting Whisper Voice Agent..."
# Start the LiveKit voice agent in the foreground so the container stays alive
# If voice agent fails, the FastAPI service will still be running
uv run python whisper_agent.py dev || (echo "Voice agent failed, but API continues running"; tail -f /dev/null)
