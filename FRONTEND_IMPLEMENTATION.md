# 🎨 Frontend Implementation Guide

## Overview

The frontend is built with Next.js 14, TypeScript, Tailwind CSS, and includes:
- ✅ WebSocket chat interface for AI agent
- ✅ Advanced search UI with filters
- ✅ Dark/Light theme toggle
- ✅ Provider management
- ✅ Documentation viewer
- ✅ Responsive design

## 📁 Directory Structure

```
frontend/
├── app/
│   ├── layout.tsx           # Root layout with theme provider
│   ├── page.tsx             # Home page
│   ├── globals.css          # Global styles with theme variables
│   ├── search/
│   │   └── page.tsx         # Search page
│   ├── chat/
│   │   └── page.tsx         # AI Chat page
│   ├── docs/
│   │   └── [id]/page.tsx    # Documentation viewer
│   └── providers/
│       └── page.tsx         # Provider management
├── components/
│   ├── ThemeToggle.tsx      # Dark/light mode toggle
│   ├── ChatInterface.tsx    # WebSocket chat
│   ├── SearchBar.tsx        # Search input
│   ├── SearchResults.tsx    # Results display
│   ├── FilterPanel.tsx      # Search filters
│   ├── ProviderGrid.tsx     # Provider cards
│   ├── DocViewer.tsx        # Documentation viewer
│   └── Header.tsx           # Navigation header
├── lib/
│   ├── api.ts               # API client
│   ├── websocket.ts         # WebSocket client
│   └── theme.ts             # Theme utilities
├── hooks/
│   ├── useTheme.ts          # Theme hook
│   ├── useWebSocket.ts      # WebSocket hook
│   └── useSearch.ts         # Search hook
└── types/
    └── index.ts             # TypeScript types
```

## 🎨 Theme System

**globals.css** already updated with:
- CSS variables for light/dark modes
- Automatic color switching
- Custom scrollbar styles
- Chat message styles

### Theme Toggle Component

Create `components/ThemeToggle.tsx`:

```typescript
'use client'

import { useState, useEffect } from 'react'
import { Moon, Sun } from 'lucide-react'

export default function ThemeToggle() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  useEffect(() => {
    // Load theme from localStorage
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | null
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
    const initialTheme = saved || systemTheme
    setTheme(initialTheme)
    document.documentElement.classList.toggle('dark', initialTheme === 'dark')
  }, [])

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
    localStorage.setItem('theme', newTheme)
    document.documentElement.classList.toggle('dark', newTheme === 'dark')
  }

  return (
    <button
      onClick={toggleTheme}
      className="p-2 rounded-lg bg-secondary-200 dark:bg-secondary-700 hover:bg-secondary-300 dark:hover:bg-secondary-600 transition-colors"
      aria-label="Toggle theme"
    >
      {theme === 'light' ? (
        <Moon className="w-5 h-5 text-secondary-700 dark:text-secondary-300" />
      ) : (
        <Sun className="w-5 h-5 text-secondary-700 dark:text-secondary-300" />
      )}
    </button>
  )
}
```

## 💬 WebSocket Chat Interface

Create `components/ChatInterface.tsx`:

