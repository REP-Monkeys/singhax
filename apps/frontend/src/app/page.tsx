'use client'

import { useEffect, useState, useRef } from 'react'
import Link from 'next/link'
import { Plane, MessageCircle, Zap, Target, Mic, Users, UsersRound } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

export default function Home() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [visibleSections, setVisibleSections] = useState<Set<string>>(new Set())
  const [parallaxOffset, setParallaxOffset] = useState(0)
  const [ctaParallaxOffset, setCtaParallaxOffset] = useState(0)
  const featuresRef = useRef<HTMLDivElement>(null)
  const ctaRef = useRef<HTMLDivElement>(null)
  const heroRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50)
      
      // Parallax effect for hero image - moves slower than scroll
      const scrollY = window.scrollY || window.pageYOffset
      // Parallax moves at 70% speed of scroll (faster to prevent cropping)
      const offset = scrollY * 0.7
      setParallaxOffset(offset)
      
      // No parallax for CTA section - static image
      setCtaParallaxOffset(0)
    }

    // Use requestAnimationFrame for smoother performance
    let ticking = false
    const onScroll = () => {
      if (!ticking) {
        window.requestAnimationFrame(() => {
          handleScroll()
          ticking = false
        })
        ticking = true
      }
    }

    window.addEventListener('scroll', onScroll, { passive: true })
    handleScroll() // Initial call
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    // Set hero as visible on mount
    setVisibleSections((prev) => new Set(prev).add('hero'))
    
    // Set features header, cards, and CTA as visible initially
    setVisibleSections((prev) => {
      const newSet = new Set(prev)
      newSet.add('features-header')
      newSet.add('cta')
      for (let i = 0; i < 6; i++) {
        newSet.add(`feature-${i}`)
      }
      return newSet
    })

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisibleSections((prev) => new Set(prev).add(entry.target.id))
          }
        })
      },
      { threshold: 0.1 }
    )

    // Observe features header
    setTimeout(() => {
      const featuresHeader = document.getElementById('features-header')
      if (featuresHeader) {
        observer.observe(featuresHeader)
      }

      // Observe feature cards
      if (featuresRef.current) {
        const featureCards = featuresRef.current.querySelectorAll('[data-feature]')
        featureCards.forEach((card, index) => {
          if (!card.id) {
            card.id = `feature-${index}`
          }
          observer.observe(card)
        })
      }

      // Observe CTA section
      if (ctaRef.current) {
        observer.observe(ctaRef.current)
      }
    }, 100)

    return () => observer.disconnect()
  }, [])

  return (
    <div className="min-h-screen" style={{ backgroundImage: 'linear-gradient(120deg, #fdfbfb 0%, #ebedee 100%)' }}>
      {/* Header */}
      <header 
        className={`border-b bg-white sticky top-0 z-50 backdrop-blur-sm transition-all duration-300 ${
          isScrolled ? 'border-gray-300 shadow-md bg-white/95 py-3' : 'border-gray-200 bg-white/90 py-4'
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Plane className="w-7 h-7" style={{ color: '#dd2930' }} />
              <h1 className="text-3xl font-semibold tracking-tight" style={{ color: '#dd2930' }}>TripMate</h1>
            </div>
            <div className="flex items-center space-x-3">
              <Link href="/app/login">
                <Button variant="ghost" className="text-black hover:bg-gray-100 font-medium">Sign In</Button>
              </Link>
              <Link href="/app/quote">
                <Button className="text-white font-medium rounded-full px-6 hover:opacity-90" style={{ backgroundColor: '#dd2930' }}>Get Quote</Button>
              </Link>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div 
        ref={heroRef}
        className="relative text-center py-20 sm:py-32 overflow-hidden w-screen"
        style={{
          marginLeft: 'calc(-50vw + 50%)',
          marginRight: 'calc(-50vw + 50%)',
          width: '100vw',
        }}
      >
          {/* Background Image with Parallax */}
          <div 
            className="absolute inset-0 z-0 overflow-hidden"
          >
            <div
              className="absolute inset-0 w-full h-full"
              style={{
                backgroundImage: `url('/plane-passing-by-sun-cloudy-day.jpg')`,
                backgroundSize: '130% auto',
                backgroundPosition: 'center bottom',
                backgroundRepeat: 'no-repeat',
                transform: `translateY(${parallaxOffset}px)`,
                willChange: 'transform',
              }}
            />
          </div>
          {/* Overlay for text readability */}
          <div className="absolute inset-0 bg-gradient-to-b from-white/60 via-white/40 to-white/60 z-0" />
          
          {/* Content */}
          <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h1 
              className="text-5xl sm:text-7xl font-bold tracking-tight text-black leading-tight transition-all duration-1000 drop-shadow-lg"
              style={{ 
                opacity: visibleSections.has('hero') ? 1 : 0,
                transform: visibleSections.has('hero') ? 'translateY(0)' : 'translateY(20px)'
              }}
            >
              Travel insurance,<br />reimagined
            </h1>
            <p 
              className="mt-8 text-xl leading-8 text-gray-700 max-w-2xl mx-auto transition-all duration-1000 delay-200 font-medium"
              style={{ 
                opacity: visibleSections.has('hero') ? 1 : 0,
                transform: visibleSections.has('hero') ? 'translateY(0)' : 'translateY(20px)'
              }}
            >
              Get personalized quotes through conversation. No forms, no hassle. 
              Just intelligent coverage for your journey.
            </p>
            <div 
              className="mt-12 flex items-center justify-center gap-x-4 transition-all duration-1000 delay-300"
              style={{ 
                opacity: visibleSections.has('hero') ? 1 : 0,
                transform: visibleSections.has('hero') ? 'translateY(0)' : 'translateY(20px)'
              }}
            >
              <Link href="/app/quote">
                <Button size="lg" className="text-white font-medium rounded-full px-8 py-6 text-lg hover:opacity-90 shadow-lg" style={{ backgroundColor: '#dd2930' }}>
                  Get started
                </Button>
              </Link>
              <Link href="#features">
                <Button variant="ghost" size="lg" className="text-black hover:bg-white/80 font-medium rounded-full px-8 py-6 text-lg bg-white/60 backdrop-blur-sm">
                  Learn more
                </Button>
              </Link>
            </div>
          </div>
      </div>

      {/* Features Section */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div id="features" className="py-20 border-t border-gray-200" ref={featuresRef}>
          <div 
            className="text-center mb-16 transition-all duration-1000"
            style={{ 
              opacity: visibleSections.has('features-header') ? 1 : 0,
              transform: visibleSections.has('features-header') ? 'translateY(0)' : 'translateY(30px)'
            }}
            id="features-header"
          >
            <h2 className="text-4xl sm:text-5xl font-bold tracking-tight text-black">
              Built for modern travelers
            </h2>
            <p className="mt-6 text-xl text-gray-600 max-w-2xl mx-auto">
              Everything you need for stress-free travel protection
            </p>
          </div>
          
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <div 
              className="bg-white p-8 hover:bg-gray-50 transition-all duration-500 rounded-xl"
              data-feature
            >
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full text-white" style={{ backgroundColor: '#dd2930' }}>
                    <MessageCircle className="w-6 h-6" />
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

            <div 
              className="bg-white p-8 hover:bg-gray-50 transition-all duration-500 rounded-xl"
              data-feature
            >
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full text-white" style={{ backgroundColor: '#dd2930' }}>
                    <Zap className="w-6 h-6" />
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

            <div 
              className="bg-white p-8 hover:bg-gray-50 transition-all duration-500 rounded-xl"
              data-feature
            >
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full text-white" style={{ backgroundColor: '#dd2930' }}>
                    <Target className="w-6 h-6" />
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

            <div 
              className="bg-white p-8 hover:bg-gray-50 transition-all duration-500 rounded-xl"
              data-feature
            >
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full text-white" style={{ backgroundColor: '#dd2930' }}>
                    <Mic className="w-6 h-6" />
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

            <div 
              className="bg-white p-8 hover:bg-gray-50 transition-all duration-500 rounded-xl"
              data-feature
            >
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full text-white" style={{ backgroundColor: '#dd2930' }}>
                    <Users className="w-6 h-6" />
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

            <div 
              className="bg-white p-8 hover:bg-gray-50 transition-all duration-500 rounded-xl"
              data-feature
            >
              <div className="flex items-start">
                <div className="flex-shrink-0">
                  <div className="flex items-center justify-center h-12 w-12 rounded-full text-white" style={{ backgroundColor: '#dd2930' }}>
                    <UsersRound className="w-6 h-6" />
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
          <div 
            ref={ctaRef}
            id="cta"
            className="relative rounded-3xl p-12 sm:p-16 text-center transition-all duration-1000 overflow-hidden"
          >
            {/* Background Image with Parallax */}
            <div 
              className="absolute inset-0 z-0"
            >
              <div
                className="absolute inset-0 w-full h-full"
                style={{
                  backgroundImage: `url('/beautiful-view-starry-sky-against-night-sky.jpg')`,
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                  backgroundRepeat: 'no-repeat',
                }}
              />
            </div>
            {/* Dark overlay for text readability */}
            <div className="absolute inset-0 bg-black/40 z-0 rounded-3xl" />
            
            {/* Content */}
            <div className="relative z-10">
              <h2 className="text-4xl sm:text-5xl font-bold text-white">
                Ready to travel worry-free?
              </h2>
              <p className="mt-6 text-xl text-gray-200 max-w-2xl mx-auto">
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
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-200 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <p className="text-sm text-gray-600">&copy; 2025 TripMate. All rights reserved.</p>
            <p className="mt-2 text-xs text-gray-500">
              Demo application
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}