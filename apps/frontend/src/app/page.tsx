import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="border-b border-gray-200 bg-white sticky top-0 z-50 backdrop-blur-sm bg-white/90">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-xl font-semibold text-black tracking-tight">ConvoTravelInsure</h1>
            </div>
            <div className="flex items-center space-x-3">
              <Link href="/app/login">
                <Button variant="ghost" className="text-black hover:bg-gray-100 font-medium">Sign In</Button>
              </Link>
              <Link href="/app/quote">
                <Button className="bg-black hover:bg-gray-800 text-white font-medium rounded-full px-6">Get Quote</Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center py-20 sm:py-32 animate-fade-in">
          <h1 className="text-5xl sm:text-7xl font-bold tracking-tight text-black leading-tight">
            Travel insurance,<br />reimagined
          </h1>
          <p className="mt-8 text-xl leading-8 text-gray-600 max-w-2xl mx-auto">
            Get personalized quotes through conversation. No forms, no hassle. 
            Just intelligent coverage for your journey.
          </p>
          <div className="mt-12 flex items-center justify-center gap-x-4">
            <Link href="/app/quote">
              <Button size="lg" className="bg-black hover:bg-gray-800 text-white font-medium rounded-full px-8 py-6 text-lg">
                Get started
              </Button>
            </Link>
            <Link href="#features">
              <Button variant="ghost" size="lg" className="text-black hover:bg-gray-100 font-medium rounded-full px-8 py-6 text-lg">
                Learn more
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="py-20 border-t border-gray-200">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-black">
              Built for modern travelers
            </h2>
            <p className="mt-6 text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need for stress-free travel protection
            </p>
          </div>
          
          <div className="grid grid-cols-1 gap-px bg-gray-200 sm:grid-cols-2 lg:grid-cols-3">
            <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-black text-white text-2xl">
                    💬
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-black">Conversational quotes</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Get personalized quotes through natural conversation. No lengthy forms to fill.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-black text-white text-2xl">
                    📋
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-black">Instant answers</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Ask questions about your coverage and get accurate answers in plain English.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-black text-white text-2xl">
                    🎯
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-black">Claims guidance</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Step-by-step help with filing claims and document requirements.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-black text-white text-2xl">
                    🎤
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-black">Voice support</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Speak naturally for hands-free interaction while on the go.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-black text-white text-2xl">
                    👥
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-black">Human support</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Connect with expert agents whenever you need extra help.
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-white p-8 hover:bg-gray-50 transition-colors">
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full bg-black text-white text-2xl">
                    👨‍👩‍👧‍👦
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-semibold text-black">Group coverage</h3>
                  <p className="mt-2 text-base text-gray-600">
                    Manage insurance for families and groups with automatic discounts.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="py-20 border-t border-gray-200">
          <div className="bg-black rounded-3xl p-12 sm:p-16 text-center">
            <h2 className="text-4xl sm:text-5xl font-bold text-white">
              Ready to travel worry-free?
            </h2>
            <p className="mt-6 text-xl text-gray-300 max-w-2xl mx-auto">
              Join thousands of travelers who trust us for their coverage needs.
            </p>
            <div className="mt-10">
              <Link href="/app/quote">
                <Button size="lg" className="bg-white hover:bg-gray-100 text-black font-medium rounded-full px-8 py-6 text-lg">
                  Get your quote
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-sm text-gray-600">&copy; 2025 ConvoTravelInsure. All rights reserved.</p>
            <p className="mt-2 text-xs text-gray-500">
              Demo application
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}