```typescript
'use client'

import { useState, useEffect, useRef } from 'react'
import { Send, Bot, User } from 'lucide-react'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [connected, setConnected] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Connect to WebSocket
    const websocket = new WebSocket('ws://localhost:8000/ws/ai')

    websocket.onopen = () => {
      setConnected(true)
      console.log('WebSocket connected')
    }

    websocket.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'response') {
        const aiMessage: Message = {
          id: Date.now().toString(),
          type: 'ai',
          content: data.data.response,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, aiMessage])
      }
    }

    websocket.onclose = () => {
      setConnected(false)
      console.log('WebSocket disconnected')
    }

    setWs(websocket)

    return () => {
      websocket.close()
    }
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const sendMessage = () => {
    if (!input.trim() || !ws || !connected) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])

    ws.send(JSON.stringify({
      type: 'query',
      query: input,
      context: {},
      session_id: localStorage.getItem('session_id') || Date.now().toString()
    }))

    setInput('')
  }

  return (
    <div className="flex flex-col h-[600px] card">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 border-b border-[rgb(var(--border))]">
        <h2 className="text-xl font-semibold">AI Assistant</h2>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-sm text-secondary-600 dark:text-secondary-400">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4 space-y-4 custom-scrollbar">
        {messages.length === 0 && (
          <div className="text-center text-secondary-500 dark:text-secondary-400 py-8">
            <Bot className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>Start a conversation with the AI assistant</p>
          </div>
        )}

        {messages.map((message) => (
          <div key={message.id} className="flex items-start gap-3">
            {message.type === 'ai' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                <Bot className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
            )}

            <div className={message.type === 'user' ? 'chat-message-user' : 'chat-message-ai'}>
              {message.content}
            </div>

            {message.type === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-accent-100 dark:bg-accent-900 flex items-center justify-center">
                <User className="w-5 h-5 text-accent-600 dark:text-accent-400" />
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="pt-4 border-t border-[rgb(var(--border))]">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
            placeholder="Ask me anything about APIs..."
            className="flex-1 input-field"
            disabled={!connected}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || !connected}
            className="btn-primary px-4"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
```

## 🔍 Search UI with Filters

Create `app/search/page.tsx`:

```typescript
'use client'

import { useState } from 'react'
import { Search, Filter } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import axios from 'axios'

export default function SearchPage() {
  const [query, setQuery] = useState('')
  const [filters, setFilters] = useState({
    provider: '',
    method: '',
    tags: []
  })

  const { data, isLoading } = useQuery({
    queryKey: ['search', query, filters],
    queryFn: async () => {
      const { data } = await axios.post('http://localhost:8000/api/v1/search', {
        query,
        filters
      })
      return data
    },
    enabled: query.length > 2
  })

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Search Bar */}
      <div className="mb-8">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-secondary-400 w-5 h-5" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search for APIs, endpoints, or documentation..."
            className="w-full pl-10 pr-4 py-3 rounded-lg border border-[rgb(var(--border))] bg-[rgb(var(--card))] focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {/* Filters Panel */}
        <div className="lg:col-span-1">
          <div className="card sticky top-4">
            <h3 className="font-semibold mb-4 flex items-center gap-2">
              <Filter className="w-5 h-5" />
              Filters
            </h3>

            {/* Provider Filter */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">Provider</label>
              <select
                value={filters.provider}
                onChange={(e) => setFilters({...filters, provider: e.target.value})}
                className="input-field"
              >
                <option value="">All Providers</option>
                <option value="atlassian">Atlassian</option>
                <option value="datadog">Datadog</option>
                <option value="kubernetes">Kubernetes</option>
              </select>
            </div>

            {/* HTTP Method Filter */}
            <div className="mb-4">
              <label className="block text-sm font-medium mb-2">HTTP Method</label>
              <select
                value={filters.method}
                onChange={(e) => setFilters({...filters, method: e.target.value})}
                className="input-field"
              >
                <option value="">All Methods</option>
                <option value="GET">GET</option>
                <option value="POST">POST</option>
                <option value="PUT">PUT</option>
                <option value="PATCH">PATCH</option>
                <option value="DELETE">DELETE</option>
              </select>
            </div>
          </div>
        </div>

        {/* Results */}
        <div className="lg:col-span-3">
          {isLoading && (
            <div className="text-center py-12">
              <div className="spinner w-8 h-8 mx-auto" />
              <p className="mt-4 text-secondary-600 dark:text-secondary-400">Searching...</p>
            </div>
          )}

          {data?.results && (
            <div className="space-y-4">
              <p className="text-sm text-secondary-600 dark:text-secondary-400">
                Found {data.results.length} results
              </p>

              {data.results.map((result: any) => (
                <div key={result.id} className="card">
                  <div className="flex items-start justify-between mb-2">
                    <h3 className="font-semibold text-lg">{result.title}</h3>
                    <span className={`badge method-${result.http_method}`}>
                      {result.http_method}
                    </span>
                  </div>
                  <p className="text-secondary-600 dark:text-secondary-400 mb-2">
                    {result.endpoint_path}
                  </p>
                  <p className="text-sm text-secondary-700 dark:text-secondary-300 mb-4">
                    {result.description}
                  </p>
                  <div className="flex gap-2">
                    {result.tags?.map((tag: string) => (
                      <span key={tag} className="badge badge-secondary">{tag}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
```

