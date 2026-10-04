/**
 * Voice Recorder Card component.
 *
 * Implements:
 * - Multilingual Voice Recording controls (Start, Stop, Cancel)
 * - Microphone permission & hardware error handling
 * - Audio transcription via POST /api/v1/voice/transcribe
 * - Clinical Observation Confirmation Boundary:
 *   * Raw audio/transcription is NEVER persisted until explicit confirmation
 *   * Editable transcript textarea for reviewing/editing observations
 *   * Explicit confirmation via POST /api/v1/voice/confirm
 * - Text-to-Speech synthesis playback via POST /api/v1/voice/synthesize
 * - Authoritative SafetyStatus presentation
 */

import React, { useState } from 'react';
import { Card, Button, AlertBanner } from '../common';
import { VoiceLanguageSelector } from './VoiceLanguageSelector';
import { VoiceAudioPlayer } from './VoiceAudioPlayer';
import { SafetyStatusBadge } from '../ai/SafetyStatusBadge';
import { useAudioRecorder } from '../../hooks/useAudioRecorder';
import { voiceService } from '../../services/voiceService';
import type {
  VoiceLanguage,
  VoiceTranscriptionResponse,
  VoiceConfirmationResponse,
  VoiceSynthesisResponse,
} from '../../types/voice';

export interface VoiceRecorderCardProps {
  sessionId?: string;
  motherId?: string;
  defaultLanguage?: VoiceLanguage;
  onConfirmedTurn?: (turn: VoiceConfirmationResponse) => void;
  onConfirmedText?: (text: string, language: VoiceLanguage) => void;
  className?: string;
}

