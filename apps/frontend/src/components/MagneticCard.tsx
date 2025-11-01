'use client'

import { useRef, useEffect, ReactNode } from 'react'

interface MagneticCardProps {
  children: ReactNode
  className?: string
  strength?: number
  [key: string]: any
}

export function MagneticCard({ children, className = '', strength = 0.3, ...props }: MagneticCardProps) {
  const cardRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const card = cardRef.current
    if (!card) return

    const handleMouseMove = (e: MouseEvent) => {
      const rect = card.getBoundingClientRect()
      const x = e.clientX - rect.left - rect.width / 2
      const y = e.clientY - rect.top - rect.height / 2

      const moveX = x * strength
      const moveY = y * strength

      card.style.transform = `translate(${moveX}px, ${moveY}px)`
    }

    const handleMouseLeave = () => {
      card.style.transform = 'translate(0, 0)'
    }

    card.addEventListener('mousemove', handleMouseMove)
    card.addEventListener('mouseleave', handleMouseLeave)

    return () => {
      card.removeEventListener('mousemove', handleMouseMove)
      card.removeEventListener('mouseleave', handleMouseLeave)
    }
  }, [strength])

  return (
    <div
      ref={cardRef}
      className={`transition-transform duration-300 ease-out ${className}`}
      style={{ willChange: 'transform' }}
      {...props}
    >
      {children}
    </div>
  )
}

