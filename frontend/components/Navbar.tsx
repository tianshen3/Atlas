'use client';

import React from 'react';

interface NavbarProps {
  isAuthenticated: boolean;
  onLogout: () => void;
  activeTab: 'documents' | 'chat';
  setActiveTab: (tab: 'documents' | 'chat') => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  isAuthenticated,
  onLogout,
  activeTab,
  setActiveTab,
}) => {
  return (
    <header className="w-full bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center space-x-8">
        <h1 className="text-xl font-bold tracking-tight text-gray-900">ATLAS</h1>
        
        {isAuthenticated && (
          <nav className="flex space-x-4">
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'documents'
                  ? 'bg-gray-100 text-gray-900 border border-gray-300'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              Documents
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                activeTab === 'chat'
                  ? 'bg-gray-100 text-gray-900 border border-gray-300'
                  : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              Chat
            </button>
          </nav>
        )}
      </div>

      {isAuthenticated && (
        <div className="flex items-center space-x-4">
          <button
            onClick={onLogout}
            className="text-xs text-red-600 hover:text-red-800 font-medium px-2 py-1 rounded hover:bg-red-50"
          >
            Logout
          </button>
        </div>
      )}
    </header>
  );
};
