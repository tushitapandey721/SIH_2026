"use client";

import React from "react";
import { HelpCircle, ArrowRight } from "lucide-react";
import { QuestionData } from "../types";

interface FormulationTreeCardProps {
  question: QuestionData;
  isLoading: boolean;
  onSelect: (questionId: string, value: boolean) => void;
}

export const FormulationTreeCard: React.FC<FormulationTreeCardProps> = ({
  question,
  isLoading,
  onSelect,
}) => {
  if (!question) return null;

  return (
    <div className="space-y-4 my-3">
      <div className="p-4 sm:p-5 rounded-2xl bg-amber-500/10 border border-amber-400/30 shadow-lg">
        <div className="flex items-center gap-2 text-xs font-mono uppercase text-amber-300 tracking-wider mb-2">
          <HelpCircle className="w-4 h-4 text-amber-400" />
          <span>Regulatory Decision Tree Required</span>
        </div>
        <h3 className="text-base sm:text-lg font-medium text-[#f5eedb] leading-snug">
          {question.question}
        </h3>
        {question.help_text && (
          <p className="mt-2 text-xs text-stone-400 leading-relaxed font-light">
            {question.help_text}
          </p>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
        <button
          type="button"
          onClick={() => onSelect(question.id, true)}
          disabled={isLoading}
          className="px-5 py-3.5 rounded-xl bg-[#f5eedb] hover:bg-white text-[#070605] font-semibold text-xs sm:text-sm transition-all shadow-[0_0_20px_rgba(245,238,219,0.2)] flex items-center justify-between group disabled:opacity-50 cursor-pointer"
        >
          <span>YES, THIS APPLIES</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>

        <button
          type="button"
          onClick={() => onSelect(question.id, false)}
          disabled={isLoading}
          className="px-5 py-3.5 rounded-xl bg-stone-900/90 hover:bg-stone-800 border border-amber-500/30 text-[#ede8d5] font-medium text-xs sm:text-sm transition-all flex items-center justify-between group disabled:opacity-50 cursor-pointer"
        >
          <span>NO, DOES NOT APPLY</span>
          <ArrowRight className="w-4 h-4 text-stone-500 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  );
};
