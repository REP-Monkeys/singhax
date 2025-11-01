'use client'

import { useState, useRef, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Mic, MicOff, Send, User, Bot, Phone, LogOut, ArrowLeft, FileText, Upload, Plane } from 'lucide-react'
import { CopilotPanel } from '@/components/CopilotPanel'
import { VoiceButton } from '@/components/VoiceButton'
import { ExtractedDataCard } from '@/components/ExtractedDataCard'
import { FileAttachment } from '@/components/FileAttachment'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'
import { usePaymentPolling } from '@/hooks/usePaymentPolling'

interface FileAttachmentData {
  filename: string
  fileType?: string
  size?: number
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: Date
  extractedData?: any  // Extracted JSON data from OCR
  fileAttachment?: FileAttachmentData  // File attachment for user messages
  documentId?: string  // Document ID for editing extracted data
}

interface TripDetails {
  destination?: string
  departure_date?: string
  return_date?: string
  area?: string
  base_rate?: number
}

interface TravelersData {
  count?: number
  ages?: number[]
}

interface Preferences {
  adventure_sports?: boolean
}

interface QuoteData {
  destination?: string
  departure_date?: string
  return_date?: string
  quotes?: {
    standard?: { total_premium: number }
    elite?: { total_premium: number }
    premier?: { total_premium: number }
  }
}

interface ConversationState {
  current_intent?: string
  trip_details?: TripDetails
  travelers_data?: TravelersData
  preferences?: Preferences
  quote_data?: QuoteData
}

// Utility function to extract Stripe checkout URLs from text
function extractStripeCheckoutUrl(text: string): string | null {
  // Match Stripe checkout URLs - more flexible pattern to catch URLs with various endings
  const stripeUrlPattern = /https:\/\/checkout\.stripe\.com\/[^\s\)\]\.,!?<>"]+/gi
  const match = text.match(stripeUrlPattern)
  return match ? match[0] : null
}

// Utility function to extract all URLs from text
function extractUrls(text: string): string[] {
  const urlPattern = /https?:\/\/[^\s\)]+/gi
  return text.match(urlPattern) || []
}

