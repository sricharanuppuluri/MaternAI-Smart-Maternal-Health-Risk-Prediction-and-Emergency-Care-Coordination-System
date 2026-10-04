/**
 * Phase 7 — Voice Processing API service.
 * Handles Speech-to-Text transcription, explicit user confirmation, and Text-to-Speech synthesis.
 *
 * Contracts:
 * - POST /api/v1/voice/transcribe
 * - POST /api/v1/voice/confirm
 * - POST /api/v1/voice/synthesize
 *
 * Clinical & Safety Notice:
 * - Clinical Observation Confirmation Boundary: Raw transcribed speech is NEVER automatically
 *   persisted into clinical records or care sessions until explicit user confirmation.
 * - The backend SafetyEngine evaluates confirmed messages and returns the authoritative safety_state.
 *   The client must never calculate, infer, or override safety states or maternal risk.
 */

import { apiRequest } from './apiClient';
import type {
  VoiceTranscriptionRequest,
  VoiceTranscriptionResponse,
  VoiceConfirmationRequest,
  VoiceConfirmationResponse,
  VoiceSynthesisRequest,
  VoiceSynthesisResponse,
} from '../types/voice';

export const voiceService = {
  /**
   * Transcribe base64-encoded audio bytes into text.
   * Calls POST /api/v1/voice/transcribe with Bearer token.
   * Note: This does NOT persist clinical data or chat messages.
   */
  async transcribeAudio(
    payload: VoiceTranscriptionRequest,
    token?: string | null
  ): Promise<VoiceTranscriptionResponse> {
    return apiRequest<VoiceTranscriptionResponse>('/voice/transcribe', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },

  /**
   * Explicitly confirm transcribed text and route it into the authoritative chat session and SafetyEngine.
   * Calls POST /api/v1/voice/confirm with Bearer token.
   */
  async confirmVoiceTranscript(
    payload: VoiceConfirmationRequest,
    token?: string | null
  ): Promise<VoiceConfirmationResponse> {
    return apiRequest<VoiceConfirmationResponse>('/voice/confirm', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },

  /**
   * Synthesize text into speech base64 audio bytes for playback UI.
   * Calls POST /api/v1/voice/synthesize with Bearer token.
   */
  async synthesizeSpeech(
    payload: VoiceSynthesisRequest,
    token?: string | null
  ): Promise<VoiceSynthesisResponse> {
    return apiRequest<VoiceSynthesisResponse>('/voice/synthesize', {
      method: 'POST',
      body: JSON.stringify(payload),
      token,
    });
  },
};
