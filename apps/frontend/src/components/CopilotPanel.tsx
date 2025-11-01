'use client'

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp, Plane, Users, DollarSign, Phone } from 'lucide-react'

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

interface CopilotPanelProps {
  conversationState: ConversationState
}

export function CopilotPanel({ conversationState }: CopilotPanelProps) {
  const [expandedSections, setExpandedSections] = useState<string[]>(['trip'])

  const toggleSection = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    )
  }

  // Extract data from conversation state
  const { trip_details, travelers_data, preferences, quote_data } = conversationState

  // Debug logging
  console.log('🎨 CopilotPanel received conversationState:', conversationState)
  console.log('👥 travelers_data:', travelers_data)
  console.log('💰 quote_data:', quote_data)

  // Auto-expand sections when they receive data
  useEffect(() => {
    const sectionsToExpand: string[] = ['trip'] // Always show trip

    if (travelers_data?.ages && travelers_data.ages.length > 0) {
      sectionsToExpand.push('travelers')
    }

    if (quote_data?.quotes) {
      sectionsToExpand.push('plan', 'pricing')
    }

    setExpandedSections(sectionsToExpand)
  }, [travelers_data, quote_data])

  // Build trip data from conversation state
  const hasDestination = trip_details?.destination
  const hasDates = trip_details?.departure_date && trip_details?.return_date
  const hasActivities = preferences?.adventure_sports !== undefined

  // Format destinations (can be comma-separated in the backend)
  const destinations = trip_details?.destination
    ? trip_details.destination.split(',').map(d => d.trim())
    : []

  // Build travelers list from ages
  const travelers = travelers_data?.ages?.map((age, index) => ({
    name: `Traveler ${index + 1}`,
    age,
    isPrimary: index === 0
  })) || []

  // Build activities list
  const activities = []
  if (preferences?.adventure_sports) {
    activities.push('Adventure sports')
  }

  // Extract quote information
  const hasQuote = quote_data?.quotes !== undefined

  // Calculate price range from available quotes
  let priceRange = { min: 0, max: 0 }
  if (quote_data?.quotes) {
    const prices = [
      quote_data.quotes.standard?.price,
      quote_data.quotes.elite?.price,
      quote_data.quotes.premier?.price
    ].filter((p): p is number => p !== undefined)

    if (prices.length > 0) {
      priceRange = { min: Math.min(...prices), max: Math.max(...prices) }
    }
  }

  return (
    <div className="space-y-4">
      {/* Trip Summary */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Plane className="w-5 h-5 mr-2" style={{ color: '#dd2930' }} />
              <h3 className="font-semibold text-black">Trip summary</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleSection('trip')}
              className="hover:bg-gray-100"
            >
              {expandedSections.includes('trip') ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
        {expandedSections.includes('trip') && (
          <div className="px-5 py-4">
            {!hasDates && !hasDestination && !hasActivities ? (
              <p className="text-sm text-gray-400 italic">Trip details will appear here as you chat...</p>
            ) : (
              <div className="space-y-4">
                {hasDates && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Dates</p>
                    <p className="text-sm text-black">
                      {trip_details?.departure_date} to {trip_details?.return_date}
                    </p>
                  </div>
                )}
                {hasDestination && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Destinations</p>
                    <div className="flex flex-wrap gap-2">
                      {destinations.map((dest, index) => (
                        <span key={index} className="px-3 py-1 bg-gray-100 text-black text-xs font-medium rounded-full">
                          {dest}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {hasActivities && (
                  <div>
                    <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Activities</p>
                    <div className="flex flex-wrap gap-2">
                      {activities.map((activity, index) => (
                        <span key={index} className="px-3 py-1 border border-gray-300 text-black text-xs rounded-full">
                          {activity}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Travelers */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Users className="w-5 h-5 mr-2" style={{ color: '#dd2930' }} />
              <h3 className="font-semibold text-black">Travelers</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleSection('travelers')}
              className="hover:bg-gray-100"
            >
              {expandedSections.includes('travelers') ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
        {expandedSections.includes('travelers') && (
          <div className="px-5 py-4">
            {travelers.length === 0 ? (
              <p className="text-sm text-gray-400 italic">Traveler information will appear here as you chat...</p>
            ) : (
              <div className="space-y-3">
                {travelers.map((traveler, index) => (
                  <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-xl">
                    <div>
                      <p className="text-sm font-medium text-black">{traveler.name}</p>
                      <p className="text-xs text-gray-500">Age: {traveler.age}</p>
                    </div>
                    {traveler.isPrimary && (
                      <span className="px-2 py-1 bg-black text-white text-xs font-medium rounded-full">
                        Primary
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Selected Plan */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <DollarSign className="w-5 h-5 mr-2" style={{ color: '#dd2930' }} />
              <h3 className="font-semibold text-black">Selected plan</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleSection('plan')}
              className="hover:bg-gray-100"
            >
              {expandedSections.includes('plan') ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
        {expandedSections.includes('plan') && (
          <div className="px-5 py-4">
            {!hasQuote ? (
              <p className="text-sm text-gray-400 italic">Available plans will appear here after quotes are generated...</p>
            ) : (
              <div className="space-y-3">
                <p className="text-sm text-gray-600">Available plans:</p>
                {quote_data?.quotes?.standard && (
                  <div className="p-3 border border-gray-200 rounded-xl hover:border-black transition-colors cursor-pointer">
                    <p className="text-sm font-semibold text-black">Standard</p>
                    <p className="text-xs text-gray-500 mt-1">SGD {quote_data.quotes.standard.price.toFixed(2)}</p>
                  </div>
                )}
                {quote_data?.quotes?.elite && (
                  <div className="p-3 border border-gray-200 rounded-xl hover:border-black transition-colors cursor-pointer">
                    <p className="text-sm font-semibold text-black">Elite</p>
                    <p className="text-xs text-gray-500 mt-1">SGD {quote_data.quotes.elite.price.toFixed(2)}</p>
                  </div>
                )}
                {quote_data?.quotes?.premier && (
                  <div className="p-3 border border-gray-200 rounded-xl hover:border-black transition-colors cursor-pointer">
                    <p className="text-sm font-semibold text-black">Premier</p>
                    <p className="text-xs text-gray-500 mt-1">SGD {quote_data.quotes.premier.price.toFixed(2)}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Price Range/Firm */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <DollarSign className="w-5 h-5 mr-2" style={{ color: '#dd2930' }} />
              <h3 className="font-semibold text-black">Pricing</h3>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => toggleSection('pricing')}
              className="hover:bg-gray-100"
            >
              {expandedSections.includes('pricing') ? (
                <ChevronUp className="w-4 h-4" />
              ) : (
                <ChevronDown className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
        {expandedSections.includes('pricing') && (
          <div className="px-5 py-4">
            {!hasQuote ? (
              <p className="text-sm text-gray-400 italic">Pricing will appear here after quotes are generated...</p>
            ) : (
              <div className="space-y-4">
                <div className="text-center py-4">
                  <p className="text-2xl font-bold text-black">
                    SGD {priceRange.min.toFixed(2)} - SGD {priceRange.max.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">Price range</p>
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm p-5">
        <div className="space-y-3">
          {!hasQuote ? (
            <Button className="w-full text-white font-medium rounded-full hover:opacity-90" style={{ backgroundColor: '#dd2930' }} disabled>
              Continue chatting to get quote
            </Button>
          ) : (
            <Button className="w-full text-white font-medium rounded-full hover:opacity-90" style={{ backgroundColor: '#dd2930' }}>
              Proceed to payment
            </Button>
          )}

          <Button variant="ghost" className="w-full text-gray-700 hover:text-black hover:bg-gray-100 rounded-full">
            <Phone className="w-4 h-4 mr-2" />
            Talk to a human
          </Button>
        </div>
      </div>
    </div>
  )
}
