import React from 'react'
import { Check, X } from 'lucide-react'

interface PlanDetails {
  name: string
  emoji: string
  price: number
  coverage: {
    medical_coverage?: number
    trip_cancellation?: number
    baggage_loss?: number
    personal_accident?: number
    adventure_sports?: boolean
    emergency_evacuation?: number
  }
  recommended?: boolean
}

interface PlanComparisonCardProps {
  plans: PlanDetails[]
}

// Define all possible coverage items
const ALL_COVERAGE_ITEMS = [
  { key: 'medical_coverage', label: 'Medical coverage', format: (val: number) => `$${val.toLocaleString()}` },
  { key: 'trip_cancellation', label: 'Trip cancellation', format: (val: number) => `$${val.toLocaleString()}` },
  { key: 'baggage_loss', label: 'Baggage protection', format: (val: number) => `$${val.toLocaleString()}` },
  { key: 'personal_accident', label: 'Personal accident', format: (val: number) => `$${val.toLocaleString()}` },
  { key: 'adventure_sports', label: 'Adventure sports', format: (val: any) => 'Included' },
  { key: 'emergency_evacuation', label: 'Emergency evacuation', format: (val: number) => `$${val.toLocaleString()}` },
]

export function PlanComparisonCard({ plans }: PlanComparisonCardProps) {
  if (plans.length === 0) return null

  return (
    <div className="my-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {plans.map((plan, idx) => {
          const isRecommended = plan.recommended
          
          return (
            <div
              key={idx}
              className={`relative border-2 rounded-xl p-4 bg-white transition-all ${
                isRecommended
                  ? 'border-[#dd2930] shadow-lg'
                  : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              {isRecommended && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-[#dd2930] text-white text-xs font-semibold px-3 py-1 rounded-full">
                  Recommended
                </div>
              )}
              
              {/* Plan Header */}
              <div className="text-center mb-4 mt-2">
                <div className="text-3xl mb-2">{plan.emoji}</div>
                <h3 className="text-lg font-bold text-gray-900">{plan.name}</h3>
                <div className="mt-2">
                  <span className="text-2xl font-bold" style={{ color: '#dd2930' }}>
                    ${plan.price.toFixed(2)}
                  </span>
                  <span className="text-sm text-gray-500 ml-1">SGD</span>
                </div>
              </div>

              {/* Coverage List */}
              <div className="space-y-2 mt-4">
                {ALL_COVERAGE_ITEMS.map((item) => {
                  const value = plan.coverage[item.key as keyof typeof plan.coverage]
                  const hasFeature = value !== undefined && value !== false && value !== 0
                  
                  return (
                    <div key={item.key} className="flex items-start text-sm">
                      {hasFeature ? (
                        <>
                          <Check className="w-4 h-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-700">
                            <span className="font-medium">{item.label}:</span>{' '}
                            {typeof value === 'number' ? item.format(value) : item.format(value)}
                          </span>
                        </>
                      ) : (
                        <>
                          <X className="w-4 h-4 text-gray-300 mr-2 flex-shrink-0 mt-0.5" />
                          <span className="text-gray-400">{item.label}</span>
                        </>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>
          )
        })}
      </div>
      <div className="text-xs text-gray-500 text-center mt-4">
        All prices are in Singapore Dollars (SGD)
      </div>
    </div>
  )
}

