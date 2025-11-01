/**
 * Audio playback hook for playing AI voice responses.
 * Handles audio element management, playback control, and cleanup.
 */

import { useState, useRef, useCallback, useEffect } from 'react'

interface UseAudioPlayerReturn {
  isPlaying: boolean
  currentTime: number
  duration: number
  play: (audioUrl: string) => Promise<void>
  pause: () => void
  stop: () => void
  seek: (time: number) => void
  error: string | null
}

export function useAudioPlayer(): UseAudioPlayerReturn {
  const [isPlaying, setIsPlaying] = useState(false)
  const [currentTime, setCurrentTime] = useState(0)
  const [duration, setDuration] = useState(0)
  const [error, setError] = useState<string | null>(null)
  
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const urlRef = useRef<string | null>(null)

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      if (urlRef.current) {
        URL.revokeObjectURL(urlRef.current)
        urlRef.current = null
      }
    }
  }, [])

  const play = useCallback(async (audioUrl: string) => {
    try {
      setError(null)
      
      // Stop current audio if playing
      if (audioRef.current) {
        audioRef.current.pause()
        audioRef.current = null
      }
      
      // Revoke old URL
      if (urlRef.current) {
        URL.revokeObjectURL(urlRef.current)
      }
      
      // Create new audio element
      const audio = new Audio(audioUrl)
      audioRef.current = audio
      urlRef.current = audioUrl
      
      // Event listeners
      audio.onloadedmetadata = () => {
        setDuration(audio.duration)
      }
      
      audio.ontimeupdate = () => {
        setCurrentTime(audio.currentTime)
      }
      
      audio.onplay = () => {
        setIsPlaying(true)
        console.log('🔊 Audio playing')
      }
      
      audio.onpause = () => {
        setIsPlaying(false)
        console.log('⏸️ Audio paused')
      }
      
      audio.onended = () => {
        setIsPlaying(false)
        setCurrentTime(0)
        console.log('✅ Audio ended')
      }
      
      audio.onerror = (e) => {
        console.error('Audio playback error:', e)
        setError('Failed to play audio. Please try again.')
        setIsPlaying(false)
      }
      
      // Play audio
      await audio.play()
      
    } catch (err) {
      console.error('Audio play error:', err)
      
      if (err instanceof Error && err.name === 'NotAllowedError') {
        setError('Browser blocked audio playback. Please interact with the page first.')
      } else {
        setError('Could not play audio. Please try again.')
      }
      
      setIsPlaying(false)
    }
  }, [])

  const pause = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
    }
  }, [])

  const stop = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current.currentTime = 0
      setCurrentTime(0)
      setIsPlaying(false)
    }
  }, [])

  const seek = useCallback((time: number) => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, Math.min(time, duration))
    }
  }, [duration])

  return {
    isPlaying,
    currentTime,
    duration,
    play,
    pause,
    stop,
    seek,
    error
  }
}

