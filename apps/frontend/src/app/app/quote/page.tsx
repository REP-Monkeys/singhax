'use client'

import { useState, useRef, useEffect } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Mic, MicOff, Send, User, Bot, Phone, LogOut, ArrowLeft, FileText, Upload } from 'lucide-react'
import { CopilotPanel } from '@/components/CopilotPanel'
import { VoiceButton } from '@/components/VoiceButton'
import { ExtractedDataCard } from '@/components/ExtractedDataCard'
import { FileAttachment } from '@/components/FileAttachment'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'

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

export default function QuotePage() {
  const { user, logout } = useAuth()
  const searchParams = useSearchParams()
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
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

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
        const transformedMessages = data.messages.map((msg: any, idx: number) => ({
          id: `${idx}`,
          role: msg.role,
          content: msg.content,
          timestamp: new Date()
        }))
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

  // Load chat history when session_id is provided
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

  const handleFileUpload = async (file: File) => {
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
      }

      // Create form data
      const formData = new FormData()
      formData.append('file', file)
      formData.append('session_id', sessionId)

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

      // Add user message with file attachment (like ChatGPT)
      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: '',  // Empty content - we'll show the file attachment instead
        timestamp: new Date(),
        fileAttachment: {
          filename: file.name,
          fileType: file.type,
          size: file.size
        }
      }

      setMessages(prev => [...prev, userMessage])

      // Add assistant response with extracted data
      if (uploadData.message) {
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: uploadData.message,
          timestamp: new Date(),
          extractedData: uploadData.ocr_result?.extracted_json || null
        }
        setMessages(prev => [...prev, assistantMessage])
      }

      // Reload chat history to get updated state
      if (sessionId) {
        await loadChatHistory(sessionId)
      }

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
    // If there's a selected file, upload it (file can be sent without text)
    if (selectedFile) {
      await handleFileUpload(selectedFile)
      // If there's also text, send it as a separate message
      if (inputValue.trim()) {
        // Wait a bit for upload to complete, then send text message
        setTimeout(() => {
          const textToSend = inputValue
          setInputValue('')
          handleSendTextMessage(textToSend)
        }, 500)
      }
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

  const handleVoiceInput = (transcript: string) => {
    setInputValue(transcript)
  }

  return (
    <ProtectedRoute requireOnboarding={true}>
      <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-50 backdrop-blur-sm bg-white/95">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <Link href="/app/dashboard">
                <Button variant="ghost" size="sm" className="text-gray-700 hover:text-black hover:bg-gray-100">
                  <ArrowLeft className="w-4 h-4 mr-1.5" />
                  Dashboard
                </Button>
              </Link>
              <h1 className="text-xl font-semibold text-black tracking-tight">ConvoTravelInsure</h1>
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
                Sign out
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-2">
            <div className="border border-gray-200 rounded-2xl h-[600px] flex flex-col bg-white shadow-sm">
              <div className="border-b border-gray-200 px-6 py-4">
                <div className="flex items-center">
                  <div className="flex items-center justify-center h-10 w-10 rounded-full bg-black mr-3">
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
                              ? 'bg-black text-white rounded-2xl rounded-tr-sm'
                              : 'bg-gray-100 text-black rounded-2xl rounded-tl-sm'
                          } px-4 py-3`}
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
                          {message.content && (
                            <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                          )}
                          <p className={`text-xs mt-2 ${message.role === 'user' ? 'text-gray-300' : 'text-gray-500'}`}>
                            {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </p>
                        </div>
                      </div>
                      {/* Show extracted data card for assistant messages with extracted data */}
                      {message.role === 'assistant' && message.extractedData && (
                        <div className="mt-2">
                          <ExtractedDataCard
                            extractedData={message.extractedData}
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
                              // User can edit by typing
                              setInputValue("I need to edit: ")
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
                    <Button
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isUploading || isLoading}
                      size="sm"
                      variant="outline"
                      className="border-gray-300 hover:bg-gray-100 text-gray-700 rounded-full h-10 w-10 p-0"
                      title="Upload PDF or image"
                    >
                      {isUploading ? (
                        <div className="w-4 h-4 border-2 border-gray-400 border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <FileText className="w-4 h-4" />
                      )}
                    </Button>
                    <VoiceButton
                      onTranscript={handleVoiceInput}
                      isActive={isVoiceActive}
                      onActiveChange={setIsVoiceActive}
                    />
                    <Button
                      onClick={handleSendMessage}
                      disabled={(!inputValue.trim() && !selectedFile) || isLoading || isUploading}
                      size="sm"
                      className="bg-black hover:bg-gray-800 text-white rounded-full h-10 w-10 p-0"
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
            <CopilotPanel conversationState={conversationState} />
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  )
}
