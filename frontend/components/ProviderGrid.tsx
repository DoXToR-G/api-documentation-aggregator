'use client'

import { motion } from 'framer-motion'
import { ExternalLink } from 'lucide-react'

const providers = [
  {
    name: 'Datadog',
    description: 'Monitoring and observability platform',
    icon: '🐕',
    color: 'from-orange-400 to-red-500',
    url: 'https://docs.datadoghq.com/api/latest/'
  },
  {
    name: 'Jira Cloud',
    description: 'Issue tracking and project management',
    icon: '📋',
    color: 'from-blue-400 to-blue-600',
    url: 'https://developer.atlassian.com/cloud/jira/platform/rest/v3/'
  },
  {
    name: 'Kubernetes',
    description: 'Container orchestration platform',
    icon: '☸️',
    color: 'from-blue-500 to-blue-700',
    url: 'https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.28/'
  },
  {
    name: 'Prometheus',
    description: 'Open-source monitoring system',
    icon: '🔥',
    color: 'from-orange-500 to-red-600',
    url: 'https://prometheus.io/docs/prometheus/latest/querying/api/'
  },
  {
    name: 'Grafana',
    description: 'Observability platform',
    icon: '📊',
    color: 'from-orange-400 to-red-500',
    url: 'https://grafana.com/docs/grafana/latest/developers/http_api/'
  },
  {
    name: 'Kibana',
    description: 'Data visualization platform',
    icon: '🔍',
    color: 'from-blue-500 to-purple-600',
    url: 'https://www.elastic.co/guide/en/kibana/current/api.html'
  }
]

export default function ProviderGrid() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {providers.map((provider, index) => (
        <motion.div
          key={provider.name}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: index * 0.1 }}
          whileHover={{ y: -5 }}
          className="card group cursor-pointer"
        >
          <div className="flex items-start justify-between mb-4">
            <div className={`text-4xl ${provider.icon}`} />
            <div className="opacity-0 group-hover:opacity-100 transition-opacity">
              <ExternalLink className="w-5 h-5 text-secondary-400" />
            </div>
          </div>
          
          <h3 className="text-xl font-semibold text-secondary-900 mb-2">
            {provider.name}
          </h3>
          
          <p className="text-secondary-600 text-sm mb-4">
            {provider.description}
          </p>
          
          <div className={`w-full h-1 bg-gradient-to-r ${provider.color} rounded-full`} />
          
          <a
            href={provider.url}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center text-sm font-medium text-primary-600 hover:text-primary-700 transition-colors"
          >
            View Documentation
            <ExternalLink className="ml-1 w-4 h-4" />
          </a>
        </motion.div>
      ))}
    </div>
  )
}
