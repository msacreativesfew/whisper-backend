#!/bin/bash
set -e

# Railway/Render provides the $PORT environment variable. Default to 8080 if not set.
export PORT="${PORT:-8080}"

echo "Starting Whisper Cloud API on port $PORT..."

# Start the LiveKit voice agent in the background
echo "Starting Whisper Voice Agent..."
uv run python whisper_agent.py dev &

# Start the FastAPI web service in the foreground
echo "Starting Uvicorn..."
exec uv run uvicorn cloud_api:app --host 0.0.0.0 --port $PORT --log-level info
