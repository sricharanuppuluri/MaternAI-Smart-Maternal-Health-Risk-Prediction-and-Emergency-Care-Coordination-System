/**
 * Voice Audio Player component.
 * Plays base64 synthesized audio bytes received from POST /api/v1/voice/synthesize.
 * Provides accessible controls: play, pause, replay, and progress display.
 */

import React from 'react';
import { Button } from '../common';

export interface VoiceAudioPlayerProps {
  audioContent: string; // Base64-encoded audio bytes
  mimeType: string;
  durationSeconds?: number;
  label?: string;
  isPlaying?: boolean;
  currentTime?: number;
  autoPlay?: boolean;
  onTogglePlay?: () => void;
  onReplay?: () => void;
  className?: string;
}

export const VoiceAudioPlayer: React.FC<VoiceAudioPlayerProps> = ({
  audioContent,
  mimeType,
  durationSeconds = 0,
  label = 'Voice Guidance Audio',
  isPlaying = false,
  currentTime = 0,
  autoPlay = false,
  onTogglePlay,
  onReplay,
  className = '',
}) => {
  const audioSrc = audioContent.startsWith('data:')
    ? audioContent
    : `data:${mimeType};base64,${audioContent}`;

  const formatSeconds = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handlePlayToggle = () => {
    if (onTogglePlay) {
      onTogglePlay();
    } else if (typeof document !== 'undefined') {
      const audio = document.getElementById('voice-audio-element') as HTMLAudioElement;
      if (audio) {
        if (audio.paused) {
          audio.play().catch(() => {});
        } else {
          audio.pause();
        }
      }
    }
  };

  const handleAudioReplay = () => {
    if (onReplay) {
      onReplay();
    } else if (typeof document !== 'undefined') {
      const audio = document.getElementById('voice-audio-element') as HTMLAudioElement;
      if (audio) {
        audio.currentTime = 0;
        audio.play().catch(() => {});
      }
    }
  };

  return (
    <div
      className={`voice-audio-player p-2.5 bg-neutral-light border rounded flex flex-col sm:flex-row items-center justify-between gap-3 text-xs ${className}`}
      role="region"
      aria-label={label}
    >
      <audio id="voice-audio-element" src={audioSrc} preload="metadata" autoPlay={autoPlay} />

      {/* Track Label and Info */}
      <div className="flex items-center gap-2">
        <span className="font-semibold text-foreground flex items-center gap-1.5">
          <span className="inline-block w-2 h-2 rounded-full bg-primary" />
          {label}
        </span>
        <span className="text-[11px] text-muted">
          ({mimeType.replace('audio/', '')})
        </span>
      </div>

      {/* Timing and Controls */}
      <div className="flex items-center gap-2">
        <span className="font-mono text-muted text-[11px]">
          {`${formatSeconds(currentTime)} / ${formatSeconds(durationSeconds)}`}
        </span>

        <Button
          variant={isPlaying ? 'secondary' : 'primary'}
          size="sm"
          onClick={handlePlayToggle}
          aria-label={isPlaying ? 'Pause voice audio' : 'Play voice audio'}
        >
          {isPlaying ? 'Pause' : 'Play'}
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={handleAudioReplay}
          aria-label="Replay voice audio from beginning"
        >
          Replay
        </Button>
      </div>
    </div>
  );
};
