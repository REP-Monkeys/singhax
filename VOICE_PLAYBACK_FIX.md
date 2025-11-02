# ElevenLabs Voice Playback Fix

## Issue
ElevenLabs voice was not playing back in the browser.

## Root Cause
The voice API endpoints were being called **without the required `/api/v1` prefix**:
- ❌ `http://localhost:8000/voice/synthesize` (incorrect)
- ✅ `http://localhost:8000/api/v1/voice/synthesize` (correct)

This caused 404 errors when trying to generate speech, preventing audio playback.

## Files Fixed

### 1. `apps/frontend/src/lib/voiceApi.ts`
Fixed all three voice endpoint URLs to include `/api/v1` prefix:

```typescript
// Before:
const url = `${API_URL}/voice/transcribe`
const url = `${API_URL}/voice/synthesize`
const url = `${API_URL}/voice/save-transcript`

// After:
const url = `${API_URL}/api/v1/voice/transcribe`
const url = `${API_URL}/api/v1/voice/synthesize`
const url = `${API_URL}/api/v1/voice/save-transcript`
```

**Additional improvements:**
- Added comprehensive logging for TTS requests
- Added blob size and type logging for debugging
- Added audio URL logging

### 2. `apps/frontend/src/hooks/useAudioPlayer.ts`
Enhanced with detailed debugging logs to help diagnose future audio issues:
- Added loading state logs (`onloadstart`, `onloadeddata`, `oncanplay`, etc.)
- Added detailed error logging with error codes and messages
- Added better error messages for different failure scenarios
- Improved visibility into the audio playback lifecycle

## Configuration Verified
✅ `ENABLE_TTS=true` in `.env`
✅ `ELEVENLABS_API_KEY` is present and valid
✅ Backend correctly loads TTS configuration

## Testing
To test the voice playback:
1. Start the backend: `cd apps/backend && source venv/bin/activate && python -m uvicorn app.main:app --reload`
2. Start the frontend: `cd apps/frontend && npm run dev`
3. Login to the app
4. Click the microphone button and speak
5. The AI response should now play back with ElevenLabs voice

## Debugging
If voice still doesn't play, check the browser console for:
- `🔊 [voiceApi] TTS request to:` - Should show correct URL with `/api/v1`
- `📦 [voiceApi] Audio blob received:` - Should show non-zero bytes
- `🎵 [useAudioPlayer] Starting playback...` - Shows playback attempt
- Any error messages with details about what failed

## Related Files
- Backend voice router: `apps/backend/app/routers/voice.py`
- Backend config: `apps/backend/app/core/config.py`
- Voice integration docs: `VOICE_INTEGRATION_MAP.md`, `VOICE_FEATURE_COMPLETE.md`

