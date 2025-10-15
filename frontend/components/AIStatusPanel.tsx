'use client';

import React, { useState, useEffect } from 'react';
import {
  Activity,
  CheckCircle,
  XCircle,
  Loader2,
  Brain,
  Database,
  MessageSquare,
  TrendingUp,
  RefreshCw
} from 'lucide-react';
import axios from 'axios';

interface AIStatus {
  agent_id: string;
  openai_configured: boolean;
  mcp_connected: boolean;
  total_sessions: number;
  total_messages: number;
  uptime: string;
  model: string;
}

export default function AIStatusPanel() {
  const [status, setStatus] = useState<AIStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    loadStatus();
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadStatus, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadStatus = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await axios.get('http://localhost:8000/ai/status');
      setStatus(response.data);
      setLastUpdate(new Date());
    } catch (err: any) {
      console.error('Failed to load AI status:', err);
      setError(err.message || 'Failed to load AI status');
    } finally {
      setIsLoading(false);
    }
  };

  const formatUptime = (uptime: string) => {
    try {
      const date = new Date(uptime);
      const now = new Date();
      const diff = now.getTime() - date.getTime();

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    } catch {
      return 'N/A';
    }
  };

  if (isLoading && !status) {
    return (
      <div className="p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-center gap-3 py-8">
          <Loader2 className="w-6 h-6 text-indigo-600 animate-spin" />
          <span className="text-gray-600 dark:text-gray-400">Loading AI status...</span>
        </div>
      </div>
    );
  }

  if (error && !status) {
    return (
      <div className="p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-xl border border-red-300 dark:border-red-700">
        <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
          <XCircle className="w-6 h-6" />
          <span>{error}</span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold flex items-center gap-3 text-gray-900 dark:text-gray-100">
          <Activity className="w-7 h-7 text-indigo-600" />
          AI Agent Status
        </h2>
        <button
          onClick={loadStatus}
          disabled={isLoading}
          className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-all"
          title="Refresh status"
        >
          <RefreshCw className={`w-5 h-5 text-gray-600 dark:text-gray-400 ${isLoading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {status && (
        <div className="space-y-4">
          {/* Connection Status Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* OpenAI Status */}
            <div className={`p-4 rounded-xl border-2 ${
              status.openai_configured
                ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                : 'border-red-500 bg-red-50 dark:bg-red-900/20'
            }`}>
              <div className="flex items-center gap-3">
                {status.openai_configured ? (
                  <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                )}
                <div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                    OpenAI API
                  </div>
                  <div className={`text-sm ${
                    status.openai_configured
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {status.openai_configured ? 'Connected' : 'Not Configured'}
                  </div>
                </div>
              </div>
            </div>

            {/* MCP Status */}
            <div className={`p-4 rounded-xl border-2 ${
              status.mcp_connected
                ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
                : 'border-red-500 bg-red-50 dark:bg-red-900/20'
            }`}>
              <div className="flex items-center gap-3">
                {status.mcp_connected ? (
                  <CheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                ) : (
                  <XCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                )}
                <div>
                  <div className="font-semibold text-gray-900 dark:text-gray-100">
                    MCP Protocol
                  </div>
                  <div className={`text-sm ${
                    status.mcp_connected
                      ? 'text-green-600 dark:text-green-400'
                      : 'text-red-600 dark:text-red-400'
                  }`}>
                    {status.mcp_connected ? 'Connected' : 'Disconnected'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Statistics Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {/* Active Sessions */}
            <div className="p-4 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl text-white">
              <div className="flex items-center gap-2 mb-2">
                <Brain className="w-5 h-5 opacity-80" />
                <span className="text-sm opacity-90">Sessions</span>
              </div>
              <div className="text-2xl font-bold">{status.total_sessions}</div>
            </div>

            {/* Total Messages */}
            <div className="p-4 bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl text-white">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare className="w-5 h-5 opacity-80" />
                <span className="text-sm opacity-90">Messages</span>
              </div>
              <div className="text-2xl font-bold">{status.total_messages}</div>
            </div>

            {/* Uptime */}
            <div className="p-4 bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl text-white">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-5 h-5 opacity-80" />
                <span className="text-sm opacity-90">Uptime</span>
              </div>
              <div className="text-2xl font-bold">{formatUptime(status.uptime)}</div>
            </div>

            {/* Model */}
            <div className="p-4 bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl text-white">
              <div className="flex items-center gap-2 mb-2">
                <Database className="w-5 h-5 opacity-80" />
                <span className="text-sm opacity-90">Model</span>
              </div>
              <div className="text-sm font-semibold truncate" title={status.model}>
                {status.model || 'N/A'}
              </div>
            </div>
          </div>

          {/* Agent Details */}
          <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
              <div>
                <span className="text-gray-600 dark:text-gray-400">Agent ID:</span>
                <span className="ml-2 font-mono text-gray-900 dark:text-gray-100 text-xs">
                  {status.agent_id}
                </span>
              </div>
              <div>
                <span className="text-gray-600 dark:text-gray-400">Last Update:</span>
                <span className="ml-2 text-gray-900 dark:text-gray-100">
                  {lastUpdate.toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>

          {/* Overall Status Indicator */}
          <div className={`mt-4 p-4 rounded-xl border-2 flex items-center gap-3 ${
            status.openai_configured && status.mcp_connected
              ? 'border-green-500 bg-green-50 dark:bg-green-900/20'
              : 'border-yellow-500 bg-yellow-50 dark:bg-yellow-900/20'
          }`}>
            <div className={`w-3 h-3 rounded-full ${
              status.openai_configured && status.mcp_connected
                ? 'bg-green-500 animate-pulse'
                : 'bg-yellow-500'
            }`} />
            <div>
              <div className="font-semibold text-gray-900 dark:text-gray-100">
                {status.openai_configured && status.mcp_connected
                  ? 'AI Agent is fully operational'
                  : 'AI Agent requires configuration'}
              </div>
              {(!status.openai_configured || !status.mcp_connected) && (
                <div className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  Please configure OpenAI API key in settings to enable AI features
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
