/**
 * Voice Language Selector component.
 * Allows user to choose from the 7 supported Indic and English voice languages.
 */

import React from 'react';
import { SUPPORTED_VOICE_LANGUAGES } from '../../types/voice';
import type { VoiceLanguage } from '../../types/voice';

export interface VoiceLanguageSelectorProps {
  value: VoiceLanguage;
  onChange: (language: VoiceLanguage) => void;
  disabled?: boolean;
  className?: string;
  id?: string;
}

export const VoiceLanguageSelector: React.FC<VoiceLanguageSelectorProps> = ({
  value,
  onChange,
  disabled = false,
  className = '',
  id = 'voice-language-select',
}) => {
  return (
    <div className={`voice-language-selector flex items-center gap-2 ${className}`}>
      <label htmlFor={id} className="text-xs font-semibold text-muted uppercase tracking-wider">
        Voice Language:
      </label>
      <select
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value as VoiceLanguage)}
        disabled={disabled}
        className="text-xs p-1.5 border rounded bg-white text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
        aria-label="Select voice interaction language"
      >
        {SUPPORTED_VOICE_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.label} ({lang.nativeLabel})
          </option>
        ))}
      </select>
    </div>
  );
};
