/**
 * Phase 7 — Multilingual Voice Interaction Types
 *
 * Aligned strictly with backend Pydantic schemas:
 * - backend/app/schemas/voice.py
 * - backend/app/safety/states.py
 */

import type { SafetyStatus, ChatTurnResponse } from './ai';

export type VoiceLanguage = 'en' | 'hi' | 'te' | 'ta' | 'kn' | 'bn' | 'mr';

export interface VoiceLanguageOption {
  code: VoiceLanguage;
  label: string;
  nativeLabel: string;
}

export const SUPPORTED_VOICE_LANGUAGES: VoiceLanguageOption[] = [
  { code: 'en', label: 'English', nativeLabel: 'English' },
  { code: 'hi', label: 'Hindi', nativeLabel: 'हिन्दी' },
  { code: 'te', label: 'Telugu', nativeLabel: 'తెలుగు' },
  { code: 'ta', label: 'Tamil', nativeLabel: 'தமிழ்' },
  { code: 'kn', label: 'Kannada', nativeLabel: 'ಕನ್ನಡ' },
  { code: 'bn', label: 'Bengali', nativeLabel: 'বাংলা' },
  { code: 'mr', label: 'Marathi', nativeLabel: 'मराठी' },
];

export const SUPPORTED_AUDIO_MIME_TYPES = [
  'audio/wav',
  'audio/webm',
  'audio/mp3',
  'audio/ogg',
  'audio/m4a',
] as const;

export type SupportedAudioMimeType = (typeof SUPPORTED_AUDIO_MIME_TYPES)[number];

export const SUPPORTED_TTS_FORMATS = [
  'audio/wav',
  'audio/mp3',
  'audio/ogg',
] as const;

export type SupportedTtsFormat = (typeof SUPPORTED_TTS_FORMATS)[number];

export const MAX_AUDIO_BYTES = 10 * 1024 * 1024; // 10 MB
export const MAX_TTS_TEXT_LENGTH = 1000;
export const MAX_AUDIO_DURATION_SECONDS = 120.0;

export interface VoiceTranscriptionRequest {
  audio_content: string; // Base64-encoded audio bytes
  mime_type: string;
  language?: VoiceLanguage;
  mother_id?: string;
  session_id?: string;
}

export interface VoiceTranscriptionResponse {
  transcript: string;
  language: VoiceLanguage;
  detected_language: VoiceLanguage;
  confidence: number;
  duration_seconds: number;
  mother_id?: string | null;
  session_id?: string | null;
  created_at: string;
}

export interface VoiceConfirmationRequest {
  session_id: string;
  confirmed_text: string;
  mother_id?: string;
  language?: VoiceLanguage;
}

export interface VoiceConfirmationResponse {
  session_id: string;
  confirmed_text: string;
  chat_turn: ChatTurnResponse;
  safety_state: SafetyStatus;
  confirmed_at: string;
}

export interface VoiceSynthesisRequest {
  text: string;
  language?: VoiceLanguage;
  output_format?: string;
  mother_id?: string;
}

export interface VoiceSynthesisResponse {
  audio_content: string; // Base64-encoded audio bytes
  mime_type: string;
  language: VoiceLanguage;
  text_length: number;
  duration_seconds: number;
  created_at: string;
}

export type AudioRecordingStatus =
  | 'idle'
  | 'requesting_permission'
  | 'recording'
  | 'processing'
  | 'reviewing'
  | 'error';