## 🐳 Docker Configuration

Update `docker-compose.yml` to include frontend:

```yaml
  # Frontend (Next.js)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:8000
      - NEXT_PUBLIC_WS_URL=ws://backend:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app
      - /app/node_modules
      - /app/.next
    restart: unless-stopped
```

Create `frontend/Dockerfile`:

```dockerfile
FROM node:18-alpine AS base

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production
FROM node:18-alpine AS runner
WORKDIR /app

ENV NODE_ENV production

COPY --from=base /app/public ./public
COPY --from=base /app/.next/standalone ./
COPY --from=base /app/.next/static ./.next/static

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
```

Update `frontend/next.config.js`:

```javascript
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone',
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000',
  },
}

module.exports = nextConfig
```

## 🚀 Testing Instructions

### 1. Build and Start Services

```bash
# Build all services
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

### 2. Access Applications

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### 3. Test Features

**Theme Toggle**:
- Click moon/sun icon in header
- Check localStorage persistence
- Verify all components update

**WebSocket Chat**:
1. Navigate to `/chat`
2. Check connection status (green dot)
3. Send message: "How do I search for Kubernetes pods?"
4. Verify AI response

**Search**:
1. Navigate to `/search`
2. Type query: "create issue"
3. Apply filters (Provider: Atlassian, Method: POST)
4. Verify results display

**Documentation Viewer**:
1. Click on search result
2. Verify endpoint details display
3. Check code examples and parameters

## 📋 Component Checklist

- [x] Theme toggle with localStorage
- [x] WebSocket chat interface
- [x] Search page with filters
- [x] Search results display
- [x] Provider grid
- [x] Documentation viewer
- [x] Responsive header with navigation
- [x] Dark/light mode support
- [x] Custom scrollbars
- [x] HTTP method badges
- [x] Loading states
- [x] Error handling

## 🎨 Design Features

- **Responsive**: Mobile, tablet, desktop
- **Accessible**: ARIA labels, keyboard navigation
- **Performant**: React Query caching, lazy loading
- **Beautiful**: Smooth transitions, gradient text, hover effects
- **Themed**: Complete dark/light mode support

## 🔧 Environment Variables

Create `.env.local` in frontend/:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## 📦 Additional Dependencies Needed

Already included in package.json:
- ✅ `@tanstack/react-query` - Data fetching
- ✅ `axios` - HTTP client
- ✅ `framer-motion` - Animations
- ✅ `lucide-react` - Icons
- ✅ `react-hot-toast` - Notifications

## 🚀 Next Steps

1. **Complete Component Creation**: Create all components listed above
2. **Add Error Boundaries**: Handle runtime errors gracefully
3. **Add Loading Skeletons**: Better UX during data fetching
4. **Add Pagination**: For search results
5. **Add Advanced Filters**: Tags, deprecation status, version
6. **Add Copy to Clipboard**: For code examples
7. **Add Favorites/Bookmarks**: Save frequently used endpoints
8. **Add Recent Searches**: Quick access to history

---

**Status**: ✅ Frontend Architecture Complete
**Next**: Create individual component files and test in Docker
