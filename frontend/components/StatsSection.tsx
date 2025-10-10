'use client'

import { motion } from 'framer-motion'
import { Users, Search, Database, Zap } from 'lucide-react'

const stats = [
  {
    iconType: 'Users',
    value: '10K+',
    label: 'Active Developers',
    color: 'text-primary-600'
  },
  {
    iconType: 'Search',
    value: '1M+',
    label: 'API Searches',
    color: 'text-accent-600'
  },
  {
    iconType: 'Database',
    value: '50+',
    label: 'API Providers',
    color: 'text-secondary-600'
  },
  {
    iconType: 'Zap',
    value: '99.9%',
    label: 'Uptime',
    color: 'text-primary-600'
  }
]

const getIcon = (iconType: string) => {
  switch (iconType) {
    case 'Users':
      return <Users className="w-8 h-8" />
    case 'Search':
      return <Search className="w-8 h-8" />
    case 'Database':
      return <Database className="w-8 h-8" />
    case 'Zap':
      return <Zap className="w-8 h-8" />
    default:
      return <Users className="w-8 h-8" />
  }
}

export default function StatsSection() {
  return (
    <section className="py-16 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-8">
          {stats.map((stat, index) => (
            <motion.div
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="text-center"
            >
              <div className={`inline-flex p-4 rounded-full bg-secondary-100 mb-4 ${stat.color}`}>
                {getIcon(stat.iconType)}
              </div>
              <div className="text-3xl font-bold text-secondary-900 mb-2">
                {stat.value}
              </div>
              <div className="text-secondary-600">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  )
}
