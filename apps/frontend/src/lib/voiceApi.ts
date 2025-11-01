/**
 * Voice API client for transcription and synthesis.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface TranscribeResponse {
  success: boolean
  text: string
  duration?: number
  language?: string
}

export interface SynthesizeRequest {
  text: string
  voice_id?: string
}

/**
 * Transcribe audio to text using Whisper.
 */
export async function transcribeAudio(
  audioBlob: Blob,
  token: string,
  language: string = 'en'
): Promise<TranscribeResponse> {
  const url = `${API_URL}/voice/transcribe`
  console.log(`🌐 [voiceApi] Transcribing to: ${url}`)
  console.log(`📦 [voiceApi] Blob size: ${audioBlob.size} bytes, type: ${audioBlob.type}`)

  const formData = new FormData()
  formData.append('audio', audioBlob, 'recording.webm')
  formData.append('language', language)

  const response = await fetch(url, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      // Don't set Content-Type - browser sets it with boundary for FormData
    },
    body: formData,
  })

  console.log(`📡 [voiceApi] Response status: ${response.status} ${response.statusText}`)

  if (!response.ok) {
    const errorText = await response.text()
    console.error(`❌ [voiceApi] Transcription error response:`, errorText)

    let errorDetail = 'Transcription failed'
    try {
      const errorJson = JSON.parse(errorText)
      errorDetail = errorJson.detail || errorDetail
    } catch {
      errorDetail = errorText || errorDetail
    }

    throw new Error(errorDetail)
  }

  const result = await response.json()
  console.log(`✅ [voiceApi] Transcription success:`, result.text?.substring(0, 50) + '...')
  return result
}

/**
 * Convert text to speech using ElevenLabs.
 * Returns a Blob URL that can be played with Audio element.
 */
export async function synthesizeSpeech(
  text: string,
  token: string,
  voiceId?: string
): Promise<string> {
  const response = await fetch(`${API_URL}/voice/synthesize`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text, voice_id: voiceId }),
  })
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Speech synthesis failed' }))
    throw new Error(error.detail || 'Failed to generate speech')
  }
  
  // Get audio blob
  const audioBlob = await response.blob()
  
  // Create object URL
  const audioUrl = URL.createObjectURL(audioBlob)
  
  return audioUrl
}

/**
 * Save voice transcript to database.
 */
export async function saveVoiceTranscript(
  sessionId: string,
  userTranscript: string,
  aiResponse: string,
  duration: number | undefined,
  token: string
): Promise<void> {
  try {
    await fetch(`${API_URL}/voice/save-transcript`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: sessionId,
        user_audio_transcript: userTranscript,
        ai_response_text: aiResponse,
        duration_seconds: duration,
      }),
    })
  } catch (err) {
    // Don't fail the request if saving transcript fails
    console.error('Failed to save transcript:', err)
  }
}

