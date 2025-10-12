'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  RefreshCw,
  Database,
  CheckCircle,
  XCircle,
  Clock,
  Settings,
  LogOut,
  Play,
  Loader2,
  Key,
  Save,
  Terminal,
  X
} from 'lucide-react';
import axios from 'axios';
import GameOfLife from '@/components/GameOfLife';
import ThemeToggle from '@/components/ThemeToggle';

interface Provider {
  id: number;
  name: string;
  base_url: string;
  is_active: boolean;
  last_sync?: string;
  total_endpoints?: number;
}

interface SyncStatus {
  provider: string;
  status: 'synced' | 'syncing' | 'failed' | 'never';
  last_sync?: string;
  endpoints_count?: number;
  error?: string;
}

interface LogEntry {
  timestamp: string;
  level: 'info' | 'success' | 'error' | 'warning';
  message: string;
}

export default function AdminDashboard() {
  const router = useRouter();
  const [providers, setProviders] = useState<Provider[]>([]);
  const [syncStatuses, setSyncStatuses] = useState<Record<string, SyncStatus>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSyncing, setIsSyncing] = useState(false);
  const [openAIKey, setOpenAIKey] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [showLogs, setShowLogs] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const logsEndRef = React.useRef<HTMLDivElement>(null);

  // Auto-scroll logs to bottom
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const addLog = (level: 'info' | 'success' | 'error' | 'warning', message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs(prev => [...prev, { timestamp, level, message }]);
  };

  const clearLogs = () => {
    setLogs([]);
  };

  useEffect(() => {
    // Check authentication
    const isLoggedIn = localStorage.getItem('adminLoggedIn');
    if (isLoggedIn !== 'true') {
      router.push('/admin');
      return;
    }

    // Load OpenAI key from localStorage
    const savedKey = localStorage.getItem('openai_api_key');
    if (savedKey) {
      setOpenAIKey(savedKey);
    }

    loadProviders();
    loadSyncStatus();
  }, [router]);

  const loadProviders = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/providers/');
      console.log('Providers response:', response.data);
      setProviders(response.data);
    } catch (error) {
      console.error('Failed to load providers:', error);
    }
  };

  const loadSyncStatus = async () => {
    setIsLoading(true);
    try {
      // Use the new stats endpoint which gives us actual database counts
      const response = await axios.get('http://localhost:8000/api/v1/providers/stats');
      const data = response.data;

      console.log('Provider stats response:', data);

      // Initialize with default values
      const statuses: Record<string, SyncStatus> = {};

      // Process provider stats
      if (data?.providers && Array.isArray(data.providers)) {
        console.log('Processing', data.providers.length, 'providers');

        data.providers.forEach((provider: any) => {
          console.log('Processing provider:', provider.display_name, provider.endpoint_count);

          const displayName = provider.display_name;

          statuses[displayName] = {
            provider: displayName,
            status: provider.endpoint_count > 0 ? 'synced' :
                   provider.last_sync_status === 'failed' ? 'failed' :
                   provider.last_sync_status === 'running' ? 'syncing' : 'never',
            last_sync: provider.last_sync_time || provider.last_successful_sync,
            endpoints_count: provider.endpoint_count || 0,
            error: undefined
          };
        });
      }

      console.log('Final statuses:', statuses);
      setSyncStatuses(statuses);
    } catch (error: any) {
      console.error('Failed to load sync status:', error);
      addLog('error', `Failed to load stats: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSyncAll = async () => {
    setIsSyncing(true);
    setShowLogs(true);
    clearLogs();

    try {
      addLog('info', '🔄 Starting sync for all providers...');

      // Use use_celery=false to run sync immediately instead of queuing in Celery
      const response = await axios.post('http://localhost:8000/api/v1/fetcher/sync/all?use_celery=false');

      addLog('info', `✓ Sync request sent: ${response.data.status}`);
      addLog('info', '⏳ Fetching documentation from APIs...');

      // Poll for updates
      const pollInterval = setInterval(async () => {
        try {
          const statsResponse = await axios.get('http://localhost:8000/api/v1/providers/stats');
          const providers = statsResponse.data.providers || [];

          providers.forEach((provider: any) => {
            if (provider.endpoint_count > 0) {
              addLog('success', `✓ ${provider.display_name}: ${provider.endpoint_count} endpoints`);
            }
          });
        } catch (error) {
          console.error('Poll error:', error);
        }
      }, 1000);

      setTimeout(async () => {
        clearInterval(pollInterval);
        await loadSyncStatus();
        addLog('success', '✅ Sync completed! Refreshing dashboard...');
        setIsSyncing(false);
      }, 5000);
    } catch (error: any) {
      console.error('Sync failed:', error);
      addLog('error', `❌ Sync failed: ${error.message || 'Unknown error'}`);
      setIsSyncing(false);
    }
  };

  const handleSyncProvider = async (providerName: string) => {
    setShowLogs(true);
    clearLogs();

    try {
      addLog('info', `🔄 Starting sync for ${providerName}...`);
      addLog('info', '⏳ Connecting to API...');

      // Use use_celery=false to run sync immediately instead of queuing in Celery
      const response = await axios.post(`http://localhost:8000/api/v1/fetcher/sync/provider/${providerName.toLowerCase()}?use_celery=false`);

      addLog('info', `✓ Sync request sent: ${response.data.status}`);
      addLog('info', '⏳ Fetching documentation...');

      setTimeout(async () => {
        await loadSyncStatus();
        const statsResponse = await axios.get('http://localhost:8000/api/v1/providers/stats');
        const provider = statsResponse.data.providers?.find((p: any) => p.name === providerName.toLowerCase());

        if (provider) {
          addLog('success', `✅ Sync completed: ${provider.endpoint_count} endpoints fetched`);
        } else {
          addLog('warning', '⚠️ Sync completed but no data found');
        }
      }, 3000);
    } catch (error: any) {
      console.error(`Sync failed for ${providerName}:`, error);
      addLog('error', `❌ Sync failed: ${error.message || 'Unknown error'}`);
    }
  };

  const handleSaveSettings = () => {
    localStorage.setItem('openai_api_key', openAIKey);
    setSaveMessage('Settings saved successfully!');
    setTimeout(() => setSaveMessage(''), 3000);
  };

  const handleLogout = () => {
    localStorage.removeItem('adminLoggedIn');
    router.push('/admin');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'synced':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'syncing':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'synced':
        return 'bg-green-100 dark:bg-green-900/20 text-green-700 dark:text-green-400';
      case 'failed':
        return 'bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-400';
      case 'syncing':
        return 'bg-blue-100 dark:bg-blue-900/20 text-blue-700 dark:text-blue-400';
      default:
        return 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-400';
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
                  API Documentation Management
                </p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-xl transition-all flex items-center gap-2"
              >
                <Settings className="w-4 h-4" />
                Settings
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
        {/* Settings Panel */}
        {showSettings && (
          <div className="mb-6 p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900 dark:text-gray-100">
              <Key className="w-5 h-5" />
              OpenAI API Configuration
            </h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  OpenAI API Key
                </label>
                <input
                  type="password"
                  value={openAIKey}
                  onChange={(e) => setOpenAIKey(e.target.value)}
                  placeholder="sk-..."
                  className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
                <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                  Enter your OpenAI API key to enable AI-powered features
                </p>
              </div>

              {saveMessage && (
                <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl text-green-700 dark:text-green-400 text-sm">
                  {saveMessage}
                </div>
              )}

              <button
                onClick={handleSaveSettings}
                className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl transition-all flex items-center gap-2"
              >
                <Save className="w-4 h-4" />
                Save Settings
              </button>
            </div>
          </div>
        )}

        {/* Logs Window */}
        {showLogs && (
          <div className="mb-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/50">
              <div className="flex items-center gap-2">
                <Terminal className="w-5 h-5 text-indigo-600" />
                <h2 className="text-lg font-bold text-gray-900 dark:text-gray-100">
                  Sync Logs
                </h2>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={clearLogs}
                  className="px-3 py-1 text-sm bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 rounded-lg transition-all"
                >
                  Clear
                </button>
                <button
                  onClick={() => setShowLogs(false)}
                  className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg transition-all"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>
            <div className="p-4 bg-gray-900 dark:bg-black font-mono text-sm max-h-96 overflow-y-auto">
              {logs.length === 0 ? (
                <div className="text-gray-500 italic">No logs yet. Start a sync operation to see logs.</div>
              ) : (
                logs.map((log, index) => (
                  <div
                    key={index}
                    className={`py-1 ${
                      log.level === 'success' ? 'text-green-400' :
                      log.level === 'error' ? 'text-red-400' :
                      log.level === 'warning' ? 'text-yellow-400' :
                      'text-gray-300'
                    }`}
                  >
                    <span className="text-gray-500">[{log.timestamp}]</span>{' '}
                    <span>{log.message}</span>
                  </div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </div>
        )}

        {/* Sync All Button and View Logs */}
        <div className="mb-6 flex items-center gap-4">
          <button
            onClick={handleSyncAll}
            disabled={isSyncing}
            className="px-8 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold rounded-xl shadow-xl hover:shadow-2xl transition-all duration-200 flex items-center gap-3"
          >
            {isSyncing ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Syncing All Providers...
              </>
            ) : (
              <>
                <RefreshCw className="w-5 h-5" />
                Sync All Providers
              </>
            )}
          </button>
          {logs.length > 0 && !showLogs && (
            <button
              onClick={() => setShowLogs(true)}
              className="px-6 py-4 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-gray-100 font-semibold rounded-xl shadow-lg hover:shadow-xl transition-all duration-200 flex items-center gap-2"
            >
              <Terminal className="w-5 h-5" />
              View Logs ({logs.length})
            </button>
          )}
        </div>

        {/* Provider Status Cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.values(syncStatuses).map((status) => (
            <div
              key={status.provider}
              className="p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-lg border border-gray-200 dark:border-gray-700"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {status.provider}
                  </h3>
                  <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium mt-2 ${getStatusColor(status.status)}`}>
                    {getStatusIcon(status.status)}
                    {status.status.toUpperCase()}
                  </div>
                </div>
              </div>

              {status.last_sync && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                  Last sync: {new Date(status.last_sync).toLocaleString()}
                </p>
              )}

              {status.endpoints_count !== undefined && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                  Endpoints: {status.endpoints_count}
                </p>
              )}

              {status.error && (
                <p className="text-xs text-red-600 dark:text-red-400 mb-4">
                  Error: {status.error}
                </p>
              )}

              <button
                onClick={() => handleSyncProvider(status.provider)}
                className="w-full px-4 py-2 bg-indigo-100 dark:bg-indigo-900/30 hover:bg-indigo-200 dark:hover:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 rounded-xl transition-all flex items-center justify-center gap-2"
              >
                <Play className="w-4 h-4" />
                Sync Now
              </button>
            </div>
          ))}
        </div>

        {/* Stats */}
        <div className="mt-8 grid md:grid-cols-3 gap-6">
          <div className="p-6 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-2xl shadow-xl text-white">
            <h4 className="text-sm opacity-90 mb-2">Total Providers</h4>
            <p className="text-4xl font-bold">{providers.length}</p>
          </div>

          <div className="p-6 bg-gradient-to-br from-emerald-500 to-teal-600 rounded-2xl shadow-xl text-white">
            <h4 className="text-sm opacity-90 mb-2">Synced</h4>
            <p className="text-4xl font-bold">
              {Object.values(syncStatuses).filter(s => s.status === 'synced').length}
            </p>
          </div>

          <div className="p-6 bg-gradient-to-br from-orange-500 to-red-600 rounded-2xl shadow-xl text-white">
            <h4 className="text-sm opacity-90 mb-2">Total Endpoints</h4>
            <p className="text-4xl font-bold">
              {Object.values(syncStatuses).reduce((acc, s) => acc + (s.endpoints_count || 0), 0)}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
