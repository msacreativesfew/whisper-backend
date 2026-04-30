# Railway Deployment Guide for Whisper Backend

## Issues Fixed

### 1. **Port Mismatch (Critical)**
- **Problem**: Dockerfile was exposing port 7860 (for Hugging Face), but the app runs on port 8000
- **Fix**: Updated Dockerfile to expose port 8000, matching Railway's $PORT environment variable
- **Status**: ✅ FIXED

### 2. **Environment Configuration**
- **Problem**: Railway needs proper PORT handling and health check endpoint support
- **Fix**: Created `railway.json` configuration file for proper Railway detection
- **Status**: ✅ FIXED

### 3. **Startup Script Improvements**
- **Problem**: Voice agent failures could prevent health checks from passing
- **Fix**: Updated `start.sh` to run API independently and handle voice agent failures gracefully
- **Status**: ✅ IMPROVED

## Deployment Steps

### 1. Check Environment Variables in Railway Dashboard
Make sure all these variables are set in your Railway project:
- `LIVEKIT_URL` - Your LiveKit project URL
- `LIVEKIT_API_KEY` - LiveKit API key
- `LIVEKIT_API_SECRET` - LiveKit API secret
- `GROQ_API_KEY_1` - Groq API key
- `DEEPGRAM_API_KEY` - Deepgram STT API key
- `SUPABASE_URL` - Supabase database URL
- `SUPABASE_API_KEY` - Supabase API key
- `GOOGLE_CREDENTIALS_JSON` - Google Cloud credentials
- `GOOGLE_TOKEN_JSON` - Google OAuth token (optional)

### 2. Test the Deployment
```bash
# Check if the API is responding
curl https://whisper-backend-production-77ec.up.railway.app/healthz

# You should see a response indicating the API is healthy
```

### 3. Verify Health Check
The app has a health endpoint at `/healthz` that returns:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

### 4. Check Logs in Railway Dashboard
Go to Railway Dashboard → Your Project → Logs to see:
- Build logs (dependency installation)
- Runtime logs (startup and API responses)

## Common Issues & Solutions

### Issue: "502 Bad Gateway"
**Causes:**
1. Port mismatch (FIXED - port should now be 8000)
2. App crashed during startup
3. Missing environment variables

**Solution:**
- Check Railway logs for startup errors
- Verify all required environment variables are set
- Ensure Dockerfile PORT is set correctly (should be 8000)

### Issue: "Connection Refused"
**Cause:** App not listening on the correct port

**Solution:**
- Verify PORT environment variable in Railway: `echo $PORT`
- Check `start.sh` is setting the port correctly
- Confirm Dockerfile EXPOSE matches the PORT variable

### Issue: Voice Agent Failing
**Cause:** LiveKit, Groq, or Deepgram credentials are missing/invalid

**Solution:**
- This won't affect the API anymore (voice agent runs independently)
- Check that at least one STT provider (Deepgram or Groq) is configured
- Verify credentials in Railway environment variables

## Testing the API

### Root Endpoint
```bash
curl https://whisper-backend-production-77ec.up.railway.app/
```

### Health Check Endpoint
```bash
curl https://whisper-backend-production-77ec.up.railway.app/healthz
```

### LiveKit Config Endpoint (requires proper setup)
```bash
curl https://whisper-backend-production-77ec.up.railway.app/livekit/config
```

## Files Modified for Railway Compatibility

1. **Dockerfile**
   - Changed EXPOSE from 7860 → 8000
   - Removed hardcoded PORT environment variable

2. **start.sh**
   - Added better logging
   - Made voice agent failure non-blocking
   - API continues running even if voice agent fails

3. **railway.json** (NEW)
   - Proper Railway configuration
   - Uses Dockerfile for builds
   - Specifies start command

## Next Steps

1. Push these changes to your GitHub repo
2. Railway will automatically detect and rebuild
3. Check the deployment logs in Railway dashboard
4. Test the endpoints after deployment

## Support Resources

- LiveKit Docs: https://docs.livekit.io
- Railway Docs: https://docs.railway.app
- Groq API: https://console.groq.com
- Deepgram STT: https://console.deepgram.com
