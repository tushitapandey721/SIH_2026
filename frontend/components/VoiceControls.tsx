"use client";

import React from "react";
import { Mic, MicOff, Volume2, VolumeX } from "lucide-react";
import { VOICE_LANGUAGES } from "../lib/constants";

interface VoiceControlsProps {
  isSupported: boolean;
  isListening: boolean;
  voiceLanguage: string;
  onLanguageChange: (lang: string) => void;
  onToggleListening: () => void;
  disabled?: boolean;
}

export const VoiceControls: React.FC<VoiceControlsProps> = ({
  isSupported,
  isListening,
  voiceLanguage,
  onLanguageChange,
  onToggleListening,
  disabled = false,
}) => {
  if (!isSupported) return null;

  return (
    <div className="flex items-center gap-1.5">
      <button
        type="button"
        onClick={onToggleListening}
        disabled={disabled}
        title={isListening ? "Stop voice listening" : `Voice input (${voiceLanguage})`}
        className={`p-2 rounded-xl transition-all flex items-center justify-center cursor-pointer ${
          isListening
            ? "bg-rose-500/30 border border-rose-400/80 text-rose-200 shadow-[0_0_15px_rgba(244,63,94,0.4)] animate-pulse"
            : "text-stone-400 hover:text-amber-300 hover:bg-stone-800/80 border border-transparent hover:border-amber-500/30"
        }`}
      >
        {isListening ? (
          <div className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-400 animate-ping" />
            <Mic className="w-4 h-4 text-rose-300" />
            <span className="text-[11px] font-mono text-rose-200 hidden sm:inline">Listening...</span>
          </div>
        ) : (
          <Mic className="w-4 h-4 text-amber-400/90" />
        )}
      </button>

      <select
        value={voiceLanguage}
        onChange={(e) => onLanguageChange(e.target.value)}
        disabled={isListening || disabled}
        title="Voice recognition language"
        className="bg-stone-900 border border-white/10 rounded-lg px-2 py-1 text-[10px] font-mono text-stone-300 outline-none hover:border-amber-400/40 cursor-pointer"
      >
        {VOICE_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code}>
            {lang.short} ({lang.name})
          </option>
        ))}
      </select>
    </div>
  );
};
