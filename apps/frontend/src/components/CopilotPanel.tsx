'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { ChevronDown, ChevronUp, Plane, Users, DollarSign, Phone } from 'lucide-react'

export function CopilotPanel() {
  const [expandedSections, setExpandedSections] = useState<string[]>(['trip'])

  const toggleSection = (section: string) => {
    setExpandedSections(prev =>
      prev.includes(section)
        ? prev.filter(s => s !== section)
        : [...prev, section]
    )
  }

  const tripData = {
    startDate: '2024-03-15',
    endDate: '2024-03-22',
    destinations: ['France', 'Italy'],
    travelers: [
      { name: 'John Doe', age: 35, isPrimary: true },
      { name: 'Jane Doe', age: 32, isPrimary: false }
    ],
    activities: ['Sightseeing', 'Museum visits', 'Restaurant dining']
  }

  const priceData = {
    range: { min: 45.00, max: 65.00 },
    firm: null,
    currency: 'USD',
    breakdown: {
      baseRate: 25.00,
      tripDuration: 7,
      ageLoading: 0.0,
      activityLoading: 0.0,
      destinationLoading: 0.1
    }
  }

  return (
    <div className="space-y-4">
      {/* Trip Summary */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Plane className="w-5 h-5 mr-2 text-black" />
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
            <div className="space-y-4">
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">Dates</p>
                <p className="text-sm text-black">
                  {tripData.startDate} to {tripData.endDate}
                </p>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Destinations</p>
                <div className="flex flex-wrap gap-2">
                  {tripData.destinations.map((dest, index) => (
                    <span key={index} className="px-3 py-1 bg-gray-100 text-black text-xs font-medium rounded-full">
                      {dest}
                    </span>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Activities</p>
                <div className="flex flex-wrap gap-2">
                  {tripData.activities.map((activity, index) => (
                    <span key={index} className="px-3 py-1 border border-gray-300 text-black text-xs rounded-full">
                      {activity}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Travelers */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Users className="w-5 h-5 mr-2 text-black" />
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
            <div className="space-y-3">
              {tripData.travelers.map((traveler, index) => (
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
          </div>
        )}
      </div>

      {/* Selected Plan */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <DollarSign className="w-5 h-5 mr-2 text-black" />
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
            <div className="space-y-4">
              <div className="p-4 bg-black rounded-xl">
                <p className="text-sm font-semibold text-white">Comprehensive Travel</p>
                <p className="text-xs text-gray-300 mt-1">Full coverage protection</p>
              </div>
              <div className="text-sm">
                <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Coverage limits</p>
                <ul className="space-y-2 text-black">
                  <li className="flex items-center"><span className="w-1.5 h-1.5 bg-black rounded-full mr-2"></span> Medical: $100,000</li>
                  <li className="flex items-center"><span className="w-1.5 h-1.5 bg-black rounded-full mr-2"></span> Trip Cancellation: $5,000</li>
                  <li className="flex items-center"><span className="w-1.5 h-1.5 bg-black rounded-full mr-2"></span> Baggage: $2,500</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Price Range/Firm */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm">
        <div className="px-5 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <DollarSign className="w-5 h-5 mr-2 text-black" />
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
            <div className="space-y-4">
              {priceData.firm ? (
                <div className="text-center py-4">
                  <p className="text-3xl font-bold text-black">
                    ${priceData.firm.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">Firm price</p>
                </div>
              ) : (
                <div className="text-center py-4">
                  <p className="text-2xl font-bold text-black">
                    ${priceData.range.min.toFixed(2)} - ${priceData.range.max.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-500 mt-1">Price range</p>
                </div>
              )}
              
              <div className="pt-3 border-t border-gray-200">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => toggleSection('breakdown')}
                  className="w-full text-gray-700 hover:text-black hover:bg-gray-100"
                >
                  Why this price?
                </Button>
                {expandedSections.includes('breakdown') && (
                  <div className="mt-3 text-xs text-gray-600 space-y-2 p-3 bg-gray-50 rounded-lg">
                    <p>Base rate: ${priceData.breakdown.baseRate.toFixed(2)}</p>
                    <p>Trip duration: {priceData.breakdown.tripDuration} days</p>
                    <p>Age loading: {priceData.breakdown.ageLoading.toFixed(1)}%</p>
                    <p>Activity loading: {priceData.breakdown.activityLoading.toFixed(1)}%</p>
                    <p>Destination loading: {priceData.breakdown.destinationLoading.toFixed(1)}%</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div className="border border-gray-200 rounded-2xl bg-white shadow-sm p-5">
        <div className="space-y-3">
          {!priceData.firm ? (
            <Button className="w-full bg-black hover:bg-gray-800 text-white font-medium rounded-full" disabled>
              Get firm price
            </Button>
          ) : (
            <Button className="w-full bg-black hover:bg-gray-800 text-white font-medium rounded-full">
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
