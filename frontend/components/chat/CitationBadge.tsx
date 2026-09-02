'use client';

import React, { useState, useRef, useEffect } from 'react';
import { CitationSource } from '@/lib/api/types';
import { FileText, X } from 'lucide-react';

interface CitationBadgeProps {
  sourceIndex: number;
  sources: CitationSource[];
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ sourceIndex, sources }) => {
  const [isOpen, setIsOpen] = useState(false);
  const popoverRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);

  const source = sources.find((s) => s.source_index === sourceIndex);

  // Close on Outside Click or Escape Key (WCAG AA requirement)
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsOpen(false);
        triggerRef.current?.focus();
      }
    };

    const handleClickOutside = (e: MouseEvent) => {
      if (
        popoverRef.current &&
        !popoverRef.current.contains(e.target as Node) &&
        triggerRef.current &&
        !triggerRef.current.contains(e.target as Node)
      ) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isOpen]);

  if (!source) {
    return (
      <span className="inline-block font-mono text-xs text-[var(--text-muted)] px-1">
        [{sourceIndex}]
      </span>
    );
  }

  const scorePercentage = (Math.max(0, Math.min(1, source.score)) * 100).toFixed(1);

  return (
    <span className="relative inline-block mx-0.5 align-baseline">
      <button
        ref={triggerRef}
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="dialog"
        aria-label={`Source ${source.source_index}: ${source.file_name}, page ${source.page_number}`}
        className={`inline-flex items-center gap-1 px-1.5 py-0.2 text-[11px] font-mono rounded border transition-colors ${
          isOpen
            ? 'bg-[var(--surface-tertiary)] text-[var(--text-primary)] border-[var(--accent-primary)]'
            : 'bg-[var(--surface-secondary)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] border-[var(--border-subtle)] hover:border-[var(--accent-primary)]'
        }`}
      >
        <span className="text-[var(--accent-primary)] font-semibold">[{source.source_index}]</span>
        <span className="max-w-[120px] truncate hidden sm:inline text-[10px] text-[var(--text-secondary)]">
          {source.file_name}
        </span>
      </button>

      {isOpen && (
        <div
          ref={popoverRef}
          role="dialog"
          aria-label={`Citation details for Source ${source.source_index}`}
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 sm:w-80 p-3 bg-[var(--surface-primary)] border border-[var(--border-subtle)] rounded-md shadow-lg text-xs z-50 text-[var(--text-primary)] font-sans transition-colors duration-150"
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[var(--border-subtle)]">
            <div className="flex items-center gap-1.5 overflow-hidden">
              <FileText className="w-3.5 h-3.5 text-[var(--accent-primary)] shrink-0" aria-hidden="true" />
              <span className="font-mono text-[11px] font-semibold text-[var(--text-primary)] truncate">
                Source {source.source_index}
              </span>
            </div>
            <button
              onClick={() => {
                setIsOpen(false);
                triggerRef.current?.focus();
              }}
              aria-label="Close citation details"
              className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] p-1 rounded hover:bg-[var(--surface-secondary)] transition-colors"
            >
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>

          {/* Reference Meta Grid */}
          <div className="space-y-1.5 text-[11px] font-mono text-[var(--text-secondary)]">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[var(--text-muted)]">DOCUMENT:</span>
              <span className="text-[var(--text-primary)] truncate text-right font-sans text-xs font-medium">
                {source.file_name}
              </span>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[var(--text-muted)]">PAGE:</span>
              <span className="text-[var(--text-primary)]">p. {source.page_number}</span>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[var(--text-muted)]">RELEVANCE:</span>
              <span className="text-[var(--accent-primary)] font-semibold">{scorePercentage}%</span>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[var(--text-muted)]">DOC UUID:</span>
              <span className="text-[var(--text-secondary)] truncate max-w-[140px]">
                {source.document_id}
              </span>
            </div>
          </div>
        </div>
      )}
    </span>
  );
};

interface FormattedTextProps {
  text: string;
  sources: CitationSource[];
}

export const FormattedMessageText: React.FC<FormattedTextProps> = ({ text, sources }) => {
  // Regex matches pattern like [Source 1], [Source 2], etc.
  const parts = text.split(/(\[Source\s+\d+\])/g);

  return (
    <span className="leading-relaxed">
      {parts.map((part, idx) => {
        const match = part.match(/\[Source\s+(\d+)\]/);
        if (match) {
          const sourceIdx = parseInt(match[1], 10);
          return <CitationBadge key={idx} sourceIndex={sourceIdx} sources={sources} />;
        }
        return <span key={idx}>{part}</span>;
      })}
    </span>
  );
};
