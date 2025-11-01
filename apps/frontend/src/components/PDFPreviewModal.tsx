'use client'

import { useState, useEffect } from 'react'
import { X, Download, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface PDFPreviewModalProps {
  documentId: string
  filename: string
  onClose: () => void
  authToken: string
}

export function PDFPreviewModal({ documentId, filename, onClose, authToken }: PDFPreviewModalProps) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let currentUrl: string | null = null
    
    const fetchPDF = async () => {
      try {
        setLoading(true)
        setError(null)
        
        const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
        const response = await fetch(`${backendUrl}/documents/${documentId}/file`, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        })

        if (!response.ok) {
          throw new Error('Failed to fetch PDF file')
        }

        const blob = await response.blob()
        const url = URL.createObjectURL(blob)
        currentUrl = url
        setPdfUrl(url)
      } catch (err: any) {
        console.error('Error fetching PDF:', err)
        setError(err.message || 'Failed to load PDF')
      } finally {
        setLoading(false)
      }
    }

    fetchPDF()

    // Cleanup blob URL on unmount or when documentId/authToken changes
    return () => {
      if (currentUrl) {
        URL.revokeObjectURL(currentUrl)
      }
    }
  }, [documentId, authToken])

  // Cleanup blob URL when component unmounts
  useEffect(() => {
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl)
      }
    }
  }, [pdfUrl])

  const handleDownload = async () => {
    if (!pdfUrl) return
    
    try {
      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${backendUrl}/documents/${documentId}/file`, {
        headers: {
          'Authorization': `Bearer ${authToken}`,
        },
      })

      if (!response.ok) {
        throw new Error('Failed to download PDF')
      }

      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Error downloading PDF:', err)
    }
  }


  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col m-4">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-black truncate flex-1 mr-4">
            {filename}
          </h2>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleDownload}
              className="text-gray-700 hover:text-black"
            >
              <Download className="w-4 h-4 mr-2" />
              Download
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClose}
              className="text-gray-700 hover:text-black"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>
        </div>

        {/* PDF Viewer */}
        <div className="flex-1 overflow-auto p-4 bg-gray-50 flex items-center justify-center">
          {loading && (
            <div className="flex flex-col items-center gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
              <p className="text-sm text-gray-600">Loading PDF...</p>
            </div>
          )}

          {error && (
            <div className="text-center">
              <p className="text-red-600 mb-4">{error}</p>
              <Button onClick={onClose} variant="outline">
                Close
              </Button>
            </div>
          )}

          {pdfUrl && !loading && !error && (
            <div className="w-full h-full flex items-center justify-center min-h-[600px]">
              <iframe
                src={pdfUrl}
                className="w-full h-full border-0 rounded-lg shadow-sm"
                title={filename}
                style={{ minHeight: '600px' }}
                onError={() => {
                  setError('Failed to load PDF document')
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

