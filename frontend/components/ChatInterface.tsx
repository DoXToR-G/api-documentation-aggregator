'use client';

import React, { useState, useRef, useEffect } from 'react';
import { Send, Loader2, Bot, User, Sparkles, X, Trash2 } from 'lucide-react';
import axios from 'axios';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

interface ChatInterfaceProps {
  apiUrl?: string;
  onClose?: () => void;
}

// Session storage keys
const CHAT_SESSION_KEY = 'chat_messages';
const CHAT_INPUT_KEY = 'chat_input';

export default function ChatInterface({ apiUrl = 'http://localhost:8000', onClose }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);

    // Load saved session from localStorage
    const savedMessages = localStorage.getItem(CHAT_SESSION_KEY);
    const savedInput = localStorage.getItem(CHAT_INPUT_KEY);

    if (savedMessages) {
      try {
        const parsedMessages = JSON.parse(savedMessages);
        setMessages(parsedMessages);
      } catch (e) {
        console.error('Failed to parse saved messages:', e);
        // Set welcome message if parsing fails
        setWelcomeMessage();
      }
    } else {
      // Add welcome message if no saved session
      setWelcomeMessage();
    }

    if (savedInput) {
      setInput(savedInput);
    }
  }, []);

  const setWelcomeMessage = () => {
    const welcomeMsg = [{
      id: '1',
      role: 'assistant' as const,
      content: 'Hello! I\'m your AI documentation assistant. Ask me anything about API documentation, endpoints, or how to use specific APIs.',
      timestamp: new Date().toISOString()
    }];
    setMessages(welcomeMsg);
    localStorage.setItem(CHAT_SESSION_KEY, JSON.stringify(welcomeMsg));
  };

  // Save messages to localStorage whenever they change
  useEffect(() => {
    if (mounted && messages.length > 0) {
      localStorage.setItem(CHAT_SESSION_KEY, JSON.stringify(messages));
    }
  }, [messages, mounted]);

  // Save input to localStorage whenever it changes
  useEffect(() => {
    if (mounted) {
      localStorage.setItem(CHAT_INPUT_KEY, input);
    }
  }, [input, mounted]);

  const clearSession = () => {
    if (confirm('Are you sure you want to clear the chat history?')) {
      localStorage.removeItem(CHAT_SESSION_KEY);
      localStorage.removeItem(CHAT_INPUT_KEY);
      setWelcomeMessage();
      setInput('');
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    // Only auto-scroll if there's more than just the welcome message
    // This prevents scrolling on initial mount
    if (messages.length > 1) {
      scrollToBottom();
    }
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${apiUrl}/ai/query`, {
        query: input,
        context: {},
        session_id: null
      }, {
        timeout: 60000, // 60 second timeout
        headers: {
          'Content-Type': 'application/json'
        }
      });

      console.log('AI Response:', response.data);

      // Extract and format the response text
      let responseText = 'I received your message but couldn\'t generate a response.';

      if (response.data && response.data.response) {
        const aiResponse = response.data.response;

        // Handle different response types
        if (typeof aiResponse === 'string') {
          responseText = aiResponse;
        } else if (typeof aiResponse === 'object') {
          // Handle error responses (with help_examples array)
          if (aiResponse.error) {
            responseText = `Error: ${aiResponse.error}`;
          }
          // Handle error type with message, suggestion, and help_examples
          else if (aiResponse.type === 'error') {
            responseText = aiResponse.message || 'An error occurred.';
            if (aiResponse.suggestion) {
              responseText += `\n\n${aiResponse.suggestion}`;
            }
            if (aiResponse.help_examples && Array.isArray(aiResponse.help_examples)) {
              responseText += '\n\n' + aiResponse.help_examples.join('\n');
            }
          }
          // Handle enhanced search results
          else if (aiResponse.type === 'enhanced_search_results' && aiResponse.results) {
            if (aiResponse.results.length === 0 && (!aiResponse.web_results || aiResponse.web_results.length === 0)) {
              responseText = `I couldn't find any results for "${input}". Try rephrasing your query or check if the provider data has been synced.`;
            } else {
              // Database results
              if (aiResponse.results.length > 0) {
                responseText = `I found ${aiResponse.results.length} relevant endpoint(s) in the database:\n\n`;
                aiResponse.results.forEach((result: any, index: number) => {
                  responseText += `${index + 1}. **${result.title || result.endpoint}**\n`;
                  responseText += `   Method: ${result.method || 'N/A'}\n`;
                  responseText += `   Provider: ${result.provider || 'N/A'}\n`;
                  if (result.description) {
                    responseText += `   Description: ${result.description}\n`;
                  }
                  responseText += `   Endpoint: ${result.endpoint || 'N/A'}\n\n`;
                });
              }

              // Web search results
              if (aiResponse.web_results && aiResponse.web_results.length > 0) {
                if (aiResponse.results.length > 0) {
                  responseText += `\n---\n\n📡 **Additional Web Search Results** (${aiResponse.web_results.length}):\n\n`;
                } else {
                  responseText = `I found ${aiResponse.web_results.length} result(s) from web search:\n\n`;
                }
                aiResponse.web_results.forEach((result: any, index: number) => {
                  responseText += `${index + 1}. **${result.title}**\n`;
                  responseText += `   ${result.snippet}\n`;
                  responseText += `   🔗 ${result.url}\n\n`;
                });
              }
            }
          }
          // Handle other object types with type and message
          else if (aiResponse.type && aiResponse.message) {
            responseText = aiResponse.message;
          }
          // Fallback to JSON string
          else {
            responseText = JSON.stringify(aiResponse, null, 2);
          }
        }
      }

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: responseText,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, aiMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);

      let errorText = 'Sorry, I encountered an error. Please try again.';

      // Handle timeout specifically
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorText = 'Request timed out. The AI is taking longer than expected. Please try again or rephrase your question.';
      }
      // Handle network errors
      else if (error.message === 'Network Error') {
        errorText = 'Network error. Please check if the backend server is running at ' + apiUrl;
      }
      // Handle different error response formats
      else if (error.response?.data?.detail) {
        const detail = error.response.data.detail;

        // If detail is an array (FastAPI validation errors)
        if (Array.isArray(detail)) {
          errorText = 'Validation Error:\n\n';
          detail.forEach((err: any) => {
            const location = err.loc ? err.loc.join(' -> ') : 'unknown';
            errorText += `• ${location}: ${err.msg}\n`;
          });
        }
        // If detail is an object with validation error structure
        else if (typeof detail === 'object' && detail.type) {
          errorText = `Error: ${detail.msg || detail.message || JSON.stringify(detail)}`;
        }
        // If detail is a string
        else if (typeof detail === 'string') {
          errorText = `Error: ${detail}`;
        }
        // Fallback for other object types
        else {
          errorText = `Error: ${JSON.stringify(detail)}`;
        }
      } else if (error.message) {
        errorText = `Error: ${error.message}`;
      }

      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: errorText,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  if (!mounted) return null;

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900 rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700">
      {/* Header */}
      <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-t-2xl">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-lg">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white">AI Assistant</h2>
            <p className="text-sm text-indigo-100">Ask me about API documentation</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={clearSession}
            className="p-2 hover:bg-white/20 rounded-lg transition-colors"
            title="Clear chat history"
          >
            <Trash2 className="w-5 h-5 text-white" />
          </button>
          {onClose && (
            <button
              onClick={onClose}
              className="p-2 hover:bg-white/20 rounded-lg transition-colors"
              title="Close"
            >
              <X className="w-5 h-5 text-white" />
            </button>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.role === 'assistant' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
            )}

            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                message.role === 'user'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100'
              }`}
            >
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {typeof message.content === 'string'
                  ? message.content
                  : JSON.stringify(message.content, null, 2)
                }
              </p>
              <span className={`text-xs mt-1 block ${
                message.role === 'user' ? 'text-indigo-100' : 'text-gray-500 dark:text-gray-400'
              }`}>
                {new Date(message.timestamp).toLocaleTimeString()}
              </span>
            </div>

            {message.role === 'user' && (
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center">
                <User className="w-5 h-5 text-white" />
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex gap-3 justify-start">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded-2xl px-4 py-3">
              <Loader2 className="w-5 h-5 animate-spin text-indigo-600" />
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-200 dark:border-gray-700">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about API documentation..."
            className="flex-1 px-4 py-3 rounded-xl border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-xl hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
