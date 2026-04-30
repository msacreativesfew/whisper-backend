# Railway Frontend Deployment Guide

## Environment Variables

### For Railway Production Deployment

Add these variables in your **Railway dashboard** under **Variables**:

```
VITE_API_BASE_URL=https://your-railway-domain.up.railway.app
CLOUD_BACKEND_URL=https://your-railway-domain.up.railway.app
```

### For Local Development

Create a `.env.local` file in the frontend directory:

```
VITE_API_BASE_URL=http://localhost:8000
CLOUD_BACKEND_URL=http://localhost:8000
```

## How API Base URL Detection Works

The frontend uses intelligent endpoint detection in this priority order:

1. **Production Deployments** (Railway/Vercel/etc):
   - If not on localhost, uses current origin (e.g., `https://your-domain.up.railway.app`)
   - This automatically works with Railway's reverse proxy

2. **Explicit Environment Variables**:
   - `VITE_API_BASE_URL`
   - `CLOUD_BACKEND_URL`
   - `REACT_APP_API_URL`

3. **Local Development**:
   - Detects if running on `localhost:5173` (Vite default) or custom port
   - Falls back to `http://127.0.0.1:8000`

## Troubleshooting Connection Errors

### 1. Check Browser Console

Open Developer Tools (F12) and check the Console tab for messages like:

```
[Whisper] Connecting to API at: https://whisper-backend-production-77ec.up.railway.app
[Whisper] Backend is healthy
[Whisper] LiveKit config received: {url: "present", token: "present"}
```

### 2. Check Backend Endpoint

Test the health check endpoint:

```bash
curl https://your-railway-domain.up.railway.app/healthz
```

Should return:
```json
{"status": "ok"}
```

### 3. Check CORS Issues

The backend should allow cross-origin requests. Verify in console for:

```
Access to XMLHttpRequest has been blocked by CORS policy
```

If you see this, the backend needs CORS configuration updates.

### 4. Check LiveKit Config Endpoint

Test the LiveKit config endpoint:

```bash
curl https://your-railway-domain.up.railway.app/livekit/config
```

Should return:
```json
{
  "url": "wss://your-livekit-server.com",
  "token": "eyJ..."
}
```

## Frontend Build for Production

```bash
cd "Frontend interface Ai assistant/Ai UI interface"
npm install
npm run build
```

The built files will be in the `dist` directory, ready to deploy.

## Common Issues

| Issue | Solution |
|-------|----------|
| **Connection Error** | Check if backend is running, verify environment variables |
| **CORS Errors** | Add CORS headers to backend responses |
| **LiveKit Connection Failed** | Verify LiveKit URL and token are correct in backend |
| **Empty Response** | Backend may not have environment variables set |
| **Audio Not Working** | Check browser permissions, enable audio playback |

## API Endpoints Expected

The frontend expects these backend endpoints:

- `GET /healthz` - Health check
- `GET /livekit/config` - Get LiveKit WebRTC credentials  
- `GET /usage/groq` - Get Groq API usage stats
- `GET /usage/elevenlabs` - Get ElevenLabs usage stats

All endpoints should be served from the same origin (e.g., `https://your-railway-domain.up.railway.app`)
