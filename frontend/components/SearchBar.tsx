'use client'

import { useState } from 'react'
import { Search, X } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface SearchBarProps {
  value: string
  onChange: (value: string) => void
  placeholder?: string
  className?: string
  onSearch?: (query: string) => void
}

export default function SearchBar({ 
  value, 
  onChange, 
  placeholder = "Search...", 
  className = "",
  onSearch 
}: SearchBarProps) {
  const [isFocused, setIsFocused] = useState(false)
  const [suggestions, setSuggestions] = useState<string[]>([])

  const handleSearch = () => {
    if (value.trim() && onSearch) {
      onSearch(value.trim())
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch()
    }
  }

  const clearSearch = () => {
    onChange('')
    setSuggestions([])
  }

  return (
    <div className={`relative ${className}`}>
      <div className="relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search className="h-5 w-5 text-secondary-400" />
        </div>
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setIsFocused(true)}
          onBlur={() => setTimeout(() => setIsFocused(false), 200)}
          onKeyPress={handleKeyPress}
          placeholder={placeholder}
          className="input-field pl-10 pr-10 text-lg"
        />
        {value && (
          <button
            onClick={clearSearch}
            className="absolute inset-y-0 right-0 pr-3 flex items-center"
          >
            <X className="h-5 w-5 text-secondary-400 hover:text-secondary-600 transition-colors" />
          </button>
        )}
      </div>

      {/* Search Suggestions */}
      <AnimatePresence>
        {isFocused && suggestions.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="absolute z-10 w-full mt-2 bg-white rounded-lg shadow-lg border border-secondary-200 max-h-60 overflow-y-auto"
          >
            {suggestions.map((suggestion, index) => (
              <button
                key={index}
                onClick={() => {
                  onChange(suggestion)
                  setSuggestions([])
                }}
                className="w-full text-left px-4 py-3 hover:bg-secondary-50 transition-colors border-b border-secondary-100 last:border-b-0"
              >
                <div className="flex items-center">
                  <Search className="h-4 w-4 text-secondary-400 mr-3" />
                  <span className="text-secondary-700">{suggestion}</span>
                </div>
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Search Button */}
      <button
        onClick={handleSearch}
        disabled={!value.trim()}
        className="absolute right-2 top-1/2 transform -translate-y-1/2 btn-primary py-1 px-3 text-sm disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Search
      </button>
    </div>
  )
}
