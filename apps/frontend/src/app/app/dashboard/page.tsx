'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'
import { LogOut, Plus, MapPin, Calendar, Users, Plane, Loader2, Phone } from 'lucide-react'
import { DocumentList } from '@/components/DocumentList'

interface Trip {
  id: string
  session_id?: string
  status: 'draft' | 'ongoing' | 'completed' | 'past'
  start_date?: string
  end_date?: string
  destinations: string[]
  travelers_count: number
  total_cost?: string
  created_at: string
  updated_at: string
}

export default function DashboardPage() {
  const router = useRouter()
  const { user, logout } = useAuth()
  const [trips, setTrips] = useState<Trip[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'upcoming' | 'past' | 'documents'>('upcoming')
  const [error, setError] = useState('')
  const [authToken, setAuthToken] = useState<string | null>(null)
  const [destinationImages, setDestinationImages] = useState<Record<string, string>>({})
  const destinationImagesRef = useRef<Record<string, string>>({})

  useEffect(() => {
    // Get auth token
    const getAuthToken = async () => {
      const { data: { session } } = await supabase.auth.getSession()
      if (session) {
        setAuthToken(session.access_token)
      }
    }
    getAuthToken()
  }, [])

  useEffect(() => {
    // Only fetch trips when not on documents tab
    if (activeTab !== 'documents') {
      fetchTrips()
    }
  }, [activeTab])

  useEffect(() => {
    // Auto-refresh trips when window gains focus (user returns from payment)
    const handleFocus = () => {
      console.log('👁️ Window gained focus - refreshing trips...')
      if (activeTab !== 'documents') {
        fetchTrips()
      }
    }

    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [activeTab])

  const sanitizeDestinationName = (destination: string): string => {
    return destination
      .toLowerCase()
      .replace(/[^a-z0-9\s,]/g, '')
      .replace(/\s+/g, '_')
      .replace(/,/g, '_')
  }

  const getPublicImageUrl = (destination: string): string[] => {
    const sanitized = sanitizeDestinationName(destination)
    // Check both .jpg and .png formats
    return [
      `/destination-images/${sanitized}.jpg`,
      `/destination-images/${sanitized}.png`
    ]
  }

  const checkImageExists = async (url: string): Promise<boolean> => {
    try {
      const response = await fetch(url, { method: 'HEAD' })
      return response.ok
    } catch {
      return false
    }
  }

  const fetchDestinationImages = useCallback(async () => {
    const uniqueDestinations = new Set<string>()
    
    // Collect all unique destinations
    trips.forEach(trip => {
      trip.destinations.forEach(dest => {
        if (dest) uniqueDestinations.add(dest)
      })
    })

    // Filter out destinations that already have images
    const destinationsToFetch = Array.from(uniqueDestinations).filter(dest => {
      return !destinationImagesRef.current[dest]
    })

    if (destinationsToFetch.length === 0) {
      return // All images already loaded
    }

    // Only check public directory for pre-generated images (no API calls)
    const publicImageChecks = await Promise.all(
      destinationsToFetch.map(async (destination) => {
        const publicUrls = getPublicImageUrl(destination)
        // Try both .jpg and .png formats
        for (const url of publicUrls) {
          const exists = await checkImageExists(url)
          if (exists) {
            return { destination, imageUrl: url }
          }
        }
        return null
      })
    )

    // Filter out null results
    const foundImages = publicImageChecks.filter(r => r !== null) as Array<{ destination: string; imageUrl: string }>

    const imagesMap: Record<string, string> = {}
    foundImages.forEach(result => {
      if (result) {
        imagesMap[result.destination] = result.imageUrl
      }
    })
    setDestinationImages(prev => {
      const updated = { ...prev, ...imagesMap }
      destinationImagesRef.current = updated
      return updated
    })
  }, [trips])

  useEffect(() => {
    // Fetch images for all unique destinations
    if (trips.length > 0) {
      fetchDestinationImages()
    }
  }, [trips, fetchDestinationImages])

  // Update ref when images change
  useEffect(() => {
    destinationImagesRef.current = destinationImages
  }, [destinationImages])

  // Cleanup blob URLs when component unmounts or images change
  useEffect(() => {
    return () => {
      Object.values(destinationImages).forEach(url => {
        if (url.startsWith('blob:')) {
          URL.revokeObjectURL(url)
        }
      })
    }
  }, [destinationImages])

  const getDestinationImageUrl = (destination: string): string | null => {
    return destinationImages[destination] || null
  }

  const fetchTrips = async () => {
    setLoading(true)
    setError('')
    try {
      // Get session from Supabase
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()

      if (sessionError || !session) {
        throw new Error('No authentication session found')
      }

      // Fetch trips based on active tab
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      let url = `${backendUrl}/trips`
      if (activeTab === 'upcoming') {
        // Show draft, ongoing, and completed trips
        url += '?status=draft,ongoing,completed'
      } else {
        // Show past trips
        url += '?status=past'
      }

      console.log('🔍 Fetching trips from:', url)

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
        },
      })

      console.log('📡 Response status:', response.status)

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ Fetch failed:', errorText)
        throw new Error(`Failed to fetch trips: ${response.status} ${errorText}`)
      }

      const data = await response.json()
      console.log('✅ Fetched trips:', data)
      setTrips(data)
    } catch (err: any) {
      console.error('❌ Error fetching trips:', err)
      setError(err.message || 'Failed to load trips')
    } finally {
      setLoading(false)
    }
  }

  const handleTripClick = (trip: Trip) => {
    if (trip.session_id) {
      router.push(`/app/quote?session=${trip.session_id}`)
    } else {
      router.push(`/app/quote`)
    }
  }

  const handleNewTrip = () => {
    router.push('/app/quote')
  }

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'TBD'
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      draft: 'bg-gray-100 text-gray-800',
      ongoing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      past: 'bg-gray-100 text-gray-600'
    }
    return styles[status as keyof typeof styles] || styles.draft
  }

  // Filter trips by current and upcoming vs past
  const upcomingTrips = trips.filter(t => ['draft', 'ongoing', 'completed'].includes(t.status))
  const pastTrips = trips.filter(t => t.status === 'past')
  const displayTrips = activeTab === 'upcoming' ? upcomingTrips : pastTrips

  return (
    <ProtectedRoute requireOnboarding={true}>
      <div className="min-h-screen overflow-y-auto" style={{ backgroundImage: 'linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%)' }}>
        {/* Header */}
        <header className="border-b border-gray-200 bg-white sticky top-0 z-10 shadow-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Plane className="w-8 h-8" style={{ color: '#dd2930' }} />
                <h1 className="text-3xl font-semibold" style={{ color: '#dd2930' }}>TripMate</h1>
              </div>
              <div className="flex items-center gap-3">
                <Button
                  onClick={handleNewTrip}
                  className="text-white font-medium rounded-full px-6 hover:opacity-90"
                  style={{ backgroundColor: '#dd2930' }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Trip
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-gray-700 hover:text-black hover:bg-gray-100"
                >
                  <Phone className="w-4 h-4 mr-1.5" />
                  Human support
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-gray-700 hover:text-black hover:bg-gray-100"
                >
                  My policies
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="text-gray-700 hover:text-black hover:bg-gray-100"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {user && (
            <p className="text-2xl font-bold mb-6 text-black">Welcome back, {user.name}</p>
          )}
          {/* Tabs */}
          <div className="flex gap-6 border-b border-gray-200 mb-8 h-[48px]">
            <button
              onClick={() => setActiveTab('upcoming')}
              className={`pb-3 px-1 font-medium text-base transition-colors relative h-full flex items-end hover:opacity-80`}
              style={{ color: '#dd2930' }}
            >
              <span className="relative">
                Upcoming & Ongoing
                {activeTab === 'upcoming' && (
                  <div className="absolute bottom-[-12px] left-0 right-0 h-0.5" style={{ backgroundColor: '#dd2930' }} />
                )}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('past')}
              className={`pb-3 px-1 font-medium text-base transition-colors relative h-full flex items-end hover:opacity-80`}
              style={{ color: '#dd2930' }}
            >
              <span className="relative">
                Past Trips
                {activeTab === 'past' && (
                  <div className="absolute bottom-[-12px] left-0 right-0 h-0.5" style={{ backgroundColor: '#dd2930' }} />
                )}
              </span>
            </button>
            <button
              onClick={() => setActiveTab('documents')}
              className={`pb-3 px-1 font-medium text-base transition-colors relative h-full flex items-end hover:opacity-80`}
              style={{ color: '#dd2930' }}
            >
              <span className="relative">
                Documents
                {activeTab === 'documents' && (
                  <div className="absolute bottom-[-12px] left-0 right-0 h-0.5" style={{ backgroundColor: '#dd2930' }} />
                )}
              </span>
            </button>
          </div>

          {/* Error Message */}
          {error && activeTab !== 'documents' && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6 text-sm">
              {error}
            </div>
          )}

          {/* Documents Tab Content */}
          {activeTab === 'documents' ? (
            authToken ? (
              <DocumentList authToken={authToken} />
            ) : (
              <div className="flex items-center justify-center py-16">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
              </div>
            )
          ) : (
            <>
              {/* Loading State */}
              {loading ? (
                <div className="flex items-center justify-center py-16">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-black"></div>
                </div>
              ) : displayTrips.length === 0 ? (
            /* Empty State */
            <div className="text-center py-16">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                <Plane className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-xl font-semibold text-black mb-2">
                {activeTab === 'upcoming' ? 'No upcoming trips yet' : 'No past trips'}
              </h3>
              <p className="text-gray-600 mb-6 max-w-md mx-auto">
                {activeTab === 'upcoming'
                  ? 'Start planning your next adventure by creating a new trip and getting a quote for travel insurance.'
                  : 'Your completed trips will appear here.'}
              </p>
              {activeTab === 'upcoming' && (
                <Button
                  onClick={handleNewTrip}
                  className="text-white font-medium rounded-full px-6 hover:opacity-90"
                  style={{ backgroundColor: '#dd2930' }}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Start Your First Trip
                </Button>
              )}
            </div>
          ) : (
            /* Trip Cards Grid */
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {displayTrips.map((trip) => (
                <Card
                  key={trip.id}
                  onClick={() => handleTripClick(trip)}
                  className="group cursor-pointer hover:shadow-lg transition-shadow duration-200 overflow-hidden border border-gray-200 rounded-xl bg-white"
                >
                  {/* Trip Image */}
                  <div className="aspect-[4/3] relative overflow-hidden" style={{ backgroundImage: 'linear-gradient(to top, #ff0844 0%, #ffb199 100%)' }}>
                    {trip.destinations.length >= 2 && getDestinationImageUrl(trip.destinations[0]) && getDestinationImageUrl(trip.destinations[1]) ? (
                      // Multi-destination: Show diagonal split with 2 images
                      <>
                        {/* First destination - top-left triangle */}
                        <div className="absolute inset-0" style={{ clipPath: 'polygon(0 0, 100% 0, 0 100%)' }}>
                          <img
                            src={getDestinationImageUrl(trip.destinations[0])!}
                            alt={trip.destinations[0]}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              const target = e.target as HTMLImageElement
                              target.style.display = 'none'
                            }}
                          />
                        </div>
                        {/* Second destination - bottom-right triangle */}
                        <div className="absolute inset-0" style={{ clipPath: 'polygon(100% 0, 100% 100%, 0 100%)' }}>
                          <img
                            src={getDestinationImageUrl(trip.destinations[1])!}
                            alt={trip.destinations[1]}
                            className="w-full h-full object-cover"
                            onError={(e) => {
                              const target = e.target as HTMLImageElement
                              target.style.display = 'none'
                            }}
                          />
                        </div>
                        {/* Diagonal line separator */}
                        <div 
                          className="absolute inset-0 pointer-events-none"
                          style={{
                            background: 'linear-gradient(to bottom right, transparent calc(50% - 1px), white calc(50% - 1px), white calc(50% + 1px), transparent calc(50% + 1px))'
                          }}
                        />
                      </>
                    ) : trip.destinations.length > 0 && getDestinationImageUrl(trip.destinations[0]) ? (
                      // Single destination: Show one image
                      <img
                        src={getDestinationImageUrl(trip.destinations[0])!}
                        alt={trip.destinations[0]}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          const target = e.target as HTMLImageElement
                          target.style.display = 'none'
                        }}
                      />
                    ) : null}
                    
                    <div className="absolute top-3 right-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(trip.status)}`}>
                        {trip.status.charAt(0).toUpperCase() + trip.status.slice(1)}
                      </span>
                    </div>
                  </div>

                  {/* Trip Details */}
                  <div className="p-4 bg-white">
                    <div className="space-y-2">
                      {/* Destination Name */}
                      {trip.destinations.length > 0 && (
                        <h3 className="text-xl font-semibold text-black mb-2">
                          {trip.destinations.length === 1 
                            ? trip.destinations[0]
                            : trip.destinations.length === 2
                            ? `${trip.destinations[0]} & ${trip.destinations[1]}`
                            : `${trip.destinations[0]} & ${trip.destinations[1]} +${trip.destinations.length - 2} more`
                          }
                        </h3>
                      )}
                      {/* Dates */}
                      {(trip.start_date || trip.end_date) && (
                        <div className="flex items-center text-sm text-gray-600">
                          <Calendar className="w-4 h-4 mr-2 flex-shrink-0" />
                          <span>
                            {formatDate(trip.start_date)} - {formatDate(trip.end_date)}
                          </span>
                        </div>
                      )}

                      {/* Destinations */}
                      {trip.destinations.length > 0 && (
                        <div className="flex items-center text-sm text-gray-600">
                          <MapPin className="w-4 h-4 mr-2 flex-shrink-0" />
                          <span className="truncate">
                            {trip.destinations.length === 1
                              ? trip.destinations[0]
                              : `${trip.destinations[0]} +${trip.destinations.length - 1} more`}
                          </span>
                        </div>
                      )}

                      {/* Travelers */}
                      <div className="flex items-center text-sm text-gray-600">
                        <Users className="w-4 h-4 mr-2 flex-shrink-0" />
                        <span>
                          {trip.travelers_count} {trip.travelers_count === 1 ? 'traveler' : 'travelers'}
                        </span>
                      </div>

                      {/* Cost */}
                      {trip.total_cost && (
                        <div className="pt-2 mt-2 border-t border-gray-100">
                          <p className="text-sm font-semibold text-black">{trip.total_cost}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
            </>
          )}
        </main>
      </div>
    </ProtectedRoute>
  )
}
