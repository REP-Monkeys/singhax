'use client'

import React, { useEffect } from 'react'
import { CheckCircle } from 'lucide-react'

export default function PaymentSuccessPage() {
  useEffect(() => {
    // On payment success, refresh the original tab (quote page)
    // This will trigger the payment polling to check for updated state
    console.log('✅ Payment completed successfully! Refreshing original tab in 3 seconds...')
    
    const timer = setTimeout(() => {
      // Refresh the opener (the original tab with the quote page)
      try {
        if (window.opener) {
          window.opener.location.reload()
          // Don't close this window - user stays on success page
        } else {
          // If opener is not available, just stay on this page
          console.log('No opener found, staying on success page')
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
          <div className="rounded-full bg-green-100 p-4">
            <CheckCircle className="w-16 h-16 text-green-600" />
          </div>
        </div>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          Payment Successful!
        </h1>
        
        <p className="text-gray-600 mb-6">
          Your payment has been processed successfully. We're confirming your policy details...
        </p>
        
        <p className="text-sm text-gray-500 animate-pulse">
          Redirecting you back...
        </p>
      </div>
    </div>
  )
}

