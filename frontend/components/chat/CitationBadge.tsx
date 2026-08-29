'use client';

import React, { useState } from 'react';
import { CitationSource } from '@/lib/api/types';

interface CitationBadgeProps {
  sourceIndex: number;
  sources: CitationSource[];
}

export const CitationBadge: React.FC<CitationBadgeProps> = ({ sourceIndex, sources }) => {
  const [showPopover, setShowPopover] = useState(false);
  const source = sources.find((s) => s.source_index === sourceIndex);

  if (!source) {
    return <span className="inline-block font-mono text-xs text-gray-500">[{sourceIndex}]</span>;
  }

  return (
    <span className="relative inline-block mx-0.5">
      <button
        onClick={() => setShowPopover(!showPopover)}
        onMouseEnter={() => setShowPopover(true)}
        onMouseLeave={() => setShowPopover(false)}
        className="inline-flex items-center px-1.5 py-0.5 text-xs font-mono bg-blue-50 text-blue-700 hover:bg-blue-100 border border-blue-200 rounded cursor-pointer transition-colors"
      >
        [{source.file_name} p.{source.page_number}]
      </button>

      {showPopover && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-white border border-gray-200 rounded-md shadow-lg text-xs z-50 text-gray-800">
          <div className="font-semibold text-gray-900 mb-1 border-b border-gray-100 pb-1">
            Source {source.source_index}: {source.file_name}
          </div>
          <div className="space-y-1 text-gray-600 font-mono text-[11px]">
            <div>Document ID: {source.document_id.slice(0, 8)}...</div>
            <div>Page: {source.page_number}</div>
            <div>Relevance Score: {(source.score * 100).toFixed(1)}%</div>
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
    <span>
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
