'use client';

import React, { useState } from 'react';
import { Search, Book, Zap, Shield, Database, Code2, MessageSquare, LogIn } from 'lucide-react';
import GameOfLife from '@/components/GameOfLife';
import ThemeToggle from '@/components/ThemeToggle';
import ChatInterface from '@/components/ChatInterface';

export default function Home() {
  const [showChat, setShowChat] = useState(false);

  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'AI-Powered Search',
      description: 'Find API documentation instantly with semantic search'
    },
    {
      icon: <Book className="w-6 h-6" />,
      title: 'Multi-Provider',
      description: 'Atlassian, Datadog, Kubernetes, and more'
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: 'Real-Time Updates',
      description: 'Automatic documentation synchronization'
    },
    {
      icon: <Database className="w-6 h-6" />,
      title: 'Vector Search',
      description: 'Semantic understanding of your queries'
    }
  ];

  const providers = [
    { name: 'Atlassian', color: 'from-blue-500 to-blue-600', endpoints: '150+' },
    { name: 'Datadog', color: 'from-purple-500 to-purple-600', endpoints: '200+' },
    { name: 'Kubernetes', color: 'from-cyan-500 to-cyan-600', endpoints: '300+' },
    { name: 'GitHub', color: 'from-gray-700 to-gray-800', endpoints: '250+' }
  ];

  return (
    <main className="min-h-screen relative">
      {/* Conway's Game of Life Background */}
      <GameOfLife cellSize={25} speed={150} density={0.25} opacity={0.12} />

      {/* Theme Toggle */}
      <ThemeToggle />

      {/* Login Button */}
      <a
        href="/admin"
        className="fixed top-4 left-4 z-50 p-3 rounded-full bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200 dark:border-gray-700 group"
        title="Admin Login"
      >
        <LogIn className="w-5 h-5 text-indigo-600 dark:text-indigo-400 group-hover:scale-110 transition-transform" />
      </a>

      {/* Hero Section */}
      <div className="relative z-10 container mx-auto px-4 py-16">
        <div className="text-center mb-16 animate-fade-in">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-full mb-6">
            <Code2 className="w-4 h-4 text-indigo-600 dark:text-indigo-400" />
            <span className="text-sm font-medium text-indigo-600 dark:text-indigo-400">
              MCP-Based Documentation Platform
            </span>
          </div>

          <h1 className="text-5xl md:text-7xl font-bold mb-6 bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 dark:from-indigo-400 dark:via-purple-400 dark:to-pink-400 bg-clip-text text-transparent">
            API Documentation
            <br />
            Reimagined
          </h1>

          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8 max-w-2xl mx-auto">
            Discover, search, and explore API documentation with the power of AI.
            Built on Model Context Protocol for intelligent documentation assistance.
          </p>

          <div className="flex flex-wrap gap-4 justify-center">
            <button
              onClick={() => setShowChat(!showChat)}
              className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl font-semibold shadow-xl hover:shadow-2xl transition-all duration-200 flex items-center gap-2"
            >
              <MessageSquare className="w-5 h-5" />
              {showChat ? 'Hide' : 'Open'} AI Assistant
            </button>

            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="px-8 py-4 bg-white/90 dark:bg-gray-800/90 hover:bg-white dark:hover:bg-gray-800 text-gray-900 dark:text-gray-100 rounded-xl font-semibold shadow-xl hover:shadow-2xl transition-all duration-200 backdrop-blur-sm border border-gray-200 dark:border-gray-700"
            >
              API Docs
            </a>

            <a
              href="/admin"
              className="px-8 py-4 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white rounded-xl font-semibold shadow-xl hover:shadow-2xl transition-all duration-200"
            >
              Admin Panel
            </a>
          </div>
        </div>

        {/* Chat Interface - Fixed Position Dialog */}
        {showChat && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
            <div className="w-full max-w-4xl h-[600px] animate-scale-in">
              <ChatInterface onClose={() => setShowChat(false)} />
            </div>
          </div>
        )}

        {/* Features Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {features.map((feature, index) => (
            <div
              key={index}
              className="p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-xl transition-all duration-200 border border-gray-200 dark:border-gray-700 animate-slide-up"
              style={{ animationDelay: `${index * 100}ms` }}
            >
              <div className="w-12 h-12 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-xl flex items-center justify-center text-white mb-4">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold mb-2 text-gray-900 dark:text-gray-100">
                {feature.title}
              </h3>
              <p className="text-gray-600 dark:text-gray-400">
                {feature.description}
              </p>
            </div>
          ))}
        </div>

        {/* Providers Section */}
        <div className="mb-16">
          <h2 className="text-3xl font-bold text-center mb-8 text-gray-900 dark:text-gray-100">
            Supported API Providers
          </h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {providers.map((provider, index) => (
              <div
                key={index}
                className="group p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-lg hover:shadow-2xl transition-all duration-200 border border-gray-200 dark:border-gray-700 cursor-pointer"
              >
                <div className={`w-full h-32 bg-gradient-to-br ${provider.color} rounded-xl mb-4 flex items-center justify-center text-white text-2xl font-bold group-hover:scale-105 transition-transform`}>
                  {provider.name}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-900 dark:text-gray-100 font-semibold">
                    {provider.name}
                  </span>
                  <span className="text-sm text-gray-500 dark:text-gray-400">
                    {provider.endpoints}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto">
          {[
            { label: 'API Endpoints', value: '900+' },
            { label: 'Providers', value: '4+' },
            { label: 'AI Queries/day', value: '∞' }
          ].map((stat, index) => (
            <div
              key={index}
              className="p-8 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-xl text-center text-white"
            >
              <div className="text-4xl font-bold mb-2">{stat.value}</div>
              <div className="text-indigo-100">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Footer */}
      <footer className="relative z-10 border-t border-gray-200 dark:border-gray-700 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-gray-600 dark:text-gray-400">
            <p className="mb-2">
              Built with Next.js 14, FastAPI, and Model Context Protocol
            </p>
            <p className="text-sm">
              Powered by Conway's Game of Life • AI • Vector Search
            </p>
          </div>
        </div>
      </footer>
    </main>
  );
}
