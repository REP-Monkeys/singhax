'use client'

import { useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useAuth } from '@/contexts/AuthContext'

export default function LoginPage() {
  const router = useRouter()
  const { login, user } = useAuth()
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  })
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      await login(formData.email, formData.password)

      // After successful login, the auth context will have updated the user
      // We need to wait a moment for the state to update, then check onboarding status
      setTimeout(() => {
        const currentUser = user
        if (currentUser && !currentUser.is_onboarded) {
          router.push('/app/onboarding')
        } else {
          router.push('/app/dashboard')
        }
      }, 100)
    } catch (err: any) {
      setError(err.message || 'An error occurred during login')
    } finally {
      setLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  return (
    <div className="min-h-screen bg-white flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-10">
        <div className="text-center">
          <Link href="/">
            <h1 className="text-2xl font-semibold text-black tracking-tight hover:text-gray-700 transition-colors">
              ConvoTravelInsure
            </h1>
          </Link>
          <h2 className="mt-8 text-3xl font-bold text-black tracking-tight">
            Welcome back
          </h2>
          <p className="mt-3 text-base text-gray-600">
            Don't have an account?{' '}
            <Link href="/app/signup" className="font-medium text-black hover:text-gray-700 underline underline-offset-4">
              Sign up
            </Link>
          </p>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <form className="space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                {error}
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-black mb-2">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                placeholder="you@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-semibold text-black mb-2">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                placeholder="Enter your password"
              />
            </div>

            <div>
              <Button
                type="submit"
                className="w-full bg-black hover:bg-gray-800 text-white font-medium py-3 rounded-full transition-colors"
                disabled={loading}
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </Button>
            </div>
          </form>
        </div>

        <div className="text-center">
          <Link href="/">
            <Button variant="ghost" className="text-gray-600 hover:text-black font-medium">
              ← Back to home
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
