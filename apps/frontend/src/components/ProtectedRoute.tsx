'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
  requireOnboarding?: boolean
}

export function ProtectedRoute({ children, requireOnboarding = false }: ProtectedRouteProps) {
  const { user, loading, isAuthenticated } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading) {
      // If not authenticated, redirect to login
      if (!isAuthenticated) {
        router.push('/app/login')
        return
      }

      // If authenticated but not onboarded, redirect to onboarding
      if (user && !user.is_onboarded && requireOnboarding) {
        router.push('/app/onboarding')
        return
      }

      // If authenticated and onboarded but trying to access onboarding, redirect to quote
      if (user && user.is_onboarded && !requireOnboarding && window.location.pathname === '/app/onboarding') {
        router.push('/app/quote')
        return
      }
    }
  }, [user, loading, isAuthenticated, requireOnboarding, router])

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-700"></div>
          <p className="mt-4 text-gray-900 font-medium">Loading...</p>
        </div>
      </div>
    )
  }

  // Don't render children until auth check is complete
  if (!isAuthenticated) {
    return null
  }

  // If requires onboarding and user is not onboarded, don't render
  if (requireOnboarding && user && !user.is_onboarded) {
    return null
  }

  return <>{children}</>
}
