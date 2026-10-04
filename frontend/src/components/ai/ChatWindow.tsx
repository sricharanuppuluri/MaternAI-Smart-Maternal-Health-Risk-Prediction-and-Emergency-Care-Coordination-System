/**
 * Chat Window component.
 *
 * Coordinates:
 * - Session initialization via POST /api/v1/chat/sessions
 * - Message turn submission via POST /api/v1/chat/sessions/{session_id}/messages
 * - Distinct USER and ASSISTANT message rendering
 * - Authoritative SafetyStatus presentation
 * - Loading, error, empty, and retry states
 * - Mobile-responsive and keyboard accessible (Enter to submit)
 */

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Card, Button, AlertBanner } from '../common';
import { ChatMessageItem } from './ChatMessageItem';
import { chatService } from '../../services/chatService';
import type {
  ChatSessionResponse,
  MessageItem,
  SafetyStatus,
} from '../../types/ai';

export interface ChatMessageEntry {
  message: MessageItem;
  safetyState?: SafetyStatus | null;
  safetyEvents?: string[];
  disclaimer?: string | null;
}

export interface ChatWindowProps {
  motherId?: string;
  defaultTitle?: string;
  className?: string;
}

export const ChatWindow: React.FC<ChatWindowProps> = ({
  motherId,
  defaultTitle = 'Maternal Care & Guidance',
  className = '',
}) => {
  const [session, setSession] = useState<ChatSessionResponse | null>(null);
  const [messages, setMessages] = useState<ChatMessageEntry[]>([]);
  const [inputContent, setInputContent] = useState<string>('');
  const [isInitializing, setIsInitializing] = useState<boolean>(true);
  const [isSending, setIsSending] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const [sessionKey, setSessionKey] = useState<number>(0);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isSending]);

  // Initialize a fresh chat session
  useEffect(() => {
    let isMounted = true;

    chatService
      .createSession({
        mother_id: motherId,
        title: defaultTitle,
        language: 'en',
      })
      .then((newSession) => {
        if (isMounted) {
          setSession(newSession);
          setMessages([]);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (isMounted) {
          const msg = err instanceof Error ? err.message : 'Failed to initialize chat session.';
          setError(msg);
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsInitializing(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [motherId, defaultTitle, sessionKey]);

  const handleNewSession = useCallback(() => {
    setIsInitializing(true);
    setError(null);
    setSessionKey((prev) => prev + 1);
  }, []);

  const handleSendMessage = async (textToSend?: string) => {
    const text = textToSend ?? inputContent.trim();
    if (!text || isSending) return;

    if (!session?.id) {
      setError('No active chat session. Please initialize a new session.');
      return;
    }

    setIsSending(true);
    setError(null);
    setLastFailedMessage(null);
    if (!textToSend) {
      setInputContent('');
    }

    try {
      const turn = await chatService.sendMessage(session.id, {
        content: text,
        language: 'en',
      });

      // Append user message and assistant message to thread
      setMessages((prev) => [
        ...prev,
        {
          message: turn.user_message,
        },
        {
          message: turn.assistant_message,
          safetyState: turn.safety_state,
          safetyEvents: turn.safety_events,
          disclaimer: turn.disclaimer,
        },
      ]);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to send message to assistant.';
      setError(msg);
      setLastFailedMessage(text);
    } finally {
      setIsSending(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <Card
      title="MaternAI Care Assistant"
      subtitle={session ? `Session: ${session.title || 'Maternal Support'} (${session.language})` : 'Connecting to care service...'}
      className={`chat-window-card flex flex-col h-[600px] max-h-[80vh] ${className}`}
    >
      {/* Session Controls / Header Actions */}
      <div className="flex items-center justify-between pb-2 mb-2 border-b text-xs text-muted">
        <span>
          {session ? `Session ID: ${session.id.slice(0, 8)}...` : 'No active session'}
        </span>
        <Button
          variant="outline"
          size="sm"
          onClick={handleNewSession}
          disabled={isInitializing || isSending}
        >
          {isInitializing ? 'Creating Session...' : '+ New Session'}
        </Button>
      </div>

      {/* Error Alert with Retry */}
      {error && (
        <div className="mb-3">
          <AlertBanner type="danger" message={error} onDismiss={() => setError(null)} />
          {lastFailedMessage && (
            <div className="mt-1">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSendMessage(lastFailedMessage)}
                disabled={isSending}
              >
                Retry Sending Message
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Messages Scroll Area */}
      <div
        className="chat-messages-viewport flex-1 overflow-y-auto space-y-3 p-2 bg-neutral-light rounded border min-h-[250px]"
        role="log"
        aria-live="polite"
        aria-label="Conversation message history"
      >
        {isInitializing && messages.length === 0 ? (
          <div className="p-8 text-center text-muted">
            <div className="spinner mx-auto mb-2" />
            <p>Initializing secure care conversation...</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="empty-chat-state p-8 text-center text-muted space-y-2">
            <p className="font-semibold text-foreground">Welcome to MaternAI Decision-Support Chat</p>
            <p className="text-xs max-w-md mx-auto">
              Ask questions regarding prenatal tracking, checkup preparation, or care coordination.
              All messages are evaluated through the authoritative safety engine.
            </p>
          </div>
        ) : (
          messages.map((entry, index) => (
            <ChatMessageItem
              key={`${entry.message.id}-${index}`}
              message={entry.message}
              safetyState={entry.safetyState}
              safetyEvents={entry.safetyEvents}
              disclaimer={entry.disclaimer}
            />
          ))
        )}

        {/* Loading Spinner for pending assistant reply */}
        {isSending && (
          <div className="flex items-start text-xs text-muted p-2 bg-white rounded border max-w-xs shadow-sm">
            <div className="spinner mr-2" />
            <span>Evaluating safety boundary & generating guidance...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Message Input & Send Bar */}
      <div className="chat-input-bar mt-3 pt-2 border-t flex items-center gap-2">
        <input
          id="chat-message-input"
          type="text"
          placeholder="Type your question or symptom observation..."
          value={inputContent}
          onChange={(e) => setInputContent(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={!session || isSending || isInitializing}
          className="form-input flex-1 text-sm p-2 border rounded"
          aria-label="Chat message input"
        />
        <Button
          variant="primary"
          onClick={() => handleSendMessage()}
          disabled={!session || isSending || isInitializing || !inputContent.trim()}
          isLoading={isSending}
        >
          Send
        </Button>
      </div>
    </Card>
  );
};
