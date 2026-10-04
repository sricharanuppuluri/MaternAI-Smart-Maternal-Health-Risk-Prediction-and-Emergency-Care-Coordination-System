/**
 * Hook for capturing audio input from user's microphone.
 * Handles permission states, MediaRecorder recording lifecycle,
 * duration timer, audio chunk compilation, and Base64 encoding.
 */

import { useState, useRef, useCallback, useEffect } from 'react';
import type { AudioRecordingStatus } from '../types/voice';
import { MAX_AUDIO_DURATION_SECONDS } from '../types/voice';

export interface UseAudioRecorderReturn {
  status: AudioRecordingStatus;
  recordingTime: number; // in seconds
  audioBlob: Blob | null;
  audioBase64: string | null;
  mimeType: string;
  error: string | null;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  cancelRecording: () => void;
  resetRecording: () => void;
  clearError: () => void;
}

export async function blobToBase64(blob: Blob): Promise<string> {
  if (typeof FileReader !== 'undefined') {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        if (typeof reader.result === 'string') {
          // Strip data:audio/*;base64, prefix if present
          const base64Content = reader.result.split(',')[1] || reader.result;
          resolve(base64Content);
        } else {
          reject(new Error('Failed to read audio blob as base64 string.'));
        }
      };
      reader.onerror = () => reject(reader.error);
      reader.readAsDataURL(blob);
    });
  }

  // Universal fallback for Node / test environments
  const arrayBuffer = await blob.arrayBuffer();
  const bytes = new Uint8Array(arrayBuffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

export interface UseAudioRecorderOptions {
  onRecordingComplete?: (b64Audio: string, mimeType: string) => void;
}

export const useAudioRecorder = (options?: UseAudioRecorderOptions): UseAudioRecorderReturn => {
  const [status, setStatus] = useState<AudioRecordingStatus>('idle');
  const [recordingTime, setRecordingTime] = useState<number>(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioBase64, setAudioBase64] = useState<string | null>(null);
  const [mimeType, setMimeType] = useState<string>('audio/webm');
  const [error, setError] = useState<string | null>(null);

  const optionsRef = useRef<UseAudioRecorderOptions | undefined>(options);

  useEffect(() => {
    optionsRef.current = options;
  }, [options]);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const clearTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const cleanupStream = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      clearTimer();
      cleanupStream();
    };
  }, [clearTimer, cleanupStream]);

  const startRecording = useCallback(async () => {
    setError(null);
    setAudioBlob(null);
    setAudioBase64(null);
    setRecordingTime(0);
    audioChunksRef.current = [];

    if (!navigator?.mediaDevices?.getUserMedia) {
      setError('Microphone audio recording is not supported in this browser environment.');
      setStatus('error');
      return;
    }

    try {
      setStatus('requesting_permission');
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      // Determine supported mime type
      let chosenMime = 'audio/webm';
      if (typeof MediaRecorder !== 'undefined') {
        if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/webm;codecs=opus')) {
          chosenMime = 'audio/webm';
        } else if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')) {
          chosenMime = 'audio/ogg';
        } else if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/wav')) {
          chosenMime = 'audio/wav';
        } else if (MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported('audio/mp4')) {
          chosenMime = 'audio/m4a';
        }
      }
      setMimeType(chosenMime);

      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        clearTimer();
        cleanupStream();

        const blob = new Blob(audioChunksRef.current, { type: chosenMime });
        setAudioBlob(blob);
        setStatus('processing');

        try {
          const b64 = await blobToBase64(blob);
          setAudioBase64(b64);
          setStatus('reviewing');
          optionsRef.current?.onRecordingComplete?.(b64, chosenMime);
        } catch (err) {
          const msg = err instanceof Error ? err.message : 'Failed to process audio recording.';
          setError(msg);
          setStatus('error');
        }
      };

      recorder.start(250); // collect data every 250ms
      setStatus('recording');

      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => {
          if (prev + 1 >= MAX_AUDIO_DURATION_SECONDS) {
            // Automatically stop at max duration
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
              mediaRecorderRef.current.stop();
            }
            return MAX_AUDIO_DURATION_SECONDS;
          }
          return prev + 1;
        });
      }, 1000);
    } catch (err: unknown) {
      cleanupStream();
      clearTimer();
      const msg =
        err instanceof Error && err.name === 'NotAllowedError'
          ? 'Microphone permission was denied. Please allow microphone access to record voice.'
          : err instanceof Error
            ? err.message
            : 'Unable to access microphone.';
      setError(msg);
      setStatus('error');
    }
  }, [cleanupStream, clearTimer]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
  }, []);

  const cancelRecording = useCallback(() => {
    clearTimer();
    cleanupStream();
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.onstop = null;
      mediaRecorderRef.current.stop();
    }
    mediaRecorderRef.current = null;
    audioChunksRef.current = [];
    setAudioBlob(null);
    setAudioBase64(null);
    setRecordingTime(0);
    setStatus('idle');
    setError(null);
  }, [clearTimer, cleanupStream]);

  const resetRecording = useCallback(() => {
    cancelRecording();
  }, [cancelRecording]);

  const clearError = useCallback(() => {
    setError(null);
    if (status === 'error') {
      setStatus('idle');
    }
  }, [status]);

  return {
    status,
    recordingTime,
    audioBlob,
    audioBase64,
    mimeType,
    error,
    startRecording,
    stopRecording,
    cancelRecording,
    resetRecording,
    clearError,
  };
};
