'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ProtectedRoute } from '@/components/ProtectedRoute'
import { useAuth } from '@/contexts/AuthContext'
import { supabase } from '@/lib/supabase'

// Comprehensive list of countries
const COUNTRIES = [
  "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda",
  "Argentina", "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain",
  "Bangladesh", "Barbados", "Belarus", "Belgium", "Belize", "Benin", "Bhutan",
  "Bolivia", "Bosnia and Herzegovina", "Botswana", "Brazil", "Brunei", "Bulgaria",
  "Burkina Faso", "Burundi", "Cabo Verde", "Cambodia", "Cameroon", "Canada",
  "Central African Republic", "Chad", "Chile", "China", "Colombia", "Comoros",
  "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
  "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt",
  "El Salvador", "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia",
  "Fiji", "Finland", "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana",
  "Greece", "Grenada", "Guatemala", "Guinea", "Guinea-Bissau", "Guyana", "Haiti",
  "Honduras", "Hungary", "Iceland", "India", "Indonesia", "Iran", "Iraq", "Ireland",
  "Israel", "Italy", "Jamaica", "Japan", "Jordan", "Kazakhstan", "Kenya", "Kiribati",
  "Kosovo", "Kuwait", "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho",
  "Liberia", "Libya", "Liechtenstein", "Lithuania", "Luxembourg", "Madagascar",
  "Malawi", "Malaysia", "Maldives", "Mali", "Malta", "Marshall Islands", "Mauritania",
  "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco", "Mongolia", "Montenegro",
  "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal", "Netherlands",
  "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Korea", "North Macedonia",
  "Norway", "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea",
  "Paraguay", "Peru", "Philippines", "Poland", "Portugal", "Qatar", "Romania",
  "Russia", "Rwanda", "Saint Kitts and Nevis", "Saint Lucia",
  "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe",
  "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore",
  "Slovakia", "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Korea",
  "South Sudan", "Spain", "Sri Lanka", "Sudan", "Suriname", "Sweden", "Switzerland",
  "Syria", "Taiwan", "Tajikistan", "Tanzania", "Thailand", "Timor-Leste", "Togo",
  "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey", "Turkmenistan", "Tuvalu",
  "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom", "United States",
  "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam",
  "Yemen", "Zambia", "Zimbabwe"
]

// Popular country codes for phone numbers
const COUNTRY_CODES = [
  { code: "+1", country: "US/Canada" },
  { code: "+44", country: "UK" },
  { code: "+61", country: "Australia" },
  { code: "+65", country: "Singapore" },
  { code: "+86", country: "China" },
  { code: "+91", country: "India" },
  { code: "+81", country: "Japan" },
  { code: "+82", country: "South Korea" },
  { code: "+49", country: "Germany" },
  { code: "+33", country: "France" },
]

interface OnboardingFormData {
  date_of_birth: string
  phone_number: string
  country_code: string
  nationality: string
  passport_number: string
  country_of_residence: string
  state_province: string
  city: string
  postal_code: string
  emergency_contact_name: string
  emergency_contact_phone: string
  emergency_contact_relationship: string
  has_pre_existing_conditions: boolean
  is_frequent_traveler: boolean
  preferred_coverage_type: string
}

