'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Mic, Square, Volume2, Loader2 } from 'lucide-react'
import { useAudioRecorder } from '@/hooks/useAudioRecorder'
import { useAudioPlayer } from '@/hooks/useAudioPlayer'
import { transcribeAudio, synthesizeSpeech, saveVoiceTranscript } from '@/lib/voiceApi'
import { supabase } from '@/lib/supabase'

interface VoiceButtonProps {
  sessionId: string
  onTranscript: (text: string) => Promise<void>
  onRequestResponse: () => Promise<string> // Gets AI response after sending transcript
  isActive: boolean
  onActiveChange: (active: boolean) => void
}

export function VoiceButton({
  sessionId,
  onTranscript,
  onRequestResponse,
  isActive,
  onActiveChange
}: VoiceButtonProps) {
  const [mode, setMode] = useState<'idle' | 'recording' | 'processing' | 'speaking'>('idle')
  const [transcript, setTranscript] = useState('')
  const [error, setError] = useState<string | null>(null)
  
  const recorder = useAudioRecorder()
  const player = useAudioPlayer()

  // Sync isActive with internal state
  useEffect(() => {
    const newActive = mode !== 'idle'
    if (newActive !== isActive) {
      onActiveChange(newActive)
    }
  }, [mode, isActive, onActiveChange])

  const handleStartRecording = async () => {
    console.log('🎤 [VoiceButton] Starting recording...')
    setError(null)
    setTranscript('')

    try {
      await recorder.startRecording()
      setMode('recording')
      console.log('✅ [VoiceButton] Recording started successfully')
    } catch (err) {
      console.error('❌ [VoiceButton] Failed to start recording:', err)
      setError('Failed to start recording. Please check microphone permissions.')
      setMode('idle')
    }
  }

  const handleStopRecording = async () => {
    console.log('⏹️ [VoiceButton] Stopping recording...')
    const audioBlob = await recorder.stopRecording()

    if (!audioBlob) {
      console.error('❌ [VoiceButton] No audio blob returned')
      setError('Failed to capture audio')
      setMode('idle')
      return
    }

    // Check size
    const sizeMB = audioBlob.size / (1024 * 1024)
    console.log(`📊 [VoiceButton] Audio blob size: ${sizeMB.toFixed(2)}MB, type: ${audioBlob.type}`)

    if (sizeMB > 5) {
      setError('Recording too long. Please keep it under 5MB (about 2 minutes).')
      setMode('idle')
      return
    }

    setMode('processing')

    try {
      // Step 1: Get auth token
      console.log('🔑 [VoiceButton] Getting auth token...')
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token

      if (!token) {
        throw new Error('Not authenticated. Please log in.')
      }
      console.log('✅ [VoiceButton] Auth token obtained')

      // Step 2: Transcribe audio
      console.log('🎤 [VoiceButton] Transcribing audio...')
      const transcribeResult = await transcribeAudio(audioBlob, token)
      
      if (!transcribeResult.success || !transcribeResult.text) {
        throw new Error('Could not understand audio. Please try again.')
      }
      
      const userText = transcribeResult.text
      setTranscript(userText)
      console.log(`✅ Transcribed: ${userText}`)
      
      // Step 3: Send transcript to chat (parent handles)
      await onTranscript(userText)
      
      // Step 4: Get AI response from parent
      const aiResponse = await onRequestResponse()
      
      if (!aiResponse) {
        throw new Error('No response from AI')
      }
      
      console.log(`💬 AI Response: ${aiResponse.substring(0, 50)}...`)
      
      // Step 5: Synthesize and play response (if TTS is enabled)
      try {
        setMode('speaking')

        console.log('🔊 Generating speech...')
        const audioUrl = await synthesizeSpeech(aiResponse, token)

        // Play audio
        await player.play(audioUrl)
      } catch (ttsError: any) {
        // If TTS is disabled (503), just skip audio playback
        if (ttsError.message?.includes('disabled') || ttsError.message?.includes('conserved')) {
          console.log('ℹ️  TTS disabled - skipping audio playback')
          setMode('idle')
          setTranscript('')

          // Auto-start recording for next question after 1 second delay
          setTimeout(() => {
            handleStartRecording()
          }, 1000)

          return // Skip the rest of audio handling
        } else {
          // Re-throw other errors
          throw ttsError
        }
      }
      
      // Step 6: Save transcript
      await saveVoiceTranscript(
        sessionId,
        userText,
        aiResponse,
        transcribeResult.duration,
        token
      )
      
      // Step 7: Wait for audio to finish
      const checkEnded = setInterval(() => {
        if (!player.isPlaying) {
          clearInterval(checkEnded)
          console.log('✅ Audio ended, ready for next question')
          setMode('idle')
          setTranscript('')
          
          // Auto-start recording for next question after 1 second delay
          setTimeout(() => {
            handleStartRecording()
          }, 1000)
        }
      }, 100)
      
    } catch (err) {
      console.error('Voice processing error:', err)
      setError(err instanceof Error ? err.message : 'Failed to process audio')
      setMode('idle')
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="flex flex-col items-center gap-2">
      {/* Main Button */}
      {mode === 'idle' && (
        <button
          onClick={handleStartRecording}
          className="border-2 rounded-full h-10 w-10 p-0 flex items-center justify-center hover:bg-red-50 transition-colors"
          style={{ borderColor: '#dd2930', color: '#dd2930' }}
          title="Speak your question"
        >
          <Mic className="w-4 h-4" stroke="#dd2930" strokeWidth={2} style={{ color: '#dd2930' }} />
        </button>
      )}
      
      {mode === 'recording' && (
        <Button
          onClick={handleStopRecording}
          size="sm"
          variant="destructive"
          className="gap-2 animate-pulse rounded-full h-10 px-4"
          title="Stop recording"
        >
          <Square className="w-4 h-4" />
          <span className="text-xs">{formatTime(recorder.recordingTime)}</span>
        </Button>
      )}
      
      {mode === 'processing' && (
        <Button
          size="sm"
          variant="outline"
          disabled
          className="gap-2 rounded-full h-10 w-10 p-0"
          title="Processing..."
        >
          <Loader2 className="w-4 h-4 animate-spin" />
        </Button>
      )}
      
      {mode === 'speaking' && (
        <Button
          onClick={() => {
            player.stop()
            setMode('idle')
          }}
          size="sm"
          variant="outline"
          className="gap-2 rounded-full h-10 w-10 p-0 animate-pulse"
          title="Speaking... (click to stop)"
        >
          <Volume2 className="w-4 h-4" />
        </Button>
      )}
      
      {/* Transcript Display (only show during processing/speaking) */}
      {transcript && mode !== 'idle' && (
        <div className="text-xs text-gray-600 max-w-xs text-center italic">
          "{transcript}"
        </div>
      )}
      
      {/* Error Display */}
      {(error || recorder.error || player.error) && (
        <div className="text-xs text-red-600 max-w-xs text-center">
          {error || recorder.error || player.error}
        </div>
      )}
    </div>
  )
}
