/**
 * Chat Message Item component.
 *
 * Renders individual user and assistant messages:
 * - Distinct USER and ASSISTANT layout and styling
 * - Authoritative SafetyStatusBadge on assistant messages
 * - Safety events list when deterministic rules trigger
 * - Mandatory clinical decision-support disclaimer
 * - Optional Text-to-Speech (TTS) listening action
 */

import React from 'react';
import type { MessageItem, SafetyStatus } from '../../types/ai';
import type { VoiceSynthesisResponse } from '../../types/voice';
import { SafetyStatusBadge } from './SafetyStatusBadge';
import { VoiceAudioPlayer } from '../voice/VoiceAudioPlayer';
import { Button } from '../common';
import { formatDate } from '../../utils/formatters';

export interface ChatMessageItemProps {
  message: MessageItem;
  safetyState?: SafetyStatus | null;
  safetyEvents?: string[];
  disclaimer?: string | null;
  onSynthesize?: (text: string) => void;
  isSynthesizing?: boolean;
  synthesizedAudio?: VoiceSynthesisResponse | null;
  className?: string;
}

export const ChatMessageItem: React.FC<ChatMessageItemProps> = ({
  message,
  safetyState,
  safetyEvents = [],
  disclaimer,
  onSynthesize,
  isSynthesizing = false,
  synthesizedAudio = null,
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

        {/* Assistant Audio (TTS) Section */}
        {!isUser && onSynthesize && (
          <div className="assistant-voice-tts mt-2 pt-2 border-t space-y-2">
            {!synthesizedAudio ? (
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onSynthesize(message.content)}
                  disabled={isSynthesizing}
                  isLoading={isSynthesizing}
                  className="text-[11px] py-0.5 px-2"
                  aria-label="Listen to assistant message via Text-to-Speech"
                >
                  {isSynthesizing ? 'Synthesizing...' : 'Listen (TTS)'}
                </Button>
              </div>
            ) : (
              <VoiceAudioPlayer
                audioContent={synthesizedAudio.audio_content}
                mimeType={synthesizedAudio.mime_type}
                durationSeconds={synthesizedAudio.duration_seconds}
                label="Spoken Guidance"
                autoPlay={false}
              />
            )}
          </div>
        )}

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
