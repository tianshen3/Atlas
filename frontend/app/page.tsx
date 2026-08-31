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
  const [activeTab, setActiveTab] = useState<'documents' | 'chat'>('documents');
  const [isInitializing, setIsInitializing] = useState<boolean>(true);

  useEffect(() => {
    const token = getStoredToken();
    if (token) {
      setIsAuthenticated(true);
    }
    setIsInitializing(false);
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
      <div className="min-h-screen bg-gray-50 flex items-center justify-center text-xs text-gray-500 font-mono">
        Initializing ATLAS Client...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 flex flex-col font-sans">
      <Navbar
        isAuthenticated={isAuthenticated}
        onLogout={handleLogout}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
      />

      <main className="flex-1 p-6 md:p-8 flex flex-col items-center">
        {!isAuthenticated ? (
          <div className="w-full flex flex-col items-center justify-center my-auto py-12">
            <LoginForm onLoginSuccess={handleLoginSuccess} />
          </div>
        ) : activeTab === 'documents' ? (
          <DocumentManager />
        ) : (
          <ChatWindow />
        )}
      </main>
    </div>
  );
}
