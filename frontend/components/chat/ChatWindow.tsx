'use client';

import React, { useState, useEffect, useRef } from 'react';
import { streamChatCompletion } from '@/lib/api/chat';
import { listDocuments } from '@/lib/api/documents';
import { CitationSource, DocumentResponse } from '@/lib/api/types';
import { FormattedMessageText } from './CitationBadge';
import { 
  ArrowRight, 
  Trash2, 
  ChevronDown, 
  Sparkles, 
  Info, 
  Layers, 
  AlertCircle
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sources?: CitationSource[];
  isStreaming?: boolean;
  streamingStage?: 'searching' | 'ranking' | 'generating';
}

export const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputQuery, setInputQuery] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedDocId, setSelectedDocId] = useState<string>('');
  const [documents, setDocuments] = useState<DocumentResponse[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [expandedWhyAnswer, setExpandedWhyAnswer] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const mainInputRef = useRef<HTMLInputElement>(null);

  // Fetch document catalog for document scope filter dropdown
  useEffect(() => {
    let isMounted = true;
    listDocuments(0, 50)
      .then((res) => {
        if (isMounted) {
          const completedDocs = (res.items || []).filter((d) => d.status === 'COMPLETED');
          setDocuments(completedDocs);
        }
      })
      .catch(() => {
        // Silently fail document filter fetch if empty/unauthorized
      });

    return () => {
      isMounted = false;
    };
  }, []);

  // Auto-scroll to bottom as text streams in
  useEffect(() => {
    if (messages.length > 0) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const handleSendMessage = async (queryToSend?: string) => {
    const query = (queryToSend ?? inputQuery).trim();
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
      streamingStage: 'searching',
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setIsGenerating(true);

    let accumulatedAnswer = '';
    let currentSources: CitationSource[] = [];

    // Progressive status staging
    const rankingTimer = setTimeout(() => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && msg.isStreaming
            ? { ...msg, streamingStage: 'ranking' }
            : msg
        )
      );
    }, 450);

    const generatingTimer = setTimeout(() => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === assistantMessageId && msg.isStreaming
            ? { ...msg, streamingStage: 'generating' }
            : msg
        )
      );
    }, 900);

    await streamChatCompletion(
      {
        query,
        tenant_id: 'tenant_default',
        document_id: selectedDocId || undefined,
        top_k: 5,
      },
      {
        onSources: (sources) => {
          clearTimeout(rankingTimer);
          clearTimeout(generatingTimer);
          currentSources = sources;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, sources: currentSources, streamingStage: 'generating' }
                : msg
            )
          );
        },
        onToken: (token) => {
          accumulatedAnswer += token;
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: accumulatedAnswer, streamingStage: 'generating' }
                : msg
            )
          );
        },
        onError: (err) => {
          clearTimeout(rankingTimer);
          clearTimeout(generatingTimer);
          setError(err.message);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: accumulatedAnswer || 'An error occurred while generating the response.',
                    isStreaming: false,
                  }
                : msg
            )
          );
          setIsGenerating(false);
        },
        onComplete: () => {
          clearTimeout(rankingTimer);
          clearTimeout(generatingTimer);
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
    if (messages.length === 0) return;
    setMessages([]);
    setError(null);
    setExpandedWhyAnswer({});
  };

  const toggleWhyAnswer = (msgId: string) => {
    setExpandedWhyAnswer((prev) => ({
      ...prev,
      [msgId]: !prev[msgId],
    }));
  };

  // Pre-configured suggestions
  const suggestionQueries = [
    'Summarize the key findings',
    'What are the main recommendations?',
    'Compare the uploaded documents',
    'Find the relevant requirements',
  ];

  return (
    <section 
      aria-label="Document Intelligence Chat"
      className="w-full max-w-4xl mx-auto flex flex-col h-[calc(100vh-100px)] min-h-[500px]"
    >
      {/* Scope & Action Header Bar */}
      <div className="px-4 py-2.5 bg-[var(--surface-primary)] border border-[var(--border-subtle)] rounded-t-md flex items-center justify-between gap-4 text-xs font-mono transition-colors duration-150">
        <div className="flex items-center gap-2 flex-wrap">
          <label htmlFor="document-scope-select" className="text-[var(--text-muted)] uppercase text-[10px] tracking-wider font-semibold">
            SCOPE:
          </label>
          <div className="relative inline-flex items-center">
            <select
              id="document-scope-select"
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              aria-label="Filter document scope"
              className="appearance-none bg-[var(--surface-secondary)] border border-[var(--border-subtle)] text-[var(--text-primary)] px-2.5 py-1 pr-7 rounded text-xs focus:border-[var(--accent-primary)] focus:outline-none transition-colors"
            >
              <option value="">All Documents ({documents.length})</option>
              {documents.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.filename}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-[var(--text-secondary)] absolute right-2 pointer-events-none" aria-hidden="true" />
          </div>
        </div>

        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] text-xs px-2 py-1 rounded hover:bg-[var(--surface-secondary)] transition-colors focus:ring-1 focus:ring-[var(--accent-primary)]"
            aria-label="Clear conversation history"
          >
            <Trash2 className="w-3 h-3 text-[var(--text-secondary)]" aria-hidden="true" />
            <span>Clear Chat</span>
          </button>
        )}
      </div>

      {/* Main Conversation Container */}
      <div 
        tabIndex={0}
        role="region"
        aria-label="Conversation Thread"
        className="flex-1 bg-[var(--surface-primary)]/40 border-x border-[var(--border-subtle)] overflow-y-auto p-4 md:p-8 space-y-8 focus:outline-none transition-colors duration-150"
      >
        {messages.length === 0 ? (
          /* EMPTY STATE */
          <div className="h-full flex flex-col items-center justify-center text-center max-w-xl mx-auto py-8">
            <div className="w-9 h-9 rounded bg-[var(--surface-secondary)] border border-[var(--border-subtle)] flex items-center justify-center text-[var(--accent-primary)] mb-4">
              <Sparkles className="w-4 h-4" aria-hidden="true" />
            </div>

            <h2 className="text-xl font-semibold text-[var(--text-primary)] tracking-tight">
              Ask ATLAS
            </h2>
            <p className="text-xs text-[var(--text-secondary)] mt-1.5 max-w-md leading-relaxed">
              Query your enterprise documents using hybrid retrieval and grounded generation.
            </p>

            {/* Centered Composer in Empty State */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="w-full mt-6"
            >
              <div className="relative flex items-center bg-[var(--surface-secondary)] border border-[var(--border-subtle)] focus-within:border-[var(--accent-primary)] rounded-md transition-colors shadow-xs">
                <input
                  ref={mainInputRef}
                  type="text"
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  placeholder="Ask your documents anything..."
                  disabled={isGenerating}
                  aria-label="Ask your documents anything"
                  className="w-full bg-transparent px-4 py-3 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={isGenerating || !inputQuery.trim()}
                  aria-label="Submit query to ATLAS"
                  className="mr-2 p-2 bg-[var(--surface-tertiary)] hover:bg-[var(--accent-primary)] text-[var(--text-secondary)] hover:text-[var(--bg-workspace)] disabled:opacity-40 disabled:hover:bg-[var(--surface-tertiary)] disabled:hover:text-[var(--text-secondary)] rounded transition-colors min-touch-target flex items-center justify-center"
                >
                  <ArrowRight className="w-4 h-4" aria-hidden="true" />
                </button>
              </div>
            </form>

            {/* Suggestion Chips */}
            <div className="w-full mt-4 flex flex-wrap items-center justify-center gap-2">
              {suggestionQueries.map((queryText) => (
                <button
                  key={queryText}
                  type="button"
                  onClick={() => handleSendMessage(queryText)}
                  className="px-2.5 py-1 text-[11px] font-mono text-[var(--text-secondary)] bg-[var(--surface-secondary)] hover:bg-[var(--surface-tertiary)] hover:text-[var(--text-primary)] border border-[var(--border-subtle)] rounded transition-colors"
                >
                  {queryText}
                </button>
              ))}
            </div>

            {/* Technical Metadata Footer */}
            <div className="mt-12 pt-6 border-t border-[var(--border-subtle)] text-[10px] font-mono text-[var(--text-muted)] tracking-wider uppercase flex items-center gap-2">
              <span className="inline-block w-1.5 h-1.5 rounded-full bg-[var(--status-ready)]" aria-hidden="true" />
              <span>Knowledge Base Ready</span>
              <span>·</span>
              <span>{documents.length} {documents.length === 1 ? 'Document' : 'Documents'}</span>
              <span>·</span>
              <span>Hybrid Retrieval</span>
            </div>
          </div>
        ) : (
          /* CONVERSATION VIEW (Technical Research Document Flow) */
          <div className="space-y-8 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <article
                key={msg.id}
                className="space-y-2"
                aria-label={msg.role === 'user' ? 'User Question' : 'ATLAS Response'}
              >
                {/* Role Marker Header */}
                <div className="flex items-center justify-between text-[11px] font-mono tracking-wider uppercase">
                  <span className={msg.role === 'user' ? 'text-[var(--text-secondary)] font-semibold' : 'text-[var(--accent-primary)] font-semibold flex items-center gap-1.5'}>
                    {msg.role === 'user' ? (
                      'YOU'
                    ) : (
                      <>
                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--status-ready)]" aria-hidden="true" />
                        <span>ATLAS</span>
                      </>
                    )}
                  </span>

                  {msg.role === 'assistant' && msg.sources && msg.sources.length > 0 && (
                    <button
                      type="button"
                      onClick={() => toggleWhyAnswer(msg.id)}
                      aria-expanded={Boolean(expandedWhyAnswer[msg.id])}
                      className="text-[10px] text-[var(--text-muted)] hover:text-[var(--text-secondary)] flex items-center gap-1 font-mono transition-colors"
                    >
                      <Info className="w-3 h-3" aria-hidden="true" />
                      <span>Why this answer?</span>
                    </button>
                  )}
                </div>

                {/* Message Body Content */}
                <div className={`text-sm leading-relaxed ${
                  msg.role === 'user' 
                    ? 'text-[var(--text-primary)] pl-3 border-l-2 border-[var(--border-subtle)]' 
                    : 'text-[var(--text-primary)] pl-3 border-l-2 border-[var(--accent-primary)]/40 space-y-3'
                }`}>
                  {msg.role === 'assistant' ? (
                    <div>
                      {/* Streaming status progress */}
                      {msg.isStreaming && !msg.content ? (
                        <div 
                          className="flex items-center gap-2 text-xs font-mono text-[var(--text-secondary)] py-2"
                          role="status"
                          aria-live="polite"
                        >
                          <span className="w-2 h-2 rounded-full bg-[var(--status-ready)] animate-pulse" aria-hidden="true" />
                          <span>
                            {msg.streamingStage === 'searching' && 'Searching documents...'}
                            {msg.streamingStage === 'ranking' && 'Ranking relevant passages...'}
                            {msg.streamingStage === 'generating' && 'Generating grounded answer...'}
                          </span>
                        </div>
                      ) : (
                        <FormattedMessageText text={msg.content} sources={msg.sources || []} />
                      )}

                      {/* "Why This Answer?" Transparency Panel */}
                      {expandedWhyAnswer[msg.id] && msg.sources && msg.sources.length > 0 && (
                        <div className="mt-3 p-3 bg-[var(--surface-secondary)] border border-[var(--border-subtle)] rounded text-[11px] font-mono text-[var(--text-secondary)] space-y-1.5 transition-colors duration-150">
                          <div className="text-[10px] text-[var(--accent-primary)] uppercase tracking-wider font-semibold mb-1 flex items-center gap-1.5">
                            <Layers className="w-3 h-3" aria-hidden="true" />
                            <span>Retrieval Transparency Report</span>
                          </div>
                          <div>Strategy: <span className="text-[var(--text-primary)]">Hybrid (Dense BGE-Small + Sparse BM25)</span></div>
                          <div>Rank Fusion: <span className="text-[var(--text-primary)]">Reciprocal Rank Fusion (k=60)</span></div>
                          <div>Sources Evaluated: <span className="text-[var(--text-primary)]">{msg.sources.length} Context Chunks</span></div>
                          <div>
                            Documents Cited:{' '}
                            <span className="text-[var(--text-primary)]">
                              {Array.from(new Set(msg.sources.map((s) => s.file_name))).join(', ')}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-[var(--text-primary)] font-medium">{msg.content}</div>
                  )}
                </div>
              </article>
            ))}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Error Callout */}
      {error && (
        <div 
          role="alert" 
          aria-live="assertive"
          className="mx-4 my-2 p-2.5 bg-[var(--surface-secondary)] border border-[var(--status-failed)] text-[var(--status-failed)] text-xs rounded flex items-start gap-2"
        >
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[var(--status-failed)]" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Fixed Composer Footer (When Conversation Exists) */}
      {messages.length > 0 && (
        <footer className="p-3 bg-[var(--surface-primary)] border border-[var(--border-subtle)] rounded-b-md transition-colors duration-150">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              placeholder="Ask your documents anything..."
              disabled={isGenerating}
              aria-label="Ask your documents anything"
              className="flex-1 bg-[var(--surface-secondary)] border border-[var(--border-subtle)] focus:border-[var(--accent-primary)] rounded px-3 py-2.5 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none transition-colors"
            />
            <button
              type="submit"
              disabled={isGenerating || !inputQuery.trim()}
              aria-label="Send message"
              className="p-2.5 bg-[var(--surface-secondary)] hover:bg-[var(--surface-tertiary)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--accent-primary)] rounded disabled:opacity-40 transition-colors min-touch-target flex items-center justify-center"
            >
              <ArrowRight className="w-4 h-4 text-[var(--accent-primary)]" aria-hidden="true" />
            </button>
          </form>
        </footer>
      )}
    </section>
  );
};
