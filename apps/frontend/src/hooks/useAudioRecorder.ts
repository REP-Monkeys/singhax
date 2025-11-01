/**
 * Audio recording hook using MediaRecorder API.
 * Handles microphone access, recording, and audio blob creation.
 */

import { useState, useRef, useCallback } from 'react'

interface UseAudioRecorderReturn {
  isRecording: boolean
  isPaused: boolean
  recordingTime: number
  startRecording: () => Promise<void>
  stopRecording: () => Promise<Blob | null>
  pauseRecording: () => void
  resumeRecording: () => void
  error: string | null
}

export function useAudioRecorder(): UseAudioRecorderReturn {
  const [isRecording, setIsRecording] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [recordingTime, setRecordingTime] = useState(0)
  const [error, setError] = useState<string | null>(null)
  
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const timerRef = useRef<NodeJS.Timeout | null>(null)

  const startRecording = useCallback(async () => {
    try {
      setError(null)
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      })
      
      streamRef.current = stream
      
      // Create MediaRecorder with webm format (Chrome support)
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      // Collect audio chunks
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }
      
      // Start recording
      mediaRecorder.start(100) // Collect data every 100ms
      setIsRecording(true)
      
      // Start timer
      setRecordingTime(0)
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
      console.log('🎤 Recording started')
      
    } catch (err) {
      console.error('Microphone access error:', err)
      
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError') {
          setError('Microphone access denied. Please allow microphone access in browser settings.')
        } else if (err.name === 'NotFoundError') {
          setError('No microphone found. Please connect a microphone.')
        } else {
          setError('Could not access microphone. Please try again.')
        }
      }
    }
  }, [])

  const stopRecording = useCallback((): Promise<Blob | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current || !isRecording) {
        resolve(null)
        return
      }
      
      const mediaRecorder = mediaRecorderRef.current
      
      mediaRecorder.onstop = () => {
        // Create audio blob from chunks
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: 'audio/webm;codecs=opus' 
        })
        
        console.log(`🎤 Recording stopped. Size: ${(audioBlob.size / 1024).toFixed(2)}KB`)
        
        // Clean up
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop())
          streamRef.current = null
        }
        
        if (timerRef.current) {
          clearInterval(timerRef.current)
          timerRef.current = null
        }
        
        setIsRecording(false)
        setIsPaused(false)
        
        resolve(audioBlob)
      }
      
      mediaRecorder.stop()
    })
  }, [isRecording])

  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording && !isPaused) {
      mediaRecorderRef.current.pause()
      setIsPaused(true)
      
      if (timerRef.current) {
        clearInterval(timerRef.current)
      }
      
      console.log('⏸️ Recording paused')
    }
  }, [isRecording, isPaused])

  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording && isPaused) {
      mediaRecorderRef.current.resume()
      setIsPaused(false)
      
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1)
      }, 1000)
      
      console.log('▶️ Recording resumed')
    }
  }, [isRecording, isPaused])

  return {
    isRecording,
    isPaused,
    recordingTime,
    startRecording,
    stopRecording,
    pauseRecording,
    resumeRecording,
    error
  }
}

