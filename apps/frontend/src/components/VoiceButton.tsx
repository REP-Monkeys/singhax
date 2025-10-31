'use client'

import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Mic, MicOff } from 'lucide-react'

interface VoiceButtonProps {
  onTranscript: (transcript: string) => void
  isActive: boolean
  onActiveChange: (active: boolean) => void
}

// Extend Window interface for speech recognition
declare global {
  interface Window {
    SpeechRecognition: any
    webkitSpeechRecognition: any
  }
}

export function VoiceButton({ onTranscript, isActive, onActiveChange }: VoiceButtonProps) {
  const [isRecording, setIsRecording] = useState(false)
  const [transcript, setTranscript] = useState('')
  const recognitionRef = useRef<any>(null)

  const startRecording = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      alert('Speech recognition is not supported in this browser')
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    recognitionRef.current = new SpeechRecognition()
    
    recognitionRef.current.continuous = true
    recognitionRef.current.interimResults = true
    recognitionRef.current.lang = 'en-US'

    recognitionRef.current.onstart = () => {
      setIsRecording(true)
      onActiveChange(true)
    }

    recognitionRef.current.onresult = (event: any) => {
      let finalTranscript = ''
      let interimTranscript = ''

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript
        if (event.results[i].isFinal) {
          finalTranscript += transcript
        } else {
          interimTranscript += transcript
        }
      }

      setTranscript(finalTranscript + interimTranscript)
    }

    recognitionRef.current.onend = () => {
      setIsRecording(false)
      onActiveChange(false)
      if (transcript.trim()) {
        onTranscript(transcript.trim())
        setTranscript('')
      }
    }

    recognitionRef.current.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error)
      setIsRecording(false)
      onActiveChange(false)
    }

    recognitionRef.current.start()
  }

  const stopRecording = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
  }

  const handleClick = () => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return (
    <Button
      variant={isRecording ? "destructive" : "outline"}
      size="sm"
      onClick={handleClick}
      className={`transition-colors ${
        isRecording ? 'animate-pulse' : ''
      }`}
    >
      {isRecording ? (
        <MicOff className="w-4 h-4" />
      ) : (
        <Mic className="w-4 h-4" />
      )}
    </Button>
  )
}
