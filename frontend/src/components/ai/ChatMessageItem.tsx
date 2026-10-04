/**
 * Chat Message Item component.
 *
 * Renders individual user and assistant messages:
 * - Distinct USER and ASSISTANT layout and styling
 * - Authoritative SafetyStatusBadge on assistant messages
 * - Safety events list when deterministic rules trigger
 * - Mandatory clinical decision-support disclaimer
 */

import React from 'react';
import type { MessageItem, SafetyStatus } from '../../types/ai';
import { SafetyStatusBadge } from './SafetyStatusBadge';
import { formatDate } from '../../utils/formatters';

export interface ChatMessageItemProps {
  message: MessageItem;
  safetyState?: SafetyStatus | null;
  safetyEvents?: string[];
  disclaimer?: string | null;
  className?: string;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  safetyState,
  safetyEvents = [],
  disclaimer,
  className = '',
}) => {
  const isUser = message.sender_role === 'USER';

  return (
    <div
      className={`chat-message-row flex flex-col ${
        isUser ? 'items-end' : 'items-start'
      } ${className}`}
      role="article"
      aria-label={`${isUser ? 'User message' : 'Assistant message'}`}
    >
      <div
        className={`message-bubble max-w-xl p-3 rounded-lg shadow-sm ${
          isUser
            ? 'bg-primary text-white rounded-br-none'
            : 'bg-white border text-foreground rounded-bl-none'
        }`}
      >
        {/* Header / Meta */}
        <div className="message-header flex items-center justify-between gap-3 mb-1 text-xs opacity-75">
          <span className="font-semibold uppercase tracking-wider">
            {isUser ? 'You' : 'MaternAI Assistant'}
          </span>
          <span>{formatDate(message.created_at)}</span>
        </div>

        {/* Content */}
        <p className="message-content text-sm whitespace-pre-wrap m-0 leading-relaxed">
          {message.content}
        </p>

        {/* Assistant Safety Presentation */}
        {!isUser && safetyState && (
          <div className="assistant-safety-block mt-3 pt-2 border-t space-y-2">
            <div className="flex items-center gap-2">
              <SafetyStatusBadge safetyState={safetyState} />
            </div>

            {/* Deterministic Safety Events */}
            {safetyEvents.length > 0 && (
              <div className="safety-events-box p-2 bg-warning-light border border-warning rounded text-xs">
                <span className="font-semibold text-warning-dark block mb-1">
                  Deterministic Safety Rule Triggered:
                </span>
                <ul className="list-disc list-inside m-0 space-y-0.5">
                  {safetyEvents.map((evt, idx) => (
                    <li key={idx}>{evt}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Mandatory Decision Support Disclaimer */}
            {disclaimer && (
              <p className="chat-disclaimer text-[11px] text-muted italic mt-2 m-0 border-t pt-1">
                {disclaimer}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
