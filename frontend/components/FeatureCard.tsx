'use client'

import { ReactNode } from 'react'
import { motion } from 'framer-motion'
import { Search, Zap, Database, Bot, Globe, Shield } from 'lucide-react'

interface FeatureCardProps {
  iconType: string
  title: string
  description: string
  color: 'primary' | 'secondary' | 'accent'
}

const colorClasses = {
  primary: 'text-primary-600 bg-primary-50 border-primary-200',
  secondary: 'text-secondary-600 bg-secondary-50 border-secondary-200',
  accent: 'text-accent-600 bg-accent-50 border-accent-200'
}

const getIcon = (iconType: string) => {
  switch (iconType) {
    case 'Search':
      return <Search className="w-6 h-6" />
    case 'Bot':
      return <Bot className="w-6 h-6" />
    case 'Database':
      return <Database className="w-6 h-6" />
    case 'Zap':
      return <Zap className="w-6 h-6" />
    case 'Globe':
      return <Globe className="w-6 h-6" />
    case 'Shield':
      return <Shield className="w-6 h-6" />
    default:
      return <Search className="w-6 h-6" />
  }
}

export default function FeatureCard({ iconType, title, description, color }: FeatureCardProps) {
  return (
    <motion.div
      whileHover={{ y: -5 }}
      className="card group cursor-pointer"
    >
      <div className={`inline-flex p-3 rounded-lg border ${colorClasses[color]} mb-4 group-hover:scale-110 transition-transform duration-200`}>
        {getIcon(iconType)}
      </div>
      
      <h3 className="text-xl font-semibold text-secondary-900 mb-3">
        {title}
      </h3>
      
      <p className="text-secondary-600 leading-relaxed">
        {description}
      </p>
      
      <div className="mt-4 flex items-center text-sm font-medium text-primary-600 group-hover:text-primary-700 transition-colors">
        Learn more
        <svg className="ml-2 w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </motion.div>
  )
}
