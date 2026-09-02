'use client';

import React from 'react';
import { MessageSquare, Files, LogOut, Sun, Moon } from 'lucide-react';
import { useTheme } from '@/lib/ThemeContext';

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
  const { theme, toggleTheme } = useTheme();

  return (
    <header className="w-full bg-[var(--surface-primary)] border-b border-[var(--border-subtle)] px-4 md:px-6 py-2.5 flex items-center justify-between sticky top-0 z-40 transition-colors duration-150">
      {/* Brand & Subtitle (Left) */}
      <div className="flex items-center space-x-3">
        <div className="flex flex-col">
          <span className="font-semibold text-sm tracking-wider text-[var(--text-primary)] font-mono">
            ATLAS
          </span>
          <span className="text-[11px] text-[var(--text-secondary)] tracking-tight">
            Enterprise Knowledge Assistant
          </span>
        </div>
      </div>

      {/* Main Tab Navigation (Center) */}
      {isAuthenticated && (
        <nav 
          aria-label="Main Navigation" 
          className="flex items-center space-x-1 bg-[var(--bg-workspace)] p-1 border border-[var(--border-subtle)] rounded-md"
        >
          <button
            onClick={() => setActiveTab('chat')}
            aria-current={activeTab === 'chat' ? 'page' : undefined}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              activeTab === 'chat'
                ? 'bg-[var(--surface-secondary)] text-[var(--text-primary)] border border-[var(--border-subtle)] shadow-xs'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-primary)]'
            }`}
          >
            <MessageSquare className="w-3.5 h-3.5 text-[var(--accent-primary)]" aria-hidden="true" />
            <span>Chat</span>
          </button>
          
          <button
            onClick={() => setActiveTab('documents')}
            aria-current={activeTab === 'documents' ? 'page' : undefined}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded transition-colors ${
              activeTab === 'documents'
                ? 'bg-[var(--surface-secondary)] text-[var(--text-primary)] border border-[var(--border-subtle)] shadow-xs'
                : 'text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-primary)]'
            }`}
          >
            <Files className="w-3.5 h-3.5 text-[var(--accent-primary)]" aria-hidden="true" />
            <span>Documents</span>
          </button>
        </nav>
      )}

      {/* Status, Theme Toggle & User Controls (Right) */}
      <div className="flex items-center space-x-3">
        {/* System Status Indicator */}
        {isAuthenticated && (
          <div
            className="flex items-center gap-1.5 px-2.5 py-1 text-[11px] font-mono rounded bg-[var(--surface-secondary)] border border-[var(--border-subtle)] text-[var(--text-secondary)]"
            role="status"
            aria-label={`System Status: ${systemStatus}`}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full ${
                systemStatus === 'ready'
                  ? 'bg-[var(--status-ready)]'
                  : 'bg-[var(--status-processing)] animate-pulse'
              }`}
              aria-hidden="true"
            />
            <span className="uppercase text-[10px] text-[var(--text-primary)]">
              {systemStatus === 'ready' ? 'Ready' : 'Indexing'}
            </span>
          </div>
        )}

        {/* Minimal Theme Switcher */}
        <button
          onClick={toggleTheme}
          aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
          className="p-1.5 rounded text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--surface-secondary)] border border-transparent hover:border-[var(--border-subtle)] transition-colors"
        >
          {theme === 'dark' ? (
            <Sun className="w-3.5 h-3.5 text-[var(--text-secondary)]" aria-hidden="true" />
          ) : (
            <Moon className="w-3.5 h-3.5 text-[var(--text-secondary)]" aria-hidden="true" />
          )}
        </button>

        {/* Logout Control */}
        {isAuthenticated && (
          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] px-2.5 py-1.5 rounded hover:bg-[var(--surface-secondary)] transition-colors focus:ring-1 focus:ring-[var(--accent-primary)]"
            aria-label="Log out of ATLAS"
          >
            <LogOut className="w-3.5 h-3.5" aria-hidden="true" />
            <span className="hidden sm:inline">Logout</span>
          </button>
        )}
      </div>
    </header>
  );
};
