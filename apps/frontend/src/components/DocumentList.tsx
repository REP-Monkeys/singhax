'use client'

import { useState, useEffect } from 'react'
import { Card } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { FileText, Calendar, Plane, Hotel, FileCheck, MapPin, Loader2 } from 'lucide-react'
import { PDFPreviewModal } from './PDFPreviewModal'

export type DocumentType = 'flight' | 'hotel' | 'visa' | 'itinerary' | 'all'

interface DocumentSummary {
  airline?: string  // Backward compatibility
  trip_type?: "one_way" | "return"
  outbound_airline?: string
  inbound_airline?: string
  departure_date?: string
  destination?: string
  hotel_name?: string
  check_in_date?: string
  location?: string
  visa_type?: string
  destination_country?: string
  applicant?: string
  trip_title?: string
  start_date?: string
  duration_days?: number
  has_adventure_sports?: boolean
}

interface Document {
  id: string
  type: 'flight' | 'hotel' | 'visa' | 'itinerary'
  filename: string
  created_at: string
  extracted_at?: string
  summary: DocumentSummary
}

interface DocumentListProps {
  authToken: string
}

export function DocumentList({ authToken }: DocumentListProps) {
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedFilter, setSelectedFilter] = useState<DocumentType>('all')
  const [selectedDocument, setSelectedDocument] = useState<Document | null>(null)

  useEffect(() => {
    fetchDocuments()
  }, [selectedFilter])

  const fetchDocuments = async () => {
    setLoading(true)
    setError(null)
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      let url = `${backendUrl}/documents`
      
      if (selectedFilter !== 'all') {
        url += `?type=${selectedFilter}`
      }

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch documents')
      }

      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (err: any) {
      console.error('Error fetching documents:', err)
      setError(err.message || 'Failed to load documents')
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const getDocumentTypeIcon = (type: string) => {
    switch (type) {
      case 'flight':
        return <Plane className="w-5 h-5" />
      case 'hotel':
        return <Hotel className="w-5 h-5" />
      case 'visa':
        return <FileCheck className="w-5 h-5" />
      case 'itinerary':
        return <MapPin className="w-5 h-5" />
      default:
        return <FileText className="w-5 h-5" />
    }
  }

  const getDocumentTypeColor = (type: string) => {
    switch (type) {
      case 'flight':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'hotel':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'visa':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'itinerary':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getDocumentSummary = (doc: Document) => {
    const { summary, type } = doc
    switch (type) {
      case 'flight':
        const tripType = summary.trip_type || 'one_way'  // Default to one_way if not provided
        const outboundAirline = summary.outbound_airline || summary.airline || 'Flight'
        const inboundAirline = summary.inbound_airline
        const destination = summary.destination || ''
        const departureDate = summary.departure_date ? ` on ${formatDate(summary.departure_date)}` : ''
        
        // Build airline display
        let airlineDisplay = outboundAirline
        if (tripType === 'return' && inboundAirline && inboundAirline !== outboundAirline) {
          // Different airlines for going and returning
          airlineDisplay = `${outboundAirline} → ${inboundAirline}`
        }
        
        // Build trip type suffix
        const tripTypeSuffix = tripType === 'return' ? ' (Return)' : ' (One-Way)'
        
        return `${airlineDisplay}${destination ? ` to ${destination}` : ''}${departureDate}${tripTypeSuffix}`
      case 'hotel':
        return `${summary.hotel_name || 'Hotel'}${summary.location ? ` in ${summary.location}` : ''}${summary.check_in_date ? ` - Check-in: ${formatDate(summary.check_in_date)}` : ''}`
      case 'visa':
        return `${summary.visa_type || 'Visa'}${summary.destination_country ? ` for ${summary.destination_country}` : ''}${summary.applicant ? ` - ${summary.applicant}` : ''}`
      case 'itinerary':
        return `${summary.trip_title || 'Itinerary'}${summary.start_date ? ` starting ${formatDate(summary.start_date)}` : ''}${summary.duration_days ? ` (${summary.duration_days} days)` : ''}`
      default:
        return 'Document'
    }
  }

  const filters: { label: string; value: DocumentType }[] = [
    { label: 'All', value: 'all' },
    { label: 'Flight', value: 'flight' },
    { label: 'Hotel', value: 'hotel' },
    { label: 'Visa', value: 'visa' },
    { label: 'Itinerary', value: 'itinerary' },
  ]

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
          <p className="text-sm text-gray-600">Loading documents...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6 text-sm">
        {error}
      </div>
    )
  }

  return (
    <>
      {/* Filter Buttons */}
      <div className="flex flex-wrap gap-2 mb-6">
        {filters.map((filter) => (
          <button
            key={filter.value}
            onClick={() => setSelectedFilter(filter.value)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              selectedFilter === filter.value
                ? 'bg-black text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Documents Grid */}
      {documents.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <FileText className="w-8 h-8 text-gray-400" />
          </div>
          <h3 className="text-xl font-semibold text-black mb-2">
            No documents found
          </h3>
          <p className="text-gray-600 max-w-md mx-auto">
            {selectedFilter === 'all'
              ? 'You haven\'t uploaded any documents yet. Upload documents during a quote conversation to see them here.'
              : `No ${selectedFilter} documents found.`}
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {documents.map((doc) => (
            <Card
              key={doc.id}
              onClick={() => setSelectedDocument(doc)}
              className="group cursor-pointer hover:shadow-lg transition-shadow duration-200 overflow-hidden border border-gray-200 rounded-xl"
            >
              <div className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2 flex-1 min-w-0">
                    <div className={`p-2 rounded-lg ${getDocumentTypeColor(doc.type)}`}>
                      {getDocumentTypeIcon(doc.type)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-black truncate text-sm">
                        {doc.filename}
                      </h3>
                    </div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Badge
                    variant="outline"
                    className={`text-xs ${getDocumentTypeColor(doc.type)}`}
                  >
                    {doc.type.charAt(0).toUpperCase() + doc.type.slice(1)}
                  </Badge>

                  <div className="flex items-center text-xs text-gray-600">
                    <Calendar className="w-3 h-3 mr-1.5 flex-shrink-0" />
                    <span>{formatDate(doc.created_at)}</span>
                  </div>

                  <p className="text-sm text-gray-700 line-clamp-2">
                    {getDocumentSummary(doc)}
                  </p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* PDF Preview Modal */}
      {selectedDocument && (
        <PDFPreviewModal
          documentId={selectedDocument.id}
          filename={selectedDocument.filename}
          onClose={() => setSelectedDocument(null)}
          authToken={authToken}
        />
      )}
    </>
  )
}