export const VoiceRecorderCard: React.FC<VoiceRecorderCardProps> = ({
  sessionId,
  motherId,
  defaultLanguage = 'en',
  onConfirmedTurn,
  onConfirmedText,
  className = '',
}) => {
  const [selectedLanguage, setSelectedLanguage] = useState<VoiceLanguage>(defaultLanguage);
  const [isTranscribing, setIsTranscribing] = useState<boolean>(false);
  const [isConfirming, setIsConfirming] = useState<boolean>(false);
  const [isSynthesizing, setIsSynthesizing] = useState<boolean>(false);
  const [transcription, setTranscription] = useState<VoiceTranscriptionResponse | null>(null);
  const [editableText, setEditableText] = useState<string>('');
  const [lastTurn, setLastTurn] = useState<VoiceConfirmationResponse | null>(null);
  const [synthesizedAudio, setSynthesizedAudio] = useState<VoiceSynthesisResponse | null>(null);
  const [apiError, setApiError] = useState<string | null>(null);

  // Step 1: Transcribe recorded audio
  const handleTranscribe = async (b64Audio: string, audioMime: string) => {
    setIsTranscribing(true);
    setApiError(null);

    try {
      const res = await voiceService.transcribeAudio({
        audio_content: b64Audio,
        mime_type: audioMime,
        language: selectedLanguage,
        mother_id: motherId,
        session_id: sessionId,
      });

      setTranscription(res);
      setEditableText(res.transcript);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Audio transcription failed.';
      setApiError(msg);
    } finally {
      setIsTranscribing(false);
    }
  };

  const {
    status: recordingStatus,
    recordingTime,
    error: recorderError,
    startRecording,
    stopRecording,
    cancelRecording,
    resetRecording,
    clearError: clearRecorderError,
  } = useAudioRecorder({
    onRecordingComplete: (b64, mime) => {
      handleTranscribe(b64, mime);
    },
  });

  const isRecording = recordingStatus === 'recording';
  const isRequesting = recordingStatus === 'requesting_permission';

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')} / 02:00`;
  };

  // Step 2: Explicit Confirmation Boundary
  const handleConfirm = async () => {
    const confirmedText = editableText.trim();
    if (!confirmedText || isConfirming) return;

    setIsConfirming(true);
    setApiError(null);

    try {
      if (sessionId) {
        const turn = await voiceService.confirmVoiceTranscript({
          session_id: sessionId,
          confirmed_text: confirmedText,
          mother_id: motherId,
          language: selectedLanguage,
        });

        setLastTurn(turn);
        onConfirmedTurn?.(turn);
      } else {
        onConfirmedText?.(confirmedText, selectedLanguage);
      }

      // Reset recorder state for next interaction
      resetRecording();
      setTranscription(null);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to confirm transcribed voice text.';
      setApiError(msg);
    } finally {
      setIsConfirming(false);
    }
  };

  // Step 3: Text-to-Speech Synthesis
  const handleSynthesizeAssistantReply = async (text: string) => {
    if (!text || isSynthesizing) return;

    setIsSynthesizing(true);
    setApiError(null);

    try {
      const tts = await voiceService.synthesizeSpeech({
        text,
        language: selectedLanguage,
        output_format: 'audio/wav',
        mother_id: motherId,
      });
      setSynthesizedAudio(tts);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Speech synthesis failed.';
      setApiError(msg);
    } finally {
      setIsSynthesizing(false);
    }
  };

  const handleDiscard = () => {
    resetRecording();
    setTranscription(null);
    setEditableText('');
    setApiError(null);
  };

  return (
    <Card
      title="Multilingual Voice Interaction"
      subtitle="Hands-free voice recording, user-confirmed transcription, and audio response"
      className={`voice-recorder-card space-y-4 ${className}`}
    >
      {/* Language Selector Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 pb-3 border-b">
        <VoiceLanguageSelector
          value={selectedLanguage}
          onChange={setSelectedLanguage}
          disabled={isRecording || isTranscribing || isConfirming}
        />
        <div className="text-xs text-muted">
          <span>Max Duration: 2 min | Max Size: 10 MB</span>
        </div>
      </div>

      {/* Error Banners */}
      {recorderError && (
        <AlertBanner
          type="danger"
          message={recorderError}
          onDismiss={clearRecorderError}
        />
      )}
      {apiError && (
        <AlertBanner
          type="danger"
          message={apiError}
          onDismiss={() => setApiError(null)}
        />
      )}

      {/* Recording Stage Controls */}
      {!transcription && !isTranscribing && (
        <div className="recording-controls-section p-4 bg-neutral-light border rounded flex flex-col items-center justify-center text-center space-y-3">
          {/* Status Indicator */}
          {isRecording ? (
            <div className="flex items-center gap-2 text-danger font-semibold text-sm animate-pulse">
              <span className="w-3 h-3 rounded-full bg-danger inline-block" />
              <span>Recording Voice ({formatTimer(recordingTime)})</span>
            </div>
          ) : isRequesting ? (
            <div className="text-sm text-primary flex items-center gap-2">
              <div className="spinner" />
              <span>Requesting microphone access...</span>
            </div>
          ) : (
            <div className="text-sm text-muted">
              Press the button below and speak your health question or symptom observation.
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center gap-3">
            {!isRecording ? (
              <Button
                variant="primary"
                onClick={startRecording}
                disabled={isRequesting}
                aria-label="Start voice recording"
              >
                Start Recording
              </Button>
            ) : (
              <>
                <Button
                  variant="primary"
                  onClick={stopRecording}
                  aria-label="Stop voice recording and transcribe"
                >
                  Stop & Transcribe
                </Button>
                <Button
                  variant="outline"
                  onClick={cancelRecording}
                  aria-label="Cancel recording"
                >
                  Cancel
                </Button>
              </>
            )}
          </div>
        </div>
      )}

      {/* Transcription Loading Spinner */}
      {isTranscribing && (
        <div className="transcription-loading-state p-6 border rounded bg-white text-center space-y-2">
          <div className="spinner mx-auto" />
          <p className="text-sm font-semibold text-foreground">Transcribing audio via IndicWhisper...</p>
          <p className="text-xs text-muted">
            Transcribed medical observations are held for user confirmation before entering the care record.
          </p>
        </div>
      )}

      {/* Clinical Observation Confirmation Boundary */}
      {transcription && (
        <div className="transcript-review-box p-4 border rounded bg-white shadow-sm space-y-3">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-2">
            <div>
              <span className="text-xs font-semibold uppercase text-muted tracking-wider block">
                Review Transcribed Observation
              </span>
              <span className="text-[11px] text-muted">
                Confidence: {(transcription.confidence * 100).toFixed(0)}% | Duration: {transcription.duration_seconds.toFixed(1)}s | Language: {transcription.language.toUpperCase()}
              </span>
            </div>
            <div className="text-xs font-medium text-warning-dark bg-warning-light px-2 py-0.5 rounded border border-warning">
              Confirmation Required
            </div>
          </div>

          <div className="space-y-1">
            <label htmlFor="transcript-editable-input" className="text-xs text-muted block">
              Review or edit the text before sending it to your care session:
            </label>
            <textarea
              id="transcript-editable-input"
              rows={3}
              value={editableText}
              onChange={(e) => setEditableText(e.target.value)}
              disabled={isConfirming}
              className="w-full text-sm p-2 border rounded focus:outline-none focus:ring-1 focus:ring-primary"
              aria-label="Editable transcribed text"
            />
          </div>

          <p className="text-[11px] text-muted italic m-0">
            <strong>Safety Notice:</strong> Raw speech is never persisted without user approval. Review ensures accurate health records and appropriate safety evaluation.
          </p>

          {/* Confirmation Actions */}
          <div className="flex items-center gap-3 pt-2">
            <Button
              variant="primary"
              onClick={handleConfirm}
              disabled={isConfirming || !editableText.trim()}
              isLoading={isConfirming}
            >
              {isConfirming ? 'Confirming...' : 'Confirm & Submit to Care Session'}
            </Button>
            <Button
              variant="outline"
              onClick={handleDiscard}
              disabled={isConfirming}
            >
              Discard & Record Again
            </Button>
          </div>
        </div>
      )}

      {/* Confirmed Chat Turn Response & TTS Section */}
      {lastTurn && (
        <div className="confirmed-turn-result p-4 border rounded bg-neutral-light space-y-3">
          <div className="flex items-center justify-between border-b pb-2">
            <span className="text-xs font-semibold text-muted uppercase">Assistant Care Guidance</span>
            <SafetyStatusBadge safetyState={lastTurn.safety_state} />
          </div>

          <p className="text-sm whitespace-pre-wrap leading-relaxed m-0 text-foreground">
            {lastTurn.chat_turn.assistant_message.content}
          </p>

          {/* TTS Synthesis Button */}
          {!synthesizedAudio ? (
            <div className="pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleSynthesizeAssistantReply(lastTurn.chat_turn.assistant_message.content)}
                disabled={isSynthesizing}
                isLoading={isSynthesizing}
              >
                {isSynthesizing ? 'Synthesizing Audio...' : 'Listen to Guidance (TTS)'}
              </Button>
            </div>
          ) : (
            <div className="pt-2">
              <VoiceAudioPlayer
                audioContent={synthesizedAudio.audio_content}
                mimeType={synthesizedAudio.mime_type}
                durationSeconds={synthesizedAudio.duration_seconds}
                label="Spoken Care Guidance"
                autoPlay={true}
              />
            </div>
          )}

          {lastTurn.chat_turn.disclaimer && (
            <p className="text-[11px] text-muted italic pt-2 border-t m-0">
              {lastTurn.chat_turn.disclaimer}
            </p>
          )}
        </div>
      )}
    </Card>
  );
};
