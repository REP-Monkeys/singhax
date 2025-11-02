'use client'

import React, { useEffect } from 'react'
import { XCircle } from 'lucide-react'

export default function PaymentCanceledPage() {
  useEffect(() => {
    // On payment cancellation, refresh the original tab (quote page)
    console.log('❌ Payment was canceled. Refreshing original tab in 3 seconds...')
    
    const timer = setTimeout(() => {
      try {
        if (window.opener) {
          window.opener.location.reload()
          // Don't close this window - user stays on canceled page
        } else {
          // If opener is not available, just stay on this page
          console.log('No opener found, staying on canceled page')
        }
      } catch (error) {
        console.error('Error refreshing opener:', error)
      }
    }, 3000)

    return () => clearTimeout(timer)
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
        <div className="flex justify-center mb-6">
          <div className="rounded-full bg-orange-100 p-4">
            <XCircle className="w-16 h-16 text-orange-600" />
          </div>
        </div>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Payment Canceled
        </h1>
        
        <p className="text-gray-600 mb-6">
          Your payment was canceled. No charges were made. You can complete your purchase whenever you're ready.
        </p>
        
        <p className="text-sm text-gray-500 animate-pulse">
          Redirecting you back...
        </p>
      </div>
    </div>
  )
}

