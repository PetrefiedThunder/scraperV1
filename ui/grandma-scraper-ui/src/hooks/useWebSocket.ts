/**
 * WebSocket hook for real-time scraping progress updates
 */

import { useEffect, useRef, useState, useCallback } from 'react';

interface ProgressUpdate {
  type: 'progress' | 'completion';
  result_id: string;
  status: string;
  progress?: number;
  items_scraped?: number;
  pages_scraped?: number;
  current_url?: string;
  message?: string;
  total_items?: number;
  total_pages?: number;
  duration_seconds?: number;
  error_message?: string;
  timestamp: string;
}

interface UseWebSocketOptions {
  resultId?: string;
  onProgress?: (update: ProgressUpdate) => void;
  onCompletion?: (update: ProgressUpdate) => void;
  onError?: (error: Event) => void;
  enabled?: boolean;
}

const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/api/v1';

export function useWebSocket(options: UseWebSocketOptions) {
  const {
    resultId,
    onProgress,
    onCompletion,
    onError,
    enabled = true,
  } = options;

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<ProgressUpdate | null>(null);

  const connect = useCallback(() => {
    if (!enabled) return;

    const url = resultId
      ? `${WS_BASE_URL}/ws/progress/${resultId}`
      : `${WS_BASE_URL}/ws/progress`;

    const ws = new WebSocket(url);

    ws.onopen = () => {
      console.log('WebSocket connected:', url);
      setIsConnected(true);

      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);

      ws.addEventListener('close', () => {
        clearInterval(pingInterval);
      });
    };

    ws.onmessage = (event) => {
      try {
        // Handle pong responses
        if (event.data === 'pong') {
          return;
        }

        const update: ProgressUpdate = JSON.parse(event.data);
        setLastUpdate(update);

        // Call appropriate callback based on update type
        if (update.type === 'progress' && onProgress) {
          onProgress(update);
        } else if (update.type === 'completion' && onCompletion) {
          onCompletion(update);
        }
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      if (onError) {
        onError(error);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);

      // Attempt to reconnect after 3 seconds
      if (enabled) {
        reconnectTimeoutRef.current = window.setTimeout(() => {
          console.log('Attempting to reconnect WebSocket...');
          connect();
        }, 3000);
      }
    };

    wsRef.current = ws;
  }, [resultId, enabled, onProgress, onCompletion, onError]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setIsConnected(false);
  }, []);

  // Connect on mount and when dependencies change
  useEffect(() => {
    if (enabled) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [connect, disconnect, enabled]);

  return {
    isConnected,
    lastUpdate,
    disconnect,
    reconnect: connect,
  };
}