export default function OnboardingPage() {
  const router = useRouter()
  const { refreshUser } = useAuth()
  const [step, setStep] = useState(1)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const [formData, setFormData] = useState<OnboardingFormData>({
    date_of_birth: '',
    phone_number: '',
    country_code: '+1',
    nationality: '',
    passport_number: '',
    country_of_residence: '',
    state_province: '',
    city: '',
    postal_code: '',
    emergency_contact_name: '',
    emergency_contact_phone: '',
    emergency_contact_relationship: '',
    has_pre_existing_conditions: false,
    is_frequent_traveler: false,
    preferred_coverage_type: 'basic'
  })
  const [postalCodeLoading, setPostalCodeLoading] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value
    }))
  }

  // Postal code autofill function using Zippopotam API (free, no API key required)
  const handlePostalCodeChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const postalCode = e.target.value
    setFormData(prev => ({ ...prev, postal_code: postalCode }))

    // Only attempt autofill if postal code looks complete (at least 3 characters)
    if (postalCode.length >= 3) {
      setPostalCodeLoading(true)
      try {
        // Map country names to ISO codes for the API
        const countryCodeMap: { [key: string]: string } = {
          'United States': 'us',
          'Canada': 'ca',
          'United Kingdom': 'gb',
          'Germany': 'de',
          'France': 'fr',
          'Spain': 'es',
          'Italy': 'it',
          'Australia': 'au',
          'Singapore': 'sg',
          'Japan': 'jp',
          'India': 'in',
          'Netherlands': 'nl',
          'Belgium': 'be',
          'Switzerland': 'ch',
          'Austria': 'at',
          'Sweden': 'se',
          'Norway': 'no',
          'Denmark': 'dk',
          'Poland': 'pl',
          'Portugal': 'pt',
          'Czech Republic': 'cz',
          'Mexico': 'mx',
          'Brazil': 'br',
          'Argentina': 'ar',
          'New Zealand': 'nz',
          'South Korea': 'kr',
          'Turkey': 'tr',
          'Russia': 'ru',
          'South Africa': 'za'
        }

        const countryCode = countryCodeMap[formData.country_of_residence]
        if (countryCode) {
          const response = await fetch(`https://api.zippopotam.us/${countryCode}/${postalCode}`)
          if (response.ok) {
            const data = await response.json()
            if (data.places && data.places.length > 0) {
              const place = data.places[0]
              setFormData(prev => ({
                ...prev,
                city: place['place name'] || prev.city,
                state_province: place['state'] || place['state abbreviation'] || prev.state_province,
                country_of_residence: data.country || prev.country_of_residence
              }))
            }
          }
        }
      } catch (error) {
        // Silently fail - user can still fill in manually
        console.log('Postal code lookup failed, user can fill manually')
      } finally {
        setPostalCodeLoading(false)
      }
    }
  }

  const handleNext = () => {
    setStep(step + 1)
  }

  const handlePrevious = () => {
    setStep(step - 1)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Get session from Supabase
      const { data: { session }, error: sessionError } = await supabase.auth.getSession()

      if (sessionError || !session) {
        throw new Error('No authentication session found')
      }

      const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'
      const response = await fetch(`${backendUrl}/auth/onboarding`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({
          ...formData,
          date_of_birth: new Date(formData.date_of_birth).toISOString()
        }),
      })

      if (!response.ok) {
        const data = await response.json()
        throw new Error(data.detail || 'Onboarding failed')
      }

      // Refresh user data to update onboarding status
      await refreshUser()

      // Redirect to dashboard
      router.push('/app/dashboard')
    } catch (err: any) {
      setError(err.message || 'An error occurred during onboarding')
    } finally {
      setLoading(false)
    }
  }

  const totalSteps = 4

  return (
    <ProtectedRoute requireOnboarding={false}>
      <div className="min-h-screen bg-white py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-2xl font-semibold text-black tracking-tight">ConvoTravelInsure</h1>
          <h2 className="mt-6 text-3xl font-bold text-black tracking-tight">
            Complete your profile
          </h2>
          <p className="mt-3 text-base text-gray-600">
            Step {step} of {totalSteps}
          </p>
          <div className="mt-6 w-full bg-gray-200 rounded-full h-1.5">
            <div
              className="bg-black h-1.5 rounded-full transition-all duration-300 ease-out"
              style={{ width: `${(step / totalSteps) * 100}%` }}
            />
          </div>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-black">
              {step === 1 && "Personal information"}
              {step === 2 && "Address information"}
              {step === 3 && "Emergency contact"}
              {step === 4 && "Travel preferences"}
            </h3>
          </div>
          <div>
            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}

              {/* Step 1: Personal Information */}
              {step === 1 && (
                <div className="space-y-5">
                  <div>
                    <label htmlFor="date_of_birth" className="block text-sm font-semibold text-black mb-2">
                      Date of birth *
                    </label>
                    <input
                      id="date_of_birth"
                      name="date_of_birth"
                      type="date"
                      required
                      value={formData.date_of_birth}
                      onChange={handleInputChange}
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    />
                  </div>

                  <div>
                    <label htmlFor="phone_number" className="block text-sm font-semibold text-black mb-2">
                      Phone number *
                    </label>
                    <div className="flex gap-2">
                      <select
                        id="country_code"
                        name="country_code"
                        value={formData.country_code}
                        onChange={handleInputChange}
                        className="block w-32 px-4 py-3 border border-gray-300 rounded-lg text-black focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                      >
                        {COUNTRY_CODES.map(({ code, country }) => (
                          <option key={code} value={code}>
                            {code}
                          </option>
                        ))}
                      </select>
                      <input
                        id="phone_number"
                        name="phone_number"
                        type="tel"
                        required
                        value={formData.phone_number}
                        onChange={handleInputChange}
                        placeholder="234 567 8900"
                        className="block flex-1 px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                      />
                    </div>
                  </div>

                  <div>
                    <label htmlFor="nationality" className="block text-sm font-semibold text-black mb-2">
                      Nationality *
                    </label>
                    <select
                      id="nationality"
                      name="nationality"
                      required
                      value={formData.nationality}
                      onChange={handleInputChange}
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    >
                      <option value="">Select your nationality</option>
                      {COUNTRIES.map(country => (
                        <option key={country} value={country}>
                          {country}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="passport_number" className="block text-sm font-semibold text-black mb-2">
                      Passport number (optional)
                    </label>
                    <input
                      id="passport_number"
                      name="passport_number"
                      type="text"
                      value={formData.passport_number}
                      onChange={handleInputChange}
                      placeholder="ABC123456"
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    />
                    <p className="mt-2 text-xs text-gray-500">
                      Passport information is securely encrypted
                    </p>
                  </div>
                </div>
              )}

              {/* Step 2: Address Information */}
              {step === 2 && (
                <div className="space-y-5">
                  <div>
                    <label htmlFor="country_of_residence" className="block text-sm font-semibold text-black mb-2">
                      Country of residence *
                    </label>
                    <select
                      id="country_of_residence"
                      name="country_of_residence"
                      required
                      value={formData.country_of_residence}
                      onChange={handleInputChange}
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    >
                      <option value="">Select your country</option>
                      {COUNTRIES.map(country => (
                        <option key={country} value={country}>
                          {country}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label htmlFor="postal_code" className="block text-sm font-semibold text-black mb-2">
                      Postal code *
                    </label>
                    <input
                      id="postal_code"
                      name="postal_code"
                      type="text"
                      required
                      value={formData.postal_code}
                      onChange={handlePostalCodeChange}
                      placeholder="Enter postal code"
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    />
                    {postalCodeLoading && (
                      <p className="mt-2 text-xs text-gray-600">Looking up address...</p>
                    )}
                    {!postalCodeLoading && (
                      <p className="mt-2 text-xs text-gray-500">
                        Auto-fills city and state based on postal code
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="city" className="block text-sm font-semibold text-black mb-2">
                      City *
                    </label>
                    <input
                      id="city"
                      name="city"
                      type="text"
                      required
                      value={formData.city}
                      onChange={handleInputChange}
                      placeholder="San Francisco"
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    />
                  </div>

                  <div>
                    <label htmlFor="state_province" className="block text-sm font-semibold text-black mb-2">
                      State / Province
                    </label>
                    <input
                      id="state_province"
                      name="state_province"
                      type="text"
                      value={formData.state_province}
                      onChange={handleInputChange}
                      placeholder="California"
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    />
                  </div>
                </div>
              )}

              {/* Step 3: Emergency Contact */}
              {step === 3 && (
                <div className="space-y-5">
                  <div>
                    <label htmlFor="emergency_contact_name" className="block text-sm font-semibold text-black mb-2">
                      Emergency contact name *
                    </label>
                    <input
                      id="emergency_contact_name"
                      name="emergency_contact_name"
                      type="text"
                      required
                      value={formData.emergency_contact_name}
                      onChange={handleInputChange}
                      placeholder="John Doe"
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    />
                  </div>

                  <div>
                    <label htmlFor="emergency_contact_phone" className="block text-sm font-semibold text-black mb-2">
                      Emergency contact phone *
                    </label>
                    <input
                      id="emergency_contact_phone"
                      name="emergency_contact_phone"
                      type="tel"
                      required
                      value={formData.emergency_contact_phone}
                      onChange={handleInputChange}
                      placeholder="+1 234 567 8900"
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black placeholder-gray-400 focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    />
                  </div>

                  <div>
                    <label htmlFor="emergency_contact_relationship" className="block text-sm font-semibold text-black mb-2">
                      Relationship *
                    </label>
                    <select
                      id="emergency_contact_relationship"
                      name="emergency_contact_relationship"
                      required
                      value={formData.emergency_contact_relationship}
                      onChange={handleInputChange}
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    >
                      <option value="">Select relationship</option>
                      <option value="spouse">Spouse</option>
                      <option value="parent">Parent</option>
                      <option value="sibling">Sibling</option>
                      <option value="child">Child</option>
                      <option value="friend">Friend</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
              )}

              {/* Step 4: Travel Preferences */}
              {step === 4 && (
                <div className="space-y-5">
                  <div>
                    <label htmlFor="preferred_coverage_type" className="block text-sm font-semibold text-black mb-2">
                      Preferred coverage type *
                    </label>
                    <select
                      id="preferred_coverage_type"
                      name="preferred_coverage_type"
                      required
                      value={formData.preferred_coverage_type}
                      onChange={handleInputChange}
                      className="block w-full px-4 py-3 border border-gray-300 rounded-lg text-black focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition-colors"
                    >
                      <option value="basic">Basic coverage</option>
                      <option value="comprehensive">Comprehensive coverage</option>
                      <option value="adventure">Adventure sports coverage</option>
                    </select>
                  </div>

                  <div className="flex items-start py-3">
                    <input
                      id="is_frequent_traveler"
                      name="is_frequent_traveler"
                      type="checkbox"
                      checked={formData.is_frequent_traveler}
                      onChange={handleInputChange}
                      className="h-5 w-5 text-black border-gray-300 rounded focus:ring-black focus:ring-1 mt-0.5"
                    />
                    <label htmlFor="is_frequent_traveler" className="ml-3 block text-sm text-black">
                      I am a frequent traveler (3+ trips per year)
                    </label>
                  </div>

                  <div className="flex items-start py-3">
                    <input
                      id="has_pre_existing_conditions"
                      name="has_pre_existing_conditions"
                      type="checkbox"
                      checked={formData.has_pre_existing_conditions}
                      onChange={handleInputChange}
                      className="h-5 w-5 text-black border-gray-300 rounded focus:ring-black focus:ring-1 mt-0.5"
                    />
                    <label htmlFor="has_pre_existing_conditions" className="ml-3 block text-sm text-black">
                      I have pre-existing medical conditions
                    </label>
                  </div>
                </div>
              )}

              {/* Navigation Buttons */}
              <div className="flex justify-between pt-6 border-t border-gray-200 mt-8">
                {step > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={handlePrevious}
                    className="text-gray-600 hover:text-black hover:bg-gray-100 font-medium"
                  >
                    ← Previous
                  </Button>
                )}

                {step < totalSteps ? (
                  <Button
                    type="button"
                    onClick={handleNext}
                    className="ml-auto bg-black hover:bg-gray-800 text-white font-medium rounded-full px-6"
                  >
                    Continue
                  </Button>
                ) : (
                  <Button
                    type="submit"
                    disabled={loading}
                    className="ml-auto bg-black hover:bg-gray-800 text-white font-medium rounded-full px-6"
                  >
                    {loading ? 'Submitting...' : 'Complete setup'}
                  </Button>
                )}
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
    </ProtectedRoute>
  )
}