// Component to render message content with clickable URLs
function MessageContent({ content }: { content: string }) {
  const stripeCheckoutUrl = extractStripeCheckoutUrl(content)
  const allUrls = extractUrls(content)
  
  // If there's a Stripe checkout URL, extract it and render specially
  if (stripeCheckoutUrl) {
    // Split content at the Stripe URL (escape special regex characters)
    const escapedUrl = stripeCheckoutUrl.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const parts = content.split(new RegExp(escapedUrl, 'i'))
    
    return (
      <div className="space-y-3">
        {/* Render text before URL */}
        {parts[0] && parts[0].trim() && (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{parts[0]}</p>
        )}
        {/* Stripe checkout button */}
        <a
          href={stripeCheckoutUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-block text-white font-semibold px-6 py-3 rounded-lg transition-colors shadow-md hover:opacity-90"
          style={{ backgroundColor: '#dd2930' }}
        >
          Proceed to Payment
        </a>
        {/* Render text after URL */}
        {parts[1] && parts[1].trim() && (
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{parts[1]}</p>
        )}
      </div>
    )
  }
  
  // Render regular content with clickable URLs
  if (allUrls.length > 0) {
    const parts = content.split(/(https?:\/\/[^\s\)]+)/gi)
    return (
      <p className="text-sm leading-relaxed whitespace-pre-wrap">
        {parts.map((part, index) => {
          if (part.match(/^https?:\/\//i)) {
            return (
              <a
                key={index}
                href={part}
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-600 hover:text-indigo-800 underline break-all"
              >
                {part}
              </a>
            )
          }
          return <span key={index}>{part}</span>
        })}
      </p>
    )
  }
  
  // No URLs, render plain text
  return <p className="text-sm leading-relaxed whitespace-pre-wrap">{content}</p>
}

export default function QuotePage() {
  const { user, logout } = useAuth()
  const searchParams = useSearchParams()
  const router = useRouter()
  const sessionIdParam = searchParams.get('session')

  const [currentSessionId, setCurrentSessionId] = useState<string | null>(sessionIdParam)
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      role: 'assistant',
      content: "Hi! I'm your travel insurance assistant. I can help you get a quote, explain your policy, or assist with claims. What would you like to do today?",
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isLoadingHistory, setIsLoadingHistory] = useState(false)
  const [isVoiceActive, setIsVoiceActive] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [conversationState, setConversationState] = useState<ConversationState>({})
  const [selectedFile, setSelectedFile] = useState<File | null>(null) // File selected but not yet uploaded
  const [awaitingPayment, setAwaitingPayment] = useState(false) // Track if waiting for payment completion
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // Poll for payment completion and auto-refresh chat
  usePaymentPolling({
    sessionId: currentSessionId,
    onPaymentComplete: async () => {
      console.log('🎉 Payment completed! Reloading chat history...')
      if (currentSessionId) {
        await loadChatHistory(currentSessionId)
        setAwaitingPayment(false)
        // Optional: Show a success notification
        const successMsg: Message = {
          id: Date.now().toString(),
          role: 'assistant',
          content: '🎉 Payment confirmed! Your policy details are being loaded...',
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMsg])
      }
    },
    enabled: awaitingPayment
  })

  // Parse plan information from message content
  const parsePlans = (content: string) => {
    console.log('🔍 [parsePlans] Parsing content:', content.substring(0, 500))
    const plans: Array<{
      name: string
      price: string
      features: string[]
      emoji: string
    }> = []

    // Match plan patterns - more flexible pattern to catch emojis
    const planPattern = /([\u{1F300}-\u{1F9FF}])\s?\*\*([^:]+):\s*\$\s*([0-9,]+\.?\d*)\s*SGD\*\*([\s\S]*?)(?=\n\n[\u{1F300}-\u{1F9FF}]\s?\*\*|\n\n[A-Z💡📊]|\n\nAll prices|$)/gu
    
    let match
    let matchCount = 0
    while ((match = planPattern.exec(content)) !== null) {
      matchCount++
      console.log(`🔍 [parsePlans] Match #${matchCount}:`, {
        emoji: match[1],
        name: match[2],
        price: match[3]
      })
      let emoji = match[1]
      const name = match[2].trim()
      const price = `$${match[3]} SGD`
      const featuresText = match[4] || ''
      
      // Fallback emoji mapping if extraction fails
      if (!emoji || emoji === '◆') {
        if (name.toLowerCase().includes('standard')) emoji = '🌟'
        else if (name.toLowerCase().includes('elite')) emoji = '⭐'
        else if (name.toLowerCase().includes('premier')) emoji = '👑'
      }
      
      // Extract features (lines starting with ✓ or *)
      const features = featuresText
        .split('\n')
        .map(line => line.trim())
        .filter(line => line.startsWith('✓') || (line.startsWith('*') && !line.startsWith('**')))
        .map(line => line.replace(/^[✓*]\s*/, '').replace(/\*\*/g, '').trim())
        .filter(line => line.length > 0 && !line.includes('All prices'))

      if (features.length > 0 || name.includes('Plan')) {
        plans.push({ name, price, features, emoji })
        console.log(`✅ [parsePlans] Added plan:`, { name, price, emoji, featureCount: features.length })
      }
    }

    console.log(`🔍 [parsePlans] Total plans parsed: ${plans.length}`)
    return plans
  }

  // Split message content into intro, plans, and outro
  const splitMessageContent = (content: string) => {
    const plans = parsePlans(content)
    
    if (plans.length === 0) {
      return { intro: content, plans: [], outro: '' }
    }

    // Find where plans section starts and ends
    const firstPlanIndex = content.search(/[\u{1F300}-\u{1F9FF}]\s?\*\*/u)
    const outroStartIndex = content.indexOf('\n\nAll prices')
    
    const intro = firstPlanIndex > 0 ? content.substring(0, firstPlanIndex).trim() : ''
    const outro = outroStartIndex > 0 ? content.substring(outroStartIndex).trim() : content.substring(content.lastIndexOf('All prices') > -1 ? content.lastIndexOf('All prices') : content.length).trim()
    
    return { intro, plans, outro }
  }

  const loadChatHistory = async (sessionId?: string) => {
    const targetSessionId = sessionId || sessionIdParam
    if (!targetSessionId) return

    setIsLoadingHistory(true)
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const token = await getAuthToken()
      
      if (!token) {
        throw new Error('No authentication token available. Please log in again.')
      }
      
      console.log('🔍 Loading chat history for session:', targetSessionId)
      const response = await fetch(`${API_URL}/chat/session/${targetSessionId}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        // Try to get error details from response
        let errorMessage = 'Failed to load chat history'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch (e) {
          try {
            const errorText = await response.text()
            errorMessage = errorText || errorMessage
          } catch (e2) {
            errorMessage = `Failed to load chat history: ${response.status} ${response.statusText}`
          }
        }
        console.error('❌ Chat history load error:', {
          status: response.status,
          statusText: response.statusText,
          error: errorMessage
        })
        throw new Error(errorMessage)
      }

      const data = await response.json()

      console.log('📂 Loaded session data:', data)
      console.log('📂 Session state:', data.state)

      // Transform messages from API format to component format
      if (data.messages && data.messages.length > 0) {
        // Check if there's document_data in state that we can attach to messages
        const documentData = data.state?.document_data || []
        
        const transformedMessages = data.messages.map((msg: any, idx: number) => {
          const message: Message = {
            id: `${idx}`,
            role: msg.role,
            content: msg.content,
            timestamp: new Date()
          }
          
          // If this is an assistant message, check if it follows a document upload
          if (msg.role === 'assistant' && documentData.length > 0) {
            // Check if previous message was a document upload
            const prevMsg = idx > 0 ? data.messages[idx - 1] : null
            const isAfterDocumentUpload = prevMsg && 
              prevMsg.role === 'user' && 
              (prevMsg.content?.includes('[User uploaded a document') || 
               prevMsg.content?.toLowerCase().includes('uploaded a document'))
            
            // Also check if this message mentions extracted details (e.g., "I've extracted", "extracted information")
            const mentionsExtraction = msg.content && (
              msg.content.includes('extracted') ||
              msg.content.includes('extraction') ||
              msg.content.includes('I\'ve extracted') ||
              msg.content.includes('extracted the following')
            )
            
            // Attach extractedData if this message is about document extraction
            if (isAfterDocumentUpload || mentionsExtraction) {
              // Find the most recent document that matches
              // Try to match by checking if message mentions the filename or use latest
              const latestDoc = documentData[documentData.length - 1]
              if (latestDoc?.extracted_json) {
                message.extractedData = latestDoc.extracted_json
                console.log('🔍 [DEBUG] Attached extractedData to assistant message:', {
                  messageIndex: idx,
                  isAfterDocumentUpload,
                  mentionsExtraction,
                  extractedData: latestDoc.extracted_json
                })
              }
            }
          }
          
          return message
        })
        setMessages(transformedMessages)
      }

      // Extract and populate conversation state from session state
      if (data.state) {
        const state = data.state
        console.log('📊 Extracting state from session:', {
          trip_details: state.trip_details,
          travelers_data: state.travelers_data,
          preferences: state.preferences,
          quote_data: state.quote_data
        })

        // Populate conversationState similar to handleSendMessage
        setConversationState({
          current_intent: state.current_intent || undefined,
          trip_details: state.trip_details || {},
          travelers_data: state.travelers_data || {},
          preferences: state.preferences || {},
          quote_data: state.quote_data || undefined
        })

        console.log('✅ Populated conversationState from session history')
      }
    } catch (error: any) {
      console.error('❌ Error loading chat history:', error)
      
      // If session not found (404), show a helpful message but don't fail completely
      if (error.message && error.message.includes('not found')) {
        console.warn('⚠️ Session not found, starting fresh conversation')
        // Keep default welcome message - user can continue chatting
      } else {
        // For other errors, show error message to user
        const errorMessage: Message = {
          id: 'error-1',
          role: 'assistant',
          content: `I couldn't load your previous conversation. ${error.message || 'Please try refreshing the page or starting a new conversation.'}`,
          timestamp: new Date()
        }
        setMessages(prev => [prev[0], errorMessage]) // Keep welcome message, add error
      }
    } finally {
      setIsLoadingHistory(false)
    }
  }

  // Load chat history when session_id is provided (only once on mount or when session changes)
  useEffect(() => {
    if (sessionIdParam) {
      loadChatHistory()
    }
  }, [sessionIdParam])

  const getAuthToken = async (): Promise<string | null> => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
  }

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    // Validate file type
    const allowedTypes = ['application/pdf', 'image/png', 'image/jpeg', 'image/jpg']
    if (!allowedTypes.includes(file.type)) {
      alert('Please upload a PDF, PNG, or JPEG file')
      return
    }

    // Validate file size (10MB max)
    if (file.size > 10 * 1024 * 1024) {
      alert('File size must be less than 10MB')
      return
    }

    // Store file for preview (will upload when user sends message)
    setSelectedFile(file)
    
    // Reset file input so same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleFileUpload = async (file: File, userMessage?: string) => {
    setIsUploading(true)

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const token = await getAuthToken()
      
      if (!token) {
        throw new Error('No authentication token available. Please log in again.')
      }

      let sessionId = currentSessionId

      // Create new session if one doesn't exist
      if (!sessionId) {
        const sessionResponse = await fetch(`${API_URL}/chat/session`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        })

        if (!sessionResponse.ok) {
          throw new Error('Failed to create chat session')
        }

        const sessionData = await sessionResponse.json()
        sessionId = sessionData.session_id
        setCurrentSessionId(sessionId)
        // Update URL with session ID so it persists on refresh
        router.replace(`/app/quote?session=${sessionId}`, { scroll: false })
      }

      // Create form data
      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', sessionId)
      // Include user message if provided (this combines text and file as context)
      if (userMessage) {
        formData.append('user_message', userMessage)
      }

      // Upload file
      const uploadResponse = await fetch(`${API_URL}/chat/upload-image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      })

      if (!uploadResponse.ok) {
        const errorData = await uploadResponse.json().catch(() => ({ detail: 'Upload failed' }))
        throw new Error(errorData.detail || 'Failed to upload file')
      }

      const uploadData = await uploadResponse.json()

      // DEBUG: Log upload response to check extracted data
      console.log('🔍 [DEBUG] Upload response:', uploadData)
      console.log('🔍 [DEBUG] ocr_result:', uploadData.ocr_result)
      console.log('🔍 [DEBUG] extracted_json:', uploadData.ocr_result?.extracted_json)
      console.log('🔍 [DEBUG] Will set extractedData to:', uploadData.ocr_result?.extracted_json || null)

      // Add user message with file attachment and optional text (like ChatGPT)
      const userMessageObj: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: userMessage || '',  // Include user message if provided
        timestamp: new Date(),
        fileAttachment: {
          filename: file.name,
          fileType: file.type,
          size: file.size
        }
      }

      setMessages(prev => [...prev, userMessageObj])

      // Add assistant response with extracted data
      if (uploadData.message) {
        const extractedDataValue = uploadData.ocr_result?.extracted_json || null
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: uploadData.message,
          timestamp: new Date(),
          extractedData: extractedDataValue,
          documentId: uploadData.document_id || undefined  // Store document ID for editing
        }
        console.log('🔍 [DEBUG] Created assistant message with extractedData:', extractedDataValue)
        console.log('🔍 [DEBUG] Document ID:', uploadData.document_id)
        console.log('🔍 [DEBUG] Full assistant message:', assistantMessage)
        setMessages(prev => [...prev, assistantMessage])
        
        // Update conversation state from upload response if available
        // But DON'T reload history as it will overwrite extractedData
        if (uploadData.state) {
          setConversationState(uploadData.state)
        }
      } else {
        console.warn('⚠️ [DEBUG] uploadData.message is missing, not creating assistant message')
      }

      // NOTE: We don't reload chat history here because it would overwrite the extractedData
      // The uploaded message with extractedData is already added above
      // If you need to sync state, update conversationState directly instead

    } catch (error: any) {
      console.error('File upload error:', error)
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Sorry, I couldn't process your file: ${error.message || 'Unknown error'}`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsUploading(false)
      setSelectedFile(null) // Clear selected file after upload
    }
  }

  const handleRemoveFile = () => {
    setSelectedFile(null)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSendMessage = async () => {
    // If there's a selected file, upload it with text context (if provided)
    if (selectedFile) {
      const textToSend = inputValue.trim()
      await handleFileUpload(selectedFile, textToSend || undefined)
      setInputValue('') // Clear input after sending
      return
    }

    // No file, just send text message (require text if no file)
    if (!inputValue.trim() || isLoading) return
    handleSendTextMessage(inputValue)
    setInputValue('')
  }

  const handleSendTextMessage = async (text: string) => {
    if (!text.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const token = await getAuthToken()
      
      if (!token) {
        throw new Error('No authentication token available. Please log in again.')
      }
      
      let sessionId = currentSessionId

      // Create new session if one doesn't exist
      if (!sessionId) {
        const sessionResponse = await fetch(`${API_URL}/chat/session`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        })

        if (!sessionResponse.ok) {
          throw new Error('Failed to create chat session')
        }

        const sessionData = await sessionResponse.json()
        sessionId = sessionData.session_id
        setCurrentSessionId(sessionId)
        // Update URL with session ID so it persists on refresh
        router.replace(`/app/quote?session=${sessionId}`, { scroll: false })
      }

      // Send message to backend
      const messageResponse = await fetch(`${API_URL}/chat/message`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: text,
        }),
      })

      if (!messageResponse.ok) {
        let errorDetails = {
          status: messageResponse.status,
          statusText: messageResponse.statusText,
          body: null as any
        }
        
        try {
          errorDetails.body = await messageResponse.json()
        } catch (e) {
          try {
            errorDetails.body = await messageResponse.text()
          } catch (e2) {
            errorDetails.body = 'Unable to read response body'
          }
        }
        
        console.error('❌ API Error:', errorDetails)
        throw new Error(`Failed to send message: ${messageResponse.status} ${messageResponse.statusText}`)
      }

      const data = await messageResponse.json()

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.message,
        timestamp: new Date()
      }

      setMessages(prev => [...prev, assistantMessage])
      
      // Store last AI response for voice playback
      lastAIResponseRef.current = data.message

      // Note: Stripe checkout URL will be rendered as a button in MessageContent component
      // No auto-redirect - user clicks the button to open in new tab

      // Update conversation state for real-time UI updates
      if (data.state) {
        console.log('📊 Received state from backend:', data.state)
        console.log('📊 Quote data:', data.quote)

        setConversationState({
          current_intent: data.state.current_intent,
          trip_details: data.state.trip_details || {},
          travelers_data: data.state.travelers_data || {},
          preferences: data.state.preferences || {},
          quote_data: data.quote || undefined
        })

        console.log('✅ Updated conversationState:', {
          trip_details: data.state.trip_details,
          travelers_data: data.state.travelers_data,
          preferences: data.state.preferences,
          quote_data: data.quote
        })
      }
    } catch (error) {
      console.error('Error sending message:', error)

      // Show error message to user
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: "I'm sorry, I encountered an error processing your message. Please try again.",
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      // Allow sending if there's text OR a file attached
      if (inputValue.trim() || selectedFile) {
        handleSendMessage()
      }
    }
  }

  const lastAIResponseRef = useRef<string>('')

  const handleVoiceInput = async (transcript: string) => {
    // Voice mode: automatically send the transcript
    console.log('🎤 Voice input received:', transcript)
    await handleSendTextMessage(transcript)
  }
  
  const handleGetLastResponse = async (): Promise<string> => {
    // Return the last AI response for voice playback
    return lastAIResponseRef.current
  }

  return (
    <ProtectedRoute requireOnboarding={true}>
      <div className="min-h-screen" style={{ backgroundImage: 'linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%)' }}>
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-50 backdrop-blur-sm bg-white/95 shadow-md">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Link href="/app/dashboard">
                <Button variant="ghost" size="sm" className="text-gray-700 hover:text-black hover:bg-gray-100">
                  <ArrowLeft className="w-4 h-4 mr-1.5" />
                  Dashboard
                </Button>
              </Link>
              <div className="flex items-center gap-2">
                <Plane className="w-7 h-7" style={{ color: '#dd2930' }} />
                <h1 className="text-2xl font-semibold tracking-tight" style={{ color: '#dd2930' }}>TripMate</h1>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <span className="text-sm text-gray-600">Hi, {user?.name}</span>
              <Button variant="ghost" size="sm" className="text-gray-700 hover:text-black hover:bg-gray-100">
                <Phone className="w-4 h-4 mr-1.5" />
                Human support
              </Button>
              <Button variant="ghost" size="sm" className="text-gray-700 hover:text-black hover:bg-gray-100">
                My policies
              </Button>
              <Button variant="ghost" size="sm" onClick={logout} className="text-gray-700 hover:text-black hover:bg-gray-100">
                <LogOut className="w-4 h-4 mr-1.5" />
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <div className="border border-gray-200 rounded-2xl h-[calc(100vh-12rem)] flex flex-col bg-white shadow-sm">
              <div className="border-b border-gray-200 px-6 py-4">
                <div className="flex items-center">
                  <div className="flex items-center justify-center h-10 w-10 rounded-full mr-3" style={{ backgroundColor: '#dd2930' }}>
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-black">Insurance assistant</h2>
                    <p className="text-xs text-gray-500">Always here to help</p>
                  </div>
                </div>
              </div>
              <div className="flex-1 flex flex-col min-h-0">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 min-h-0">
                  {isLoadingHistory ? (
                    <div className="flex items-center justify-center py-16">
                      <div className="text-center">
                        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-black mb-3"></div>
                        <p className="text-sm text-gray-600">Loading conversation history...</p>
                      </div>
                    </div>
                  ) : (
                    <>
                  {messages.map((message) => (
                    <div key={message.id}>
                      <div
                        className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                      >
                        <div
                          className={`max-w-[75%] ${
                            message.role === 'user'
                              ? 'text-white rounded-2xl rounded-tr-sm'
                              : 'bg-gray-100 text-black rounded-2xl rounded-tl-sm'
                          } px-4 py-3`}
                          style={message.role === 'user' ? { backgroundColor: '#dd2930' } : undefined}
                        >
                          {/* Show file attachment if present */}
                          {message.fileAttachment && (
                            <div className="mb-2">
                              <FileAttachment
                                filename={message.fileAttachment.filename}
                                fileType={message.fileAttachment.fileType}
                                size={message.fileAttachment.size}
                              />
                            </div>
                          )}
                          {/* Show content only if it exists */}
                          {message.content && (() => {
                            const { intro, plans, outro } = splitMessageContent(message.content)
                            // If no plans, render entire content through MessageContent to handle Stripe URLs
                            if (plans.length === 0) {
                              return <MessageContent content={message.content} />
                            }
                            return (
                              <div>
                                {intro && (
                                  <div className="mb-4">
                                    <MessageContent content={intro} />
                                  </div>
                                )}
                                {plans.length > 0 && (
                                  <div className={`grid grid-cols-1 ${plans.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3'} gap-3 mb-4`}>
                                    {plans.map((plan, index) => (
                                      <Card key={index} className="border border-gray-200 hover:border-gray-300 transition-colors">
                                        <CardHeader className="pb-3">
                                          <CardTitle className="text-base flex items-start gap-2 min-h-[3rem]">
                                            <span className="text-2xl flex-shrink-0" style={{ fontFamily: '"Apple Color Emoji", "Segoe UI Emoji", "Noto Color Emoji", sans-serif' }}>
                                              {plan.emoji}
                                            </span>
                                            <span className="break-words font-semibold leading-tight text-sm">
                                              {plan.name.replace('(Recommended for adventure sports)', '').trim()}
                                              {plan.name.includes('Recommended') && (
                                                <span className="block text-xs text-gray-500 font-normal mt-0.5">
                                                  Recommended for adventure sports
                                                </span>
                                              )}
                                            </span>
                                          </CardTitle>
                                          <CardDescription className="text-xl font-bold text-black mt-2">
                                            {plan.price}
                                          </CardDescription>
                                        </CardHeader>
                                        <CardContent className="pt-0">
                                          <ul className="space-y-1.5">
                                            {plan.features.map((feature, idx) => (
                                              <li key={idx} className="text-xs text-gray-600 flex items-start">
                                                <span className="text-green-600 mr-1.5 flex-shrink-0">✓</span>
                                                <span className="break-words">{feature}</span>
                                              </li>
                                            ))}
                                          </ul>
                                        </CardContent>
                                      </Card>
                                    ))}
                                  </div>
                                )}
                                {outro && (
                                  <div>
                                    <MessageContent content={outro} />
                                  </div>
                                )}
                              </div>
                            )
                          })()}
                          <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-gray-300' : 'text-gray-500'}`}>
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                      {/* Show extracted data card for assistant messages with extracted data */}
                      {message.role === 'assistant' && (() => {
                        console.log('🔍 [DEBUG] Rendering check - message.extractedData:', message.extractedData)
                        return message.extractedData
                      })() && (
                        <div className="mt-2">
                          <ExtractedDataCard
                            extractedData={message.extractedData}
                            documentId={message.documentId}
                            onConfirm={async () => {
                              // Send confirmation message directly
                              const confirmMessage = "Yes, confirm"
                              setInputValue(confirmMessage)
                              // Wait a tick then send
                              await new Promise(resolve => setTimeout(resolve, 50))
                              // Call handleSendMessage - but we need inputValue set first
                              // Better: send message directly
                              const userMsg: Message = {
                                id: Date.now().toString(),
                                role: 'user',
                                content: confirmMessage,
                                timestamp: new Date()
                              }
                              setMessages(prev => [...prev, userMsg])
                              // Then trigger API call
                              const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
                              const token = await getAuthToken()
                              if (token && currentSessionId) {
                                try {
                                  const response = await fetch(`${API_URL}/chat/message`, {
                                    method: 'POST',
                                    headers: {
                                      'Authorization': `Bearer ${token}`,
                                      'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({
                                      session_id: currentSessionId,
                                      message: confirmMessage,
                                    }),
                                  })
                                  if (response.ok) {
                                    const data = await response.json()
                                    const assistantMsg: Message = {
                                      id: (Date.now() + 1).toString(),
                                      role: 'assistant',
                                      content: data.message,
                                      timestamp: new Date()
                                    }
                                    setMessages(prev => [...prev, assistantMsg])
                                    setConversationState(data.state || {})
                                  }
                                } catch (e) {
                                  console.error('Confirmation send error:', e)
                                }
                              }
                            }}
                            onEdit={() => {
                              // Edit button click handled by component itself (sets isEditing)
                            }}
                            onSave={(updatedData) => {
                              // Update the message's extractedData after save
                              setMessages(prev => prev.map(msg => 
                                msg.id === message.id 
                                  ? { ...msg, extractedData: updatedData }
                                  : msg
                              ))
                              // Optionally trigger re-processing by sending a message
                              // For now, just update the UI
                            }}
                            onReject={async () => {
                              // Send rejection message directly
                              const rejectMessage = "No, that's not correct"
                              setInputValue(rejectMessage)
                              await new Promise(resolve => setTimeout(resolve, 50))
                              const userMsg: Message = {
                                id: Date.now().toString(),
                                role: 'user',
                                content: rejectMessage,
                                timestamp: new Date()
                              }
                              setMessages(prev => [...prev, userMsg])
                              // Trigger API call
                              const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
                              const token = await getAuthToken()
                              if (token && currentSessionId) {
                                try {
                                  const response = await fetch(`${API_URL}/chat/message`, {
                                    method: 'POST',
                                    headers: {
                                      'Authorization': `Bearer ${token}`,
                                      'Content-Type': 'application/json',
                                    },
                                    body: JSON.stringify({
                                      session_id: currentSessionId,
                                      message: rejectMessage,
                                    }),
                                  })
                                  if (response.ok) {
                                    const data = await response.json()
                                    const assistantMsg: Message = {
                                      id: (Date.now() + 1).toString(),
                                      role: 'assistant',
                                      content: data.message,
                                      timestamp: new Date()
                                    }
                                    setMessages(prev => [...prev, assistantMsg])
                                    setConversationState(data.state || {})
                                  }
                                } catch (e) {
                                  console.error('Rejection send error:', e)
                                }
                              }
                            }}
                          />
                        </div>
                      )}
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-2xl rounded-tl-sm px-4 py-3">
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                  </>
                  )}
                </div>

                {/* Input Area */}
                <div className="border-t border-gray-200 p-4 bg-gray-50">
                  {/* File preview (shown before sending) */}
                  {selectedFile && (
                    <div className="mb-2">
                      <FileAttachment
                        filename={selectedFile.name}
                        fileType={selectedFile.type}
                        size={selectedFile.size}
                        onRemove={handleRemoveFile}
                        variant="input"
                      />
                    </div>
                  )}
                  <div className="flex items-end space-x-2">
                    <div className="flex-1 relative">
                      <textarea
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder={selectedFile ? "Ask anything..." : "Type your message..."}
                        className="w-full px-4 py-3 border border-gray-300 rounded-xl focus:outline-none focus:border-black focus:ring-1 focus:ring-black resize-none transition-colors text-black placeholder-gray-400"
                        rows={2}
                      />
                    </div>
                    {/* Hidden file input */}
                    <input
                      ref={fileInputRef}
                      type="file"
                      accept=".pdf,.png,.jpg,.jpeg"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    {/* PDF Upload Button */}
                    <button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isUploading || isLoading}
                      className="border-2 rounded-full h-10 w-10 p-0 flex items-center justify-center hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      style={{ borderColor: '#dd2930', color: '#dd2930' }}
                      title="Upload PDF or image"
                    >
                      {isUploading ? (
                        <div className="w-4 h-4 border-2 border-t-transparent rounded-full animate-spin" style={{ borderColor: '#dd2930', borderTopColor: 'transparent' }} />
                      ) : (
                        <FileText className="w-4 h-4" stroke="#dd2930" strokeWidth={2} style={{ color: '#dd2930' }} />
                      )}
                    </button>
                    <VoiceButton
                      sessionId={currentSessionId || ''}
                      onTranscript={handleVoiceInput}
                      onRequestResponse={handleGetLastResponse}
                      isActive={isVoiceActive}
                      onActiveChange={setIsVoiceActive}
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={(!inputValue.trim() && !selectedFile) || isLoading || isUploading}
                      size="sm"
                      className="text-white rounded-full h-10 w-10 p-0 hover:opacity-90"
                      style={{ backgroundColor: '#dd2930' }}
                    >
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Copilot Panel */}
          <div className="lg:col-span-1">
            <div className="border border-gray-200 rounded-2xl h-[calc(100vh-12rem)] flex flex-col bg-white shadow-sm overflow-hidden">
              <div 
                className="flex-1 overflow-y-auto p-4 [&::-webkit-scrollbar]:hidden [-ms-overflow-style:none] [scrollbar-width:none]"
              >
                <CopilotPanel 
                  conversationState={conversationState} 
                  sessionId={currentSessionId || ''}
                  onPaymentStarted={() => {
                    console.log('💳 Payment initiated, starting polling...')
                    setAwaitingPayment(true)
                  }}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  )
}
