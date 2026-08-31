import { getApiBaseUrl, getStoredToken } from './client';
import { ChatRequest, CitationSource } from './types';

export interface StreamChatCallbacks {
  onSources?: (sources: CitationSource[]) => void;
  onToken?: (token: string) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

export async function streamChatCompletion(
  payload: ChatRequest,
  callbacks: StreamChatCallbacks
): Promise<void> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${getApiBaseUrl()}/chat/completions`, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Chat API error (${response.status}): ${errorText}`);
    }

    if (!response.body) {
      throw new Error('ReadableStream not supported by browser/response.');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');
    let buffer = '';

    while (true) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep partial line in buffer

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          const jsonStr = trimmed.slice(6);
          try {
            const parsed = JSON.parse(jsonStr);
            if (parsed.event === 'sources' && Array.isArray(parsed.data)) {
              callbacks.onSources?.(parsed.data);
            } else if (parsed.event === 'token' && typeof parsed.data === 'string') {
              callbacks.onToken?.(parsed.data);
            }
          } catch (err) {
            console.error('Failed to parse SSE payload:', err, jsonStr);
          }
        }
      }
    }

    if (buffer.trim().startsWith('data: ')) {
      const jsonStr = buffer.trim().slice(6);
      try {
        const parsed = JSON.parse(jsonStr);
        if (parsed.event === 'sources' && Array.isArray(parsed.data)) {
          callbacks.onSources?.(parsed.data);
        } else if (parsed.event === 'token' && typeof parsed.data === 'string') {
          callbacks.onToken?.(parsed.data);
        }
      } catch {
        // Ignore partial trailing data error
      }
    }

    callbacks.onComplete?.();
  } catch (error) {
    callbacks.onError?.(error instanceof Error ? error : new Error(String(error)));
  }
}
