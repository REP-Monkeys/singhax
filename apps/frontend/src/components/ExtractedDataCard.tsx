'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Check, X, Edit2, Save } from 'lucide-react'
import { supabase } from '@/lib/supabase'

interface ExtractedDataCardProps {
  extractedData: any
  documentId?: string  // Document ID for updating
  onConfirm: () => void
  onEdit: () => void
  onReject: () => void
  onSave?: (updatedData: any) => void  // Callback after successful save
}

export function ExtractedDataCard({
  extractedData,
  documentId,
  onConfirm,
  onEdit,
  onReject,
  onSave
}: ExtractedDataCardProps) {
  const [isEditing, setIsEditing] = useState(false)
  const [editedData, setEditedData] = useState<any>(null)
  const [isSaving, setIsSaving] = useState(false)
  
  // Get auth token helper function
  const getAuthToken = async (): Promise<string | null> => {
    const { data: { session } } = await supabase.auth.getSession()
    return session?.access_token || null
  }
  
  // Initialize edited data when entering edit mode
  useEffect(() => {
    if (isEditing && extractedData) {
      setEditedData(JSON.parse(JSON.stringify(extractedData)))  // Deep copy
    }
  }, [isEditing, extractedData])

  if (!extractedData) return null

  const documentType = extractedData.document_type || 'document'
  const documentTypeLabel = documentType
    .split('_')
    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')

  // Helper function to build display data from extracted data
  const buildDisplayData = (data: any): { label: string; value: any; path: string[] }[] => {
    const displayData: { label: string; value: any; path: string[] }[] = []

    // Flight confirmation data
    if (data.destination) {
      const dest = data.destination
      const value = `${dest.city || ''}${dest.city && dest.country ? ', ' : ''}${dest.country || ''}`.trim() || dest.value
      displayData.push({
        label: 'Destination',
        value: value,
        path: ['destination', 'country']  // Path for editing
      })
    }

    if (data.flight_details) {
      const fd = data.flight_details
      if (fd.departure?.date) {
        displayData.push({ 
          label: 'Departure Date', 
          value: fd.departure.date,
          path: ['flight_details', 'departure', 'date']
        })
      }
      if (fd.return?.date) {
        displayData.push({ 
          label: 'Return Date', 
          value: fd.return.date,
          path: ['flight_details', 'return', 'date']
        })
      }
    }

    // Trip details (from normalized structure)
    if (data.trip_details) {
      const td = data.trip_details
      if (td.departure_date?.value) {
        displayData.push({ 
          label: 'Departure Date', 
          value: td.departure_date.value,
          path: ['trip_details', 'departure_date', 'value']
        })
      }
      if (td.return_date?.value) {
        displayData.push({ 
          label: 'Return Date', 
          value: td.return_date.value,
          path: ['trip_details', 'return_date', 'value']
        })
      }
      if (td.destination?.country) {
        displayData.push({ 
          label: 'Destination', 
          value: td.destination.country,
          path: ['trip_details', 'destination', 'country']
        })
      }
    }

    // Travelers
    if (data.travelers && Array.isArray(data.travelers)) {
      const travelerNames = data.travelers
        .map((t: any) => t.name?.full || `${t.name?.first || ''} ${t.name?.last || ''}`.trim())
        .filter((n: string) => n)
      if (travelerNames.length > 0) {
        displayData.push({ 
          label: 'Travelers', 
          value: travelerNames.join(', '),
          path: ['travelers']  // Complex structure, simplified editing
        })
      }
    }

    // Trip duration
    if (data.trip_duration?.days) {
      displayData.push({ 
        label: 'Duration', 
        value: `${data.trip_duration.days} days`,
        path: ['trip_duration', 'days']
      })
    }

    // Trip value
    if (data.trip_value?.total_cost?.amount) {
      const cost = data.trip_value.total_cost
      displayData.push({
        label: 'Trip Value',
        value: `${cost.currency || 'SGD'} ${cost.amount.toFixed(2)}`,
        path: ['trip_value', 'total_cost', 'amount']
      })
    }

    return displayData
  }

  const displayData = buildDisplayData(isEditing && editedData ? editedData : extractedData)

  // Helper function to update nested value in edited data
  const updateValue = (path: string[], newValue: any) => {
    if (!editedData) return
    
    const newData = JSON.parse(JSON.stringify(editedData))  // Deep copy
    let current: any = newData
    
    // Navigate to the parent of the target field
    for (let i = 0; i < path.length - 1; i++) {
      if (!current[path[i]]) {
        current[path[i]] = {}
      }
      current = current[path[i]]
    }
    
    // Set the value
    current[path[path.length - 1]] = newValue
    setEditedData(newData)
  }

  // Save handler
  const handleSave = async () => {
    if (!documentId || !editedData) {
      console.error('Cannot save: missing documentId or editedData')
      return
    }

    setIsSaving(true)
    try {
      const token = await getAuthToken()
      if (!token) {
        console.error('No auth token available')
        setIsSaving(false)
        return
      }

      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${API_URL}/documents/${documentId}/extracted-data`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          extracted_data: editedData
        })
      })

      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to save document')
      }

      const result = await response.json()
      
      // Update extractedData with saved data
      if (onSave) {
        onSave(result.extracted_data)
      }
      
      setIsEditing(false)
      alert('Document updated successfully!')
    } catch (error: any) {
      console.error('Save error:', error)
      alert(`Failed to save: ${error.message}`)
    } finally {
      setIsSaving(false)
    }
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
              <div key={idx} className="flex justify-between items-start gap-2">
                <span className="font-medium text-gray-700 text-sm flex-shrink-0">{item.label}:</span>
                {isEditing && editedData ? (
                  <Input
                    value={String(item.value || '')}
                    onChange={(e) => updateValue(item.path, e.target.value)}
                    className="text-sm flex-1 max-w-[200px]"
                    placeholder={item.label}
                  />
                ) : (
                  <span className="text-gray-900 text-sm text-right">{String(item.value || 'N/A')}</span>
                )}
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
                onClick={() => setIsEditing(true)}
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
              <div className="flex gap-2">
                <Button
                  onClick={handleSave}
                  disabled={isSaving || !documentId}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
                  size="sm"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {isSaving ? 'Saving...' : 'Save'}
                </Button>
                <Button
                  onClick={() => {
                    setIsEditing(false)
                    setEditedData(null)
                  }}
                  variant="outline"
                  size="sm"
                  className="flex-1"
                  disabled={isSaving}
                >
                  Cancel
                </Button>
              </div>
              {!documentId && (
                <p className="text-xs text-amber-600 mt-2">
                  ⚠️ Document ID not available. Editing may not work properly.
                </p>
              )}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

