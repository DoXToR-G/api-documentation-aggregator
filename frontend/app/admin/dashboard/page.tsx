'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Database,
  Settings,
  LogOut,
  BookOpen,
  Check,
  X as XIcon,
  FileText
} from 'lucide-react';
import axios from 'axios';
import GameOfLife from '@/components/GameOfLife';
import ThemeToggle from '@/components/ThemeToggle';
import AIConfigPanel from '@/components/AIConfigPanel';
import AIStatusPanel from '@/components/AIStatusPanel';

interface DocumentationSource {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  icon_color: string;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [showSettings, setShowSettings] = useState(false);
  const [docSources, setDocSources] = useState<DocumentationSource[]>([]);
  const [isLoadingSources, setIsLoadingSources] = useState(true);

  useEffect(() => {
    // Check authentication
    const isLoggedIn = localStorage.getItem('adminLoggedIn');
    if (isLoggedIn !== 'true') {
      router.push('/admin');
      return;
    }

    // Load documentation sources from backend
    loadDocumentationSources();
  }, [router]);

  const loadDocumentationSources = async () => {
    setIsLoadingSources(true);
    try {
      const response = await axios.get('http://localhost:8000/api/v1/doc-sources');
      const sources = response.data.map((source: any) => ({
        id: source.id.toString(),
        name: source.display_name,
        description: source.description,
        enabled: source.is_active,
        icon_color: source.icon_color || getIconColor(source.name)
      }));
      setDocSources(sources);
    } catch (error) {
      console.error('Failed to load documentation sources:', error);
    } finally {
      setIsLoadingSources(false);
    }
  };

  const getIconColor = (name: string): string => {
    const colors = [
      'from-blue-500 to-blue-600',
      'from-cyan-500 to-cyan-600',
      'from-purple-500 to-purple-600',
      'from-green-500 to-green-600',
      'from-orange-500 to-orange-600',
      'from-pink-500 to-pink-600'
    ];
    const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
  };

  const handleLogout = () => {
    localStorage.removeItem('adminLoggedIn');
    window.location.href = 'http://localhost:3000/';  // Redirect to main page
  };

  const toggleSourceEnabled = async (sourceId: string) => {
    try {
      await axios.patch(`http://localhost:8000/api/v1/doc-sources/${sourceId}/toggle`);
      // Refresh sources
      await loadDocumentationSources();
    } catch (error) {
      console.error('Failed to toggle source:', error);
      alert('Failed to toggle source. Please try again.');
    }
  };


  return (
    <div className="min-h-screen relative">
      {/* Background */}
      <GameOfLife cellSize={25} speed={150} density={0.25} opacity={0.08} />

      {/* Theme Toggle */}
      <ThemeToggle />

      {/* Header */}
      <div className="relative z-10 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border-b border-gray-200 dark:border-gray-700">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Database className="w-8 h-8 text-indigo-600" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                  Admin Dashboard
                </h1>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  AI-Powered Documentation Management
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => router.push('/admin/logs')}
                className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-xl transition-all flex items-center gap-2"
                title="View System Logs"
              >
                <FileText className="w-4 h-4" />
                Logs
              </button>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-xl transition-all flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                AI Settings
              </button>
              <button
                onClick={handleLogout}
                className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-xl transition-all flex items-center gap-2"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* AI Settings Modal */}
        {showSettings && (
          <div className="mb-6 grid md:grid-cols-2 gap-6">
            <AIConfigPanel onSaveSuccess={() => {}} />
            <div>
              <AIStatusPanel />
            </div>
          </div>
        )}

        {/* AI Status Panel - Always Visible */}
        {!showSettings && (
          <div className="mb-6">
            <AIStatusPanel />
          </div>
        )}

        {/* Documentation Sources Section */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 flex items-center gap-3">
                <BookOpen className="w-7 h-7 text-indigo-600" />
                Documentation Sources
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                AI-accessible API documentation sources (use "load_openapi" for dynamic loading)
              </p>
            </div>
          </div>

          {/* Documentation Sources Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {docSources.map((source) => (
              <div
                key={source.id}
                className="p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700 hover:shadow-xl transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className={`w-12 h-12 bg-gradient-to-br ${source.icon_color} rounded-xl flex items-center justify-center text-white font-bold text-xl`}>
                    {source.name.charAt(0)}
                  </div>
                  <button
                    onClick={() => toggleSourceEnabled(source.id)}
                    className={`p-2 rounded-lg transition-all ${
                      source.enabled
                        ? 'bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400'
                        : 'bg-gray-100 dark:bg-gray-700 text-gray-400'
                    }`}
                    title={source.enabled ? 'Enabled' : 'Disabled'}
                  >
                    {source.enabled ? (
                      <Check className="w-5 h-5" />
                    ) : (
                      <XIcon className="w-5 h-5" />
                    )}
                  </button>
                </div>

                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {source.name}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  {source.description}
                </p>

                <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium ${
                  source.enabled
                    ? 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                    : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400'
                }`}>
                  {source.enabled ? (
                    <>
                      <Check className="w-3 h-3" />
                      ACTIVE
                    </>
                  ) : (
                    <>
                      <XIcon className="w-3 h-3" />
                      INACTIVE
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Info Section */}
        <div className="mt-8 p-6 bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-2xl border border-indigo-200 dark:border-indigo-800">
          <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-3">
            How It Works
          </h3>
          <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
            <p>
              • <strong>AI-Powered:</strong> Documentation is accessed on-demand by the AI agent using MCP (Model Context Protocol)
            </p>
            <p>
              • <strong>Dynamic Loading:</strong> Use "load_openapi" to bring any OpenAPI spec URL at chat time - no database persistence needed
            </p>
            <p>
              • <strong>Database Sources:</strong> Pre-configured sources above are persisted in the database for frequent use
            </p>
            <p>
              • <strong>Real-Time:</strong> Always up-to-date information from official documentation sources
            </p>
            <p>
              • <strong>Intelligent:</strong> AI understands context and provides relevant answers with code examples
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
