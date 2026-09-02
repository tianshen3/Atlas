'use client';

import React, { useState } from 'react';
import { login } from '@/lib/api/auth';
import { Lock, Mail, AlertCircle, ArrowRight } from 'lucide-react';

interface LoginFormProps {
  onLoginSuccess: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onLoginSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      await login({ email, password });
      onLoginSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Authentication failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-sm bg-[var(--surface-primary)] border border-[var(--border-subtle)] rounded-md p-6 shadow-sm transition-colors duration-150">
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="font-mono text-xs text-[var(--accent-primary)] uppercase tracking-wider font-semibold">
            ATLAS GATEWAY
          </span>
        </div>
        <h2 className="text-base font-semibold text-[var(--text-primary)] tracking-tight">
          Sign In to Knowledge Base
        </h2>
        <p className="text-xs text-[var(--text-secondary)] mt-1">
          Access enterprise documents and grounded hybrid RAG assistant.
        </p>
      </div>

      {/* Error Callout */}
      {error && (
        <div
          role="alert"
          aria-live="assertive"
          className="mb-5 p-3 bg-[var(--surface-secondary)] border border-[var(--status-failed)] text-[var(--status-failed)] text-xs rounded flex items-start gap-2.5"
        >
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[var(--status-failed)]" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4" noValidate>
        <div>
          <label
            htmlFor="login-email"
            className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5 font-mono"
          >
            EMAIL ADDRESS
          </label>
          <div className="relative">
            <Mail
              className="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
              aria-hidden="true"
            />
            <input
              id="login-email"
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full bg-[var(--surface-secondary)] border border-[var(--border-subtle)] rounded px-3 py-2 pl-9 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--accent-primary)] focus:bg-[var(--surface-primary)] transition-colors"
              placeholder="user@atlas.io"
            />
          </div>
        </div>

        <div>
          <label
            htmlFor="login-password"
            className="block text-xs font-medium text-[var(--text-secondary)] mb-1.5 font-mono"
          >
            PASSWORD
          </label>
          <div className="relative">
            <Lock
              className="w-4 h-4 text-[var(--text-muted)] absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none"
              aria-hidden="true"
            />
            <input
              id="login-password"
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full bg-[var(--surface-secondary)] border border-[var(--border-subtle)] rounded px-3 py-2 pl-9 text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:border-[var(--accent-primary)] focus:bg-[var(--surface-primary)] transition-colors"
              placeholder="••••••••"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full mt-2 py-2 px-4 bg-[var(--surface-secondary)] hover:bg-[var(--surface-tertiary)] text-[var(--text-primary)] border border-[var(--border-subtle)] hover:border-[var(--accent-primary)] rounded text-xs font-mono uppercase tracking-wider font-medium flex items-center justify-center gap-2 transition-all disabled:opacity-50 min-touch-target"
        >
          {loading ? (
            <span>Authenticating...</span>
          ) : (
            <>
              <span>Authenticate</span>
              <ArrowRight className="w-3.5 h-3.5 text-[var(--accent-primary)]" aria-hidden="true" />
            </>
          )}
        </button>
      </form>

      {/* Subtle Hint */}
      <div className="mt-5 pt-4 border-t border-[var(--border-subtle)] text-center">
        <span className="text-[11px] text-[var(--text-muted)] font-mono">
          Default admin: admin@atlas.io
        </span>
      </div>
    </div>
  );
};
