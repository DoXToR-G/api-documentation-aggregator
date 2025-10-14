'use client';

import React, { useState, useEffect } from 'react';
import {
  Key,
  Save,
  CheckCircle,
  XCircle,
  Loader2,
  Brain,
  AlertCircle,
  Edit3
} from 'lucide-react';
import axios from 'axios';

console.log('=== AIConfigPanel module loaded ===');

interface AIModel {
  id: string;
  name: string;
  description: string;
  context_window: number;
  cost_per_1m_tokens: {
    input: number;
    output: number;
  };
}

interface AIConfigPanelProps {
  onSaveSuccess?: () => void;
}

export default function AIConfigPanel({ onSaveSuccess }: AIConfigPanelProps) {
  console.log('=== AIConfigPanel component rendering ===');

  // State
  const [openAIKey, setOpenAIKey] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt-4o-mini');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [enableWebSearch, setEnableWebSearch] = useState(false);

  // UI State
  const [isValidating, setIsValidating] = useState(false);
  const [keyValidStatus, setKeyValidStatus] = useState<'unknown' | 'valid' | 'invalid'>('unknown');
  const [validationMessage, setValidationMessage] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState('');
  const [availableModels, setAvailableModels] = useState<AIModel[]>([]);
  const [showPromptEditor, setShowPromptEditor] = useState(false);

  // Load settings on mount
  useEffect(() => {
    console.log('AIConfigPanel mounted, loading settings and models...');
    loadSettings().catch(err => console.error('loadSettings failed:', err));
    loadModels().catch(err => console.error('loadModels failed:', err));
  }, []);

  const loadSettings = async () => {
    console.log('[loadSettings] Starting...');
    try {
      console.log('[loadSettings] Fetching from /api/v1/ai/settings');
      const response = await axios.get('http://localhost:8000/api/v1/ai/settings');
      console.log('[loadSettings] Response:', response.data);
      const data = response.data;

      setSelectedModel(data.openai_model || 'gpt-4o-mini');
      setSystemPrompt(data.system_prompt || '');
      setEnableWebSearch(data.enable_web_search || false);

      // Load API key from localStorage (for display only)
      const savedKey = localStorage.getItem('openai_api_key');
      if (savedKey) {
        console.log('[loadSettings] Found saved API key in localStorage');
        setOpenAIKey(savedKey);
        setKeyValidStatus('unknown');
      }
      console.log('[loadSettings] Complete');
    } catch (error: any) {
      console.error('[loadSettings] FAILED:', error);
      // Silently fail - non-critical error
    }
  };

  const loadModels = async () => {
    try {
      const response = await axios.get('http://localhost:8000/api/v1/ai/models');
      setAvailableModels(response.data.models || []);
    } catch (error: any) {
      console.error('Failed to load models:', error);
      // Silently fail - use default models if API fails
      setAvailableModels([
        {
          id: "gpt-4o-mini",
          name: "GPT-4o Mini",
          description: "Fast and affordable",
          context_window: 128000,
          cost_per_1m_tokens: { input: 0.15, output: 0.60 }
        }
      ]);
    }
  };

  const validateAPIKey = async () => {
    if (!openAIKey || !openAIKey.startsWith('sk-')) {
      setKeyValidStatus('invalid');
      setValidationMessage('API key must start with "sk-"');
      return;
    }

    setIsValidating(true);
    setKeyValidStatus('unknown');
    setValidationMessage('');

    const requestPayload = { api_key: openAIKey };
    console.log('Validating API key, sending:', JSON.stringify(requestPayload));
    console.log('API key value:', openAIKey);
    console.log('API key type:', typeof openAIKey);

    try {
      const response = await axios.post('http://localhost:8000/api/v1/ai/validate-key',
        requestPayload,
        {
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
          }
        }
      );

      console.log('Validation response:', response.data);

      const data = response.data;

      if (data && typeof data === 'object') {
        if (data.valid) {
          setKeyValidStatus('valid');
          setValidationMessage(String(data.message || 'API key is valid'));
        } else {
          setKeyValidStatus('invalid');
          setValidationMessage(String(data.message || 'API key is invalid'));
        }
      } else {
        setKeyValidStatus('invalid');
        setValidationMessage('Unexpected response format');
      }
    } catch (error: any) {
      console.error('Validation error:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);

      setKeyValidStatus('invalid');

      // Handle different error response formats
      let errorMsg = 'Validation failed';

      if (error.response?.data) {
        const data = error.response.data;

        // Check for detail field (FastAPI error format)
        if (data.detail) {
          const detail = data.detail;

          // If detail is an array (FastAPI validation errors)
          if (Array.isArray(detail)) {
            errorMsg = 'Validation error: ' + detail.map((err: any) => {
              const location = Array.isArray(err.loc) ? err.loc.join(' -> ') : 'unknown';
              const message = err.msg || err.message || 'invalid';
              return `${location}: ${message}`;
            }).join(', ');
          }
          // If detail is a string
          else if (typeof detail === 'string') {
            errorMsg = detail;
          }
          // If detail is an object
          else if (typeof detail === 'object' && detail !== null) {
            errorMsg = detail.message || JSON.stringify(detail);
          }
        }
        // Check for message field
        else if (data.message && typeof data.message === 'string') {
          errorMsg = data.message;
        }
        // Fallback to stringifying the whole response
        else if (typeof data === 'string') {
          errorMsg = data;
        }
        else {
          errorMsg = 'Validation failed: ' + JSON.stringify(data);
        }
      } else if (error.message) {
        errorMsg = error.message;
      }

      console.log('Setting validation message:', errorMsg);
      setValidationMessage(String(errorMsg)); // Ensure it's always a string
    } finally {
      setIsValidating(false);
    }
  };

  const handleSaveSettings = async () => {
    setIsSaving(true);
    setSaveMessage('');

    try {
      // Save to backend
      await axios.post('http://localhost:8000/api/v1/ai/settings', {
        openai_api_key: openAIKey,
        openai_model: selectedModel,
        system_prompt: systemPrompt,
        enable_web_search: enableWebSearch
      });

      // Save to localStorage (for persistence across sessions)
      localStorage.setItem('openai_api_key', openAIKey);
      localStorage.setItem('openai_model', selectedModel);
      localStorage.setItem('enable_web_search', enableWebSearch.toString());

      setSaveMessage('Settings saved successfully! AI agent updated.');
      setTimeout(() => setSaveMessage(''), 5000);

      if (onSaveSuccess) {
        onSaveSuccess();
      }
    } catch (error: any) {
      console.error('Save settings error:', error);

      // Handle different error response formats
      let errorMsg = 'Failed to save settings';

      if (error.response?.data?.detail) {
        const detail = error.response.data.detail;

        // If detail is an array (FastAPI validation errors)
        if (Array.isArray(detail)) {
          errorMsg = detail.map((err: any) => {
            const location = err.loc ? err.loc.join(' -> ') : 'unknown';
            return `${location}: ${err.msg}`;
          }).join(', ');
        }
        // If detail is a string
        else if (typeof detail === 'string') {
          errorMsg = detail;
        }
        // If detail is an object
        else if (typeof detail === 'object') {
          errorMsg = detail.message || JSON.stringify(detail);
        }
      } else if (error.message) {
        errorMsg = error.message;
      }

      setSaveMessage(errorMsg);
      setTimeout(() => setSaveMessage(''), 5000);
    } finally {
      setIsSaving(false);
    }
  };

  const getStatusIcon = () => {
    if (isValidating) {
      return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
    }
    switch (keyValidStatus) {
      case 'valid':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'invalid':
        return <XCircle className="w-5 h-5 text-red-500" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = () => {
    switch (keyValidStatus) {
      case 'valid':
        return 'border-green-500 bg-green-50 dark:bg-green-900/20';
      case 'invalid':
        return 'border-red-500 bg-red-50 dark:bg-red-900/20';
      default:
        return 'border-gray-300 dark:border-gray-600';
    }
  };

  return (
    <div className="p-6 bg-white/90 dark:bg-gray-800/90 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-200 dark:border-gray-700">
      <h2 className="text-2xl font-bold mb-6 flex items-center gap-3 text-gray-900 dark:text-gray-100">
        <Brain className="w-7 h-7 text-indigo-600" />
        AI Configuration
      </h2>

      <div className="space-y-6">
        {/* OpenAI API Key */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            OpenAI API Key
          </label>
          <div className="flex gap-2">
            <div className={`flex-1 flex items-center gap-2 px-4 py-3 border-2 rounded-xl transition-all ${getStatusColor()}`}>
              <Key className="w-5 h-5 text-gray-400" />
              <input
                type="password"
                value={openAIKey}
                onChange={(e) => {
                  setOpenAIKey(e.target.value);
                  setKeyValidStatus('unknown');
                }}
                placeholder="sk-..."
                className="flex-1 bg-transparent text-gray-900 dark:text-gray-100 focus:outline-none"
              />
              {getStatusIcon()}
            </div>
            <button
              onClick={validateAPIKey}
              disabled={isValidating || !openAIKey}
              className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all font-medium"
            >
              {isValidating ? 'Validating...' : 'Validate'}
            </button>
          </div>
          {validationMessage && typeof validationMessage === 'string' && validationMessage.length > 0 && (
            <p className={`mt-2 text-sm ${keyValidStatus === 'valid' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {validationMessage}
            </p>
          )}
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Get your API key from <a href="https://platform.openai.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-indigo-600 hover:underline">OpenAI Platform</a>
          </p>
        </div>

        {/* Model Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            AI Model
          </label>
          <select
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value)}
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            {availableModels.map((model) => (
              <option key={model.id} value={model.id}>
                {model.name} - ${model.cost_per_1m_tokens.input}/1M tokens
              </option>
            ))}
          </select>
          {availableModels.find(m => m.id === selectedModel) && (
            <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
              {availableModels.find(m => m.id === selectedModel)?.description}
            </p>
          )}
        </div>

        {/* System Prompt */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              System Prompt Template
            </label>
            <button
              onClick={() => setShowPromptEditor(!showPromptEditor)}
              className="text-sm text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <Edit3 className="w-4 h-4" />
              {showPromptEditor ? 'Hide' : 'Edit'}
            </button>
          </div>

          {showPromptEditor && (
            <textarea
              value={systemPrompt}
              onChange={(e) => setSystemPrompt(e.target.value)}
              rows={12}
              className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 font-mono text-sm"
              placeholder="Enter system prompt that guides AI behavior..."
            />
          )}

          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            This prompt defines how the AI assistant behaves and responds to queries
          </p>
        </div>

        {/* Web Search Toggle */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Enable Web Search
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Allow AI to search the web when database results are insufficient
              </p>
            </div>
            <button
              onClick={() => setEnableWebSearch(!enableWebSearch)}
              className={`relative inline-flex h-8 w-14 items-center rounded-full transition-colors ${
                enableWebSearch ? 'bg-indigo-600' : 'bg-gray-300 dark:bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-6 w-6 transform rounded-full bg-white transition-transform ${
                  enableWebSearch ? 'translate-x-7' : 'translate-x-1'
                }`}
              />
            </button>
          </div>
        </div>

        {/* Save Message */}
        {saveMessage && (
          <div className={`p-4 rounded-xl text-sm ${
            (typeof saveMessage === 'string' && saveMessage.includes('success'))
              ? 'bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 text-green-700 dark:text-green-400'
              : 'bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400'
          }`}>
            {typeof saveMessage === 'string' ? saveMessage : JSON.stringify(saveMessage)}
          </div>
        )}

        {/* Save Button */}
        <button
          onClick={handleSaveSettings}
          disabled={isSaving || keyValidStatus === 'invalid'}
          className="w-full px-6 py-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-xl transition-all flex items-center justify-center gap-2 font-semibold shadow-lg"
        >
          {isSaving ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-5 h-5" />
              Save AI Configuration
            </>
          )}
        </button>

        {/* Status Summary */}
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="text-gray-600 dark:text-gray-400">API Status:</span>
              <span className={`ml-2 font-medium ${
                keyValidStatus === 'valid' ? 'text-green-600 dark:text-green-400' :
                keyValidStatus === 'invalid' ? 'text-red-600 dark:text-red-400' :
                'text-gray-600 dark:text-gray-400'
              }`}>
                {keyValidStatus === 'valid' ? '● Connected' :
                 keyValidStatus === 'invalid' ? '● Disconnected' :
                 '● Unknown'}
              </span>
            </div>
            <div>
              <span className="text-gray-600 dark:text-gray-400">Model:</span>
              <span className="ml-2 font-medium text-gray-900 dark:text-gray-100">
                {selectedModel}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
