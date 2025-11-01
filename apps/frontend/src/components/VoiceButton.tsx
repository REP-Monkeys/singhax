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
    setError(null)
    setTranscript('')
    await recorder.startRecording()
    setMode('recording')
  }

  const handleStopRecording = async () => {
    const audioBlob = await recorder.stopRecording()
    
    if (!audioBlob) {
      setError('Failed to capture audio')
      setMode('idle')
      return
    }
    
    // Check size
    const sizeMB = audioBlob.size / (1024 * 1024)
    if (sizeMB > 5) {
      setError('Recording too long. Please keep it under 5MB (about 2 minutes).')
      setMode('idle')
      return
    }
    
    setMode('processing')
    
    try {
      // Step 1: Get auth token
      const { data: { session } } = await supabase.auth.getSession()
      const token = session?.access_token
      
      if (!token) {
        throw new Error('Not authenticated. Please log in.')
      }
      
      // Step 2: Transcribe audio
      console.log('🎤 Transcribing audio...')
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
      
      // Step 5: Synthesize and play response
      setMode('speaking')
      
      console.log('🔊 Generating speech...')
      const audioUrl = await synthesizeSpeech(aiResponse, token)
      
      // Play audio
      await player.play(audioUrl)
      
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
        <Button
          onClick={handleStartRecording}
          size="sm"
          variant="outline"
          className="gap-2 rounded-full h-10 w-10 p-0"
          title="Speak your question"
        >
          <Mic className="w-4 h-4" />
        </Button>
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
