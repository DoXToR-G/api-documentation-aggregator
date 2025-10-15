'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Database,
  Settings,
  LogOut,
  Plus,
  BookOpen,
  Check,
  X as XIcon
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
  const [docSources, setDocSources] = useState<DocumentationSource[]>([
    {
      id: 'atlassian',
      name: 'Atlassian/Jira',
      description: 'Jira Cloud REST API v3 documentation',
      enabled: true,
      icon_color: 'from-blue-500 to-blue-600'
    },
    {
      id: 'kubernetes',
      name: 'Kubernetes',
      description: 'Kubernetes API documentation',
      enabled: true,
      icon_color: 'from-cyan-500 to-cyan-600'
    }
  ]);
  const [showAddSource, setShowAddSource] = useState(false);
  const [newSourceName, setNewSourceName] = useState('');
  const [newSourceDescription, setNewSourceDescription] = useState('');

  useEffect(() => {
    // Check authentication
    const isLoggedIn = localStorage.getItem('adminLoggedIn');
    if (isLoggedIn !== 'true') {
      router.push('/admin');
      return;
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem('adminLoggedIn');
    router.push('/admin');
  };

  const toggleSourceEnabled = (sourceId: string) => {
    setDocSources(prev =>
      prev.map(source =>
        source.id === sourceId
          ? { ...source, enabled: !source.enabled }
          : source
      )
    );
  };

  const handleAddSource = () => {
    if (!newSourceName.trim()) return;

    const newSource: DocumentationSource = {
      id: newSourceName.toLowerCase().replace(/\s+/g, '-'),
      name: newSourceName,
      description: newSourceDescription || `${newSourceName} API documentation`,
      enabled: true,
      icon_color: 'from-purple-500 to-purple-600'
    };

    setDocSources(prev => [...prev, newSource]);
    setNewSourceName('');
    setNewSourceDescription('');
    setShowAddSource(false);
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
                Manage AI-accessible API documentation sources
              </p>
            </div>
            <button
              onClick={() => setShowAddSource(!showAddSource)}
              className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl transition-all flex items-center gap-2 font-semibold shadow-lg"
            >
              <Plus className="w-5 h-5" />
              Add Source
            </button>
          </div>

          {/* Add Source Form */}
          {showAddSource && (
            <div className="mb-6 p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-4">
                Add New Documentation Source
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Source Name
                  </label>
                  <input
                    type="text"
                    value={newSourceName}
                    onChange={(e) => setNewSourceName(e.target.value)}
                    placeholder="e.g., Grafana, Prometheus, etc."
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Description
                  </label>
                  <input
                    type="text"
                    value={newSourceDescription}
                    onChange={(e) => setNewSourceDescription(e.target.value)}
                    placeholder="Brief description of the API"
                    className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleAddSource}
                    disabled={!newSourceName.trim()}
                    className="flex-1 px-4 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all font-semibold"
                  >
                    Add Source
                  </button>
                  <button
                    onClick={() => {
                      setShowAddSource(false);
                      setNewSourceName('');
                      setNewSourceDescription('');
                    }}
                    className="px-4 py-3 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 rounded-xl transition-all font-semibold"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          )}

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
              • <strong>No Storage:</strong> No need to sync or store API endpoints - the AI searches documentation directly
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
