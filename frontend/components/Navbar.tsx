'use client';

import React from 'react';
import { MessageSquare, Files, LogOut } from 'lucide-react';

interface NavbarProps {
  isAuthenticated: boolean;
  onLogout: () => void;
  activeTab: 'documents' | 'chat';
  setActiveTab: (tab: 'documents' | 'chat') => void;
  systemStatus?: 'ready' | 'processing' | 'indexing';
}

export const Navbar: React.FC<NavbarProps> = ({
  isAuthenticated,
  onLogout,
  activeTab,
  setActiveTab,
  systemStatus = 'ready',
}) => {
  return (
    <header className="w-full bg-[#111513] border-b border-[#242A26] px-4 md:px-6 py-3 flex items-center justify-between sticky top-0 z-40">
      {/* Brand & Subtitle */}
      <div className="flex items-center space-x-3">
        <div className="flex flex-col">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm tracking-wider text-[#E4E8E4] font-mono">
              ATLAS
            </span>
            <span className="hidden sm:inline-block text-[10px] uppercase font-mono px-1.5 py-0.2 text-[#89938C] bg-[#151A17] border border-[#242A26] rounded">
              v1.0
            </span>
          </div>
          <span className="text-[11px] text-[#89938C] tracking-tight">
            Enterprise Knowledge Assistant
          </span>
        </div>
      </div>

      {/* Main Tab Navigation */}
      {isAuthenticated && (
        <nav aria-label="Main Navigation" className="flex items-center space-x-1 bg-[#0B0E0D] p-1 border border-[#242A26] rounded-md">
          <button
            onClick={() => setActiveTab('chat')}
            aria-current={activeTab === 'chat' ? 'page' : undefined}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              activeTab === 'chat'
                ? 'bg-[#151A17] text-[#E4E8E4] border border-[#242A26] shadow-sm'
                : 'text-[#89938C] hover:text-[#E4E8E4] hover:bg-[#111513]'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5 text-[#6F9B82]" aria-hidden="true" />
            <span>Chat</span>
          </button>
          
          <button
            onClick={() => setActiveTab('documents')}
            aria-current={activeTab === 'documents' ? 'page' : undefined}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              activeTab === 'documents'
                ? 'bg-[#151A17] text-[#E4E8E4] border border-[#242A26] shadow-sm'
                : 'text-[#89938C] hover:text-[#E4E8E4] hover:bg-[#111513]'
            }`}
          >
            <Files className="w-3.5 h-3.5 text-[#6F9B82]" aria-hidden="true" />
            <span>Documents</span>
          </button>
        </nav>
      )}

      {/* Status & User Controls */}
      <div className="flex items-center space-x-4">
        {isAuthenticated && (
          <>
            {/* System Status Pill */}
            <div
              className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono rounded bg-[#151A17] border border-[#242A26] text-[#89938C]"
              role="status"
              aria-label={`System Status: ${systemStatus}`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  systemStatus === 'ready'
                    ? 'bg-[#6F9B82]'
                    : 'bg-[#89938C] animate-pulse'
                }`}
                aria-hidden="true"
              />
              <span className="uppercase text-[10px] text-[#E4E8E4]">
                {systemStatus === 'ready' ? 'Ready' : 'Indexing'}
              </span>
            </div>

            {/* Logout Button */}
            <button
              onClick={onLogout}
              className="flex items-center gap-1.5 text-xs text-[#89938C] hover:text-[#E4E8E4] px-2.5 py-1.5 rounded hover:bg-[#151A17] transition-colors focus:ring-1 focus:ring-[#6F9B82]"
              aria-label="Log out of ATLAS"
            >
              <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </>
        )}
      </div>
    </header>
  );
};
