'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Check, X, Edit2 } from 'lucide-react'

interface ExtractedDataCardProps {
  extractedData: any
  onConfirm: () => void
  onEdit: () => void
  onReject: () => void
}

export function ExtractedDataCard({
  extractedData,
  onConfirm,
  onEdit,
  onReject
}: ExtractedDataCardProps) {
  const [isEditing, setIsEditing] = useState(false)

  if (!extractedData) return null

  const documentType = extractedData.document_type || 'document'
  const documentTypeLabel = documentType
    .split('_')
    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')

  // Extract key information for display
  const displayData: { label: string; value: any }[] = []

  // Flight confirmation data
  if (extractedData.destination) {
    const dest = extractedData.destination
    displayData.push({
      label: 'Destination',
      value: `${dest.city || ''}${dest.city && dest.country ? ', ' : ''}${dest.country || ''}`.trim() || dest.value
    })
  }

  if (extractedData.flight_details) {
    const fd = extractedData.flight_details
    if (fd.departure?.date) {
      displayData.push({ label: 'Departure Date', value: fd.departure.date })
    }
    if (fd.return?.date) {
      displayData.push({ label: 'Return Date', value: fd.return.date })
    }
  }

  // Trip details (from normalized structure)
  if (extractedData.trip_details) {
    const td = extractedData.trip_details
    if (td.departure_date?.value) {
      displayData.push({ label: 'Departure Date', value: td.departure_date.value })
    }
    if (td.return_date?.value) {
      displayData.push({ label: 'Return Date', value: td.return_date.value })
    }
    if (td.destination?.country) {
      displayData.push({ label: 'Destination', value: td.destination.country })
    }
  }

  // Travelers
  if (extractedData.travelers && Array.isArray(extractedData.travelers)) {
    const travelerNames = extractedData.travelers
      .map((t: any) => t.name?.full || `${t.name?.first || ''} ${t.name?.last || ''}`.trim())
      .filter((n: string) => n)
    if (travelerNames.length > 0) {
      displayData.push({ label: 'Travelers', value: travelerNames.join(', ') })
    }
  }

  // Trip duration
  if (extractedData.trip_duration?.days) {
    displayData.push({ label: 'Duration', value: `${extractedData.trip_duration.days} days` })
  }

  // Trip value
  if (extractedData.trip_value?.total_cost?.amount) {
    const cost = extractedData.trip_value.total_cost
    displayData.push({
      label: 'Trip Value',
      value: `${cost.currency || 'SGD'} ${cost.amount.toFixed(2)}`
    })
  }

  return (
    <Card className="mt-4 border-2 border-blue-200 bg-blue-50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold text-gray-900">
            📄 Extracted Information ({documentTypeLabel})
          </CardTitle>
          {!isEditing && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsEditing(true)}
              className="h-8 w-8 p-0"
            >
              <Edit2 className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {displayData.length > 0 ? (
            displayData.map((item, idx) => (
              <div key={idx} className="flex justify-between items-start">
                <span className="font-medium text-gray-700 text-sm">{item.label}:</span>
                <span className="text-gray-900 text-sm text-right">{String(item.value || 'N/A')}</span>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-600">Processing document information...</p>
          )}

          {extractedData.low_confidence_fields && extractedData.low_confidence_fields.length > 0 && (
            <div className="mt-3 pt-3 border-t border-gray-300">
              <p className="text-xs text-amber-600 font-medium mb-1">
                ⚠️ Low confidence fields (please verify):
              </p>
              <ul className="text-xs text-amber-700 list-disc list-inside">
                {extractedData.low_confidence_fields.map((field: string, idx: number) => (
                  <li key={idx}>{field}</li>
                ))}
              </ul>
            </div>
          )}

          {extractedData.missing_fields && extractedData.missing_fields.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-600">
                Missing: {extractedData.missing_fields.join(', ')}
              </p>
            </div>
          )}

          {!isEditing && (
            <div className="flex gap-2 mt-4 pt-3 border-t border-gray-300">
              <Button
                onClick={onConfirm}
                className="flex-1 bg-green-600 hover:bg-green-700 text-white"
                size="sm"
              >
                <Check className="w-4 h-4 mr-2" />
                Confirm
              </Button>
              <Button
                onClick={onEdit}
                variant="outline"
                className="flex-1"
                size="sm"
              >
                <Edit2 className="w-4 h-4 mr-2" />
                Edit
              </Button>
              <Button
                onClick={onReject}
                variant="outline"
                className="flex-1 border-red-300 text-red-700 hover:bg-red-50"
                size="sm"
              >
                <X className="w-4 h-4 mr-2" />
                Reject
              </Button>
            </div>
          )}

          {isEditing && (
            <div className="mt-4 pt-3 border-t border-gray-300">
              <p className="text-sm text-gray-700 mb-2">
                You can edit the information by typing corrections in the chat.
              </p>
              <Button
                onClick={() => setIsEditing(false)}
                variant="outline"
                size="sm"
                className="w-full"
              >
                Done Editing
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

