/**
 * Chat API service.
 * Handles chat session creation and message turn submission.
 * Contracts:
 * - POST /api/v1/chat/sessions
 * - POST /api/v1/chat/sessions/{session_id}/messages
 *
 * Safety Notice:
 * The returned safety_state (CLEAR, CONCERNING, EMERGENCY) is authoritative from backend.
 * The client must never calculate or override safety states.
 */

import { apiRequest } from './apiClient';
import type {
  ChatSessionCreate,
  ChatSessionResponse,
  ChatMessageCreate,
  ChatTurnResponse,
} from '../types/ai';

export const chatService = {
  /**
   * Create a new chat session for maternal decision support.
   * Calls POST /api/v1/chat/sessions with Bearer token.
   */
  async createSession(
    payload: ChatSessionCreate = {},
    token?: string | null
  ): Promise<ChatSessionResponse> {
    return apiRequest<ChatSessionResponse>('/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },

  /**
   * Submit a user message to a chat session and receive assistant response with safety evaluation.
   * Calls POST /api/v1/chat/sessions/{session_id}/messages with Bearer token.
   */
  async sendMessage(
    sessionId: string,
    payload: ChatMessageCreate,
    token?: string | null
  ): Promise<ChatTurnResponse> {
    return apiRequest<ChatTurnResponse>(`/chat/sessions/${sessionId}/messages`, {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },
};
