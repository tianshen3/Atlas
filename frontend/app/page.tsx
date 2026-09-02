'use client';

import React, { useState, useEffect } from 'react';
import { Navbar } from '@/components/Navbar';
import { LoginForm } from '@/components/auth/LoginForm';
import { DocumentManager } from '@/components/documents/DocumentManager';
import { ChatWindow } from '@/components/chat/ChatWindow';
import { getStoredToken } from '@/lib/api/client';
import { logout } from '@/lib/api/auth';

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'chat' | 'documents'>('chat');
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  useEffect(() => {
    // Asynchronously resolve stored authentication state on client mount
    Promise.resolve().then(() => {
      const token = getStoredToken();
      if (token) {
        setIsAuthenticated(true);
      }
      setIsInitializing(false);
    });
  }, []);

  const handleLoginSuccess = () => {
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    logout();
    setIsAuthenticated(false);
  };

  if (isInitializing) {
    return (
      <div 
        role="status"
        aria-live="polite"
        className="min-h-screen bg-[#0B0E0D] text-[#89938C] flex flex-col items-center justify-center font-mono text-xs gap-3"
      >
        <span className="w-2 h-2 rounded-full bg-[#6F9B82] animate-pulse" aria-hidden="true" />
        <span>INITIALIZING ATLAS WORKSPACE...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0E0D] text-[#E4E8E4] flex flex-col font-sans technical-grid-bg">
      <Navbar
        isAuthenticated={isAuthenticated}
        onLogout={handleLogout}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main 
        id="main-content"
        className="flex-1 p-4 md:p-6 flex flex-col items-center"
      >
        {!isAuthenticated ? (
          <div className="w-full flex-1 flex flex-col items-center justify-center py-12">
            <LoginForm onLoginSuccess={handleLoginSuccess} />
          </div>
        ) : activeTab === 'chat' ? (
          <ChatWindow />
        ) : (
          <DocumentManager />
        )}
      </main>
    </div>
  );
}
