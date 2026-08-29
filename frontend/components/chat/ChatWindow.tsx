'use client';

import React, { useState, useEffect, useRef } from 'react';
import { streamChatCompletion } from '@/lib/api/chat';
import { listDocuments } from '@/lib/api/documents';
import { CitationSource, DocumentResponse } from '@/lib/api/types';
import { FormattedMessageText } from './CitationBadge';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: CitationSource[];
  isStreaming?: boolean;
}

interface ChatWindowProps {
  tenantId: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({ tenantId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch document list for document filter dropdown
  useEffect(() => {
    listDocuments(0, 50)
      .then((res) => {
        const completedDocs = (res.items || []).filter((d) => d.status === 'COMPLETED');
        setDocuments(completedDocs);
      })
      .catch(() => {
        // Silently fail document filter fetch if empty
      });
  }, []);

  // Auto-scroll to bottom as text streams in
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const query = inputQuery.trim();
    if (!query || isGenerating) return;

    setError(null);
    setInputQuery('');

    const userMessageId = `user-${Date.now()}`;
    const assistantMessageId = `assistant-${Date.now()}`;

    const userMsg: Message = {
      id: userMessageId,
      role: 'user',
      content: query,
    };

    const assistantMsg: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      sources: [],
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsGenerating(true);

    let accumulatedAnswer = '';
    let currentSources: CitationSource[] = [];

    await streamChatCompletion(
      {
        query,
        tenant_id: tenantId,
        document_id: selectedDocId || undefined,
        top_k: 5,
      },
      {
        onSources: (sources) => {
          currentSources = sources;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, sources: currentSources }
                : msg
            )
          );
        },
        onToken: (token) => {
          accumulatedAnswer += token;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: accumulatedAnswer }
                : msg
            )
          );
        },
        onError: (err) => {
          setError(err.message);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: accumulatedAnswer || 'An error occurred while generating response.',
                    isStreaming: false,
                  }
                : msg
            )
          );
          setIsGenerating(false);
        },
        onComplete: () => {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, isStreaming: false }
                : msg
            )
          );
          setIsGenerating(false);
        },
      }
    );
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div className="w-full max-w-4xl mx-auto h-[calc(100vh-140px)] flex flex-col bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Chat Header Bar */}
      <div className="px-6 py-3.5 border-b border-gray-200 bg-gray-50 flex items-center justify-between gap-4 text-xs">
        <div className="flex items-center space-x-3">
          <span className="font-semibold text-gray-900">RAG Chat Assistant</span>
          <span className="text-gray-400">|</span>
          <label className="text-gray-600 font-medium">Filter Document:</label>
          <select
            value={selectedDocId}
            onChange={(e) => setSelectedDocId(e.target.value)}
            className="px-2 py-1 bg-white border border-gray-300 rounded text-xs text-gray-800 focus:outline-none"
          >
            <option value="">All Uploaded Documents</option>
            {documents.map((doc) => (
              <option key={doc.id} value={doc.id}>
                {doc.filename}
              </option>
            ))}
          </select>
        </div>

        <button
          onClick={clearChat}
          className="text-xs text-gray-600 hover:text-gray-900 hover:underline"
        >
          Clear Chat
        </button>
      </div>

      {/* Messages Thread Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center text-gray-400">
            <p className="text-sm font-medium text-gray-600">Start a Grounded RAG Chat</p>
            <p className="text-xs mt-1 max-w-md text-gray-400">
              Ask questions about your uploaded documents. Responses are synthesized with verified inline citation badges.
            </p>
          </div>
        ) : (
          messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.role === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div
                className={`max-w-2xl px-4 py-3 rounded-lg text-sm leading-relaxed ${
                  msg.role === 'user'
                    ? 'bg-gray-900 text-white'
                    : 'bg-gray-50 border border-gray-200 text-gray-900'
                }`}
              >
                {msg.role === 'assistant' ? (
                  <div>
                    {msg.content ? (
                      <FormattedMessageText text={msg.content} sources={msg.sources || []} />
                    ) : (
                      <span className="text-gray-400 italic text-xs animate-pulse">
                        Retrieving context & generating answer...
                      </span>
                    )}

                    {/* Sources Summary list at bottom of message */}
                    {msg.sources && msg.sources.length > 0 && !msg.isStreaming && (
                      <div className="mt-3 pt-3 border-t border-gray-200 text-xs text-gray-600">
                        <div className="font-semibold text-gray-800 mb-1.5 text-[11px] uppercase tracking-wider">
                          Grounding Citations ({msg.sources.length}):
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {msg.sources.map((src) => (
                            <span
                              key={src.chunk_id}
                              className="px-2 py-0.5 bg-white border border-gray-200 rounded text-[11px] font-mono text-gray-700"
                            >
                              [{src.source_index}] {src.file_name} (p. {src.page_number})
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div>{msg.content}</div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {error && (
        <div className="mx-6 mb-2 p-2 bg-red-50 border border-red-200 text-red-700 text-xs rounded">
          {error}
        </div>
      )}

      {/* Input Form Footer */}
      <form onSubmit={handleSendMessage} className="p-4 border-t border-gray-200 bg-white flex gap-2">
        <input
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          placeholder="Ask a question grounded in your documents..."
          disabled={isGenerating}
          className="flex-1 px-4 py-2.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-gray-400 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isGenerating || !inputQuery.trim()}
          className="px-5 py-2.5 bg-gray-900 text-white text-sm font-medium rounded-md hover:bg-gray-800 disabled:opacity-50 transition-colors"
        >
          {isGenerating ? 'Streaming...' : 'Send'}
        </button>
      </form>
    </div>
  );
};
