'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'
import { LogOut, Plus, MapPin, Calendar, Users, Plane } from 'lucide-react'

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
  const [activeTab, setActiveTab] = useState<'upcoming' | 'past'>('upcoming')
  const [error, setError] = useState('')
  const [destinationImages, setDestinationImages] = useState<Record<string, string>>({})
  const destinationImagesRef = useRef<Record<string, string>>({})

  useEffect(() => {
    fetchTrips()
  }, [activeTab])

  const sanitizeDestinationName = (destination: string): string => {
    return destination
      .toLowerCase()
      .replace(/[^a-z0-9\s,]/g, '')
      .replace(/\s+/g, '_')
      .replace(/,/g, '_')
  }

  const getPublicImageUrl = (destination: string): string | null => {
    const sanitized = sanitizeDestinationName(destination)
    // Check if image exists in public directory
    return `/destination-images/${sanitized}.png`
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
        const publicUrl = getPublicImageUrl(destination)
        if (publicUrl) {
          const exists = await checkImageExists(publicUrl)
          if (exists) {
            return { destination, imageUrl: publicUrl }
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
      <div className="min-h-screen bg-white">
        {/* Header */}
        <header className="border-b border-gray-200 bg-white sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-semibold text-black">ConvoTravelInsure</h1>
                {user && (
                  <p className="text-sm text-gray-600 mt-1">Welcome back, {user.name}</p>
                )}
              </div>
              <div className="flex items-center gap-3">
                <Button
                  onClick={handleNewTrip}
                  className="bg-black hover:bg-gray-800 text-white font-medium rounded-full px-6"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  New Trip
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={logout}
                  className="text-gray-700 hover:text-black"
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
          {/* Tabs */}
          <div className="flex gap-6 border-b border-gray-200 mb-8">
            <button
              onClick={() => setActiveTab('upcoming')}
              className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                activeTab === 'upcoming'
                  ? 'text-black'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Upcoming & Ongoing
              {activeTab === 'upcoming' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-black" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('past')}
              className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                activeTab === 'past'
                  ? 'text-black'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Past Trips
              {activeTab === 'past' && (
                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-black" />
              )}
            </button>
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6 text-sm">
              {error}
            </div>
          )}

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
                  className="bg-black hover:bg-gray-800 text-white font-medium rounded-full px-6"
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
                  className="group cursor-pointer hover:shadow-lg transition-shadow duration-200 overflow-hidden border border-gray-200 rounded-xl"
                >
                  {/* Trip Image */}
                  <div className="aspect-[4/3] bg-gradient-to-br from-blue-400 via-blue-500 to-indigo-600 relative overflow-hidden">
                    {trip.destinations.length > 0 && getDestinationImageUrl(trip.destinations[0]) ? (
                      <img
                        src={getDestinationImageUrl(trip.destinations[0])!}
                        alt={trip.destinations[0]}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          // Fallback to gradient if image fails to load
                          const target = e.target as HTMLImageElement
                          target.style.display = 'none'
                        }}
                      />
                    ) : null}
                    
                    <div className="absolute inset-0 bg-black/10 group-hover:bg-black/5 transition-colors" />
                    <div className="absolute top-3 right-3">
                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(trip.status)}`}>
                        {trip.status.charAt(0).toUpperCase() + trip.status.slice(1)}
                      </span>
                    </div>
                    {trip.destinations.length > 0 && (
                      <div className="absolute bottom-3 left-3 text-white">
                        <h3 className="text-xl font-semibold drop-shadow">
                          {trip.destinations[0]}
                        </h3>
                      </div>
                    )}
                  </div>

                  {/* Trip Details */}
                  <div className="p-4">
                    <div className="space-y-2">
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
        </main>
      </div>
    </ProtectedRoute>
  )
}
