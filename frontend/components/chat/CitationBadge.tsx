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
      <span className="inline-block font-mono text-xs text-[#89938C] px-1">
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
            ? 'bg-[#1C2420] text-[#E4E8E4] border-[#6F9B82]'
            : 'bg-[#151A17] text-[#89938C] hover:text-[#E4E8E4] border-[#242A26] hover:border-[#6F9B82]'
        }`}
      >
        <span className="text-[#6F9B82] font-semibold">[{source.source_index}]</span>
        <span className="max-w-[120px] truncate hidden sm:inline text-[10px] text-[#89938C]">
          {source.file_name}
        </span>
      </button>

      {isOpen && (
        <div
          ref={popoverRef}
          role="dialog"
          aria-label={`Citation details for Source ${source.source_index}`}
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-72 sm:w-80 p-3 bg-[#151A17] border border-[#242A26] rounded-md shadow-2xl text-xs z-50 text-[#E4E8E4] font-sans"
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-2 mb-2 border-b border-[#242A26]">
            <div className="flex items-center gap-1.5 overflow-hidden">
              <FileText className="w-3.5 h-3.5 text-[#6F9B82] shrink-0" aria-hidden="true" />
              <span className="font-mono text-[11px] font-semibold text-[#E4E8E4] truncate">
                Source {source.source_index}
              </span>
            </div>
            <button
              onClick={() => {
                setIsOpen(false);
                triggerRef.current?.focus();
              }}
              aria-label="Close citation details"
              className="text-[#89938C] hover:text-[#E4E8E4] p-1 rounded hover:bg-[#1C221F]"
            >
              <X className="w-3.5 h-3.5" aria-hidden="true" />
            </button>
          </div>

          {/* Reference Meta Grid */}
          <div className="space-y-1.5 text-[11px] font-mono text-[#89938C]">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[#626B65]">DOCUMENT:</span>
              <span className="text-[#E4E8E4] truncate text-right font-sans text-xs">
                {source.file_name}
              </span>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[#626B65]">PAGE:</span>
              <span className="text-[#E4E8E4]">p. {source.page_number}</span>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[#626B65]">RELEVANCE:</span>
              <span className="text-[#6F9B82] font-semibold">{scorePercentage}%</span>
            </div>
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-[#626B65]">DOC UUID:</span>
              <span className="text-[#89938C] truncate max-w-[140px]">
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
