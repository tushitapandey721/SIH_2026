"use client";

import React from "react";
import { Leaf, Sprout, Building2, HelpCircle, ArrowRight, FileCheck, CheckCircle2 } from "lucide-react";
import { ABSComplianceData } from "../types";

interface ABSComplianceCardProps {
  messageId: string;
  absData: ABSComplianceData;
  onOptionSelect: (messageId: string, questionId: string, value: boolean) => void;
}

export const ABSComplianceCard: React.FC<ABSComplianceCardProps> = ({
  messageId,
  absData,
  onOptionSelect,
}) => {
  if (!absData || !absData.triggered) return null;

  return (
    <div className="mb-6 rounded-2xl bg-gradient-to-b from-[#08130e]/95 via-[#0b1712]/90 to-[#070e0a]/95 border border-emerald-500/40 p-5 sm:p-6 shadow-[0_0_35px_rgba(16,185,129,0.14)] space-y-5">
      {/* Panel Header */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-emerald-500/20 pb-3.5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/20 border border-emerald-400/50 flex items-center justify-center text-emerald-300 shadow-[0_0_12px_rgba(52,211,153,0.3)] shrink-0">
            <Leaf className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold tracking-wide text-emerald-200">
                ABS Compliance Helper
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono uppercase bg-emerald-500/15 border border-emerald-400/30 text-emerald-300">
                Structured Flow
              </span>
            </div>
            <span className="text-[11px] text-stone-400 font-mono">
              Biological Diversity Act, 2002 (as amended 2023) · BD Rules 2024
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium ${
              absData.status === "completed"
                ? "bg-emerald-950/80 border border-emerald-400/50 text-emerald-300"
                : "bg-amber-950/80 border border-amber-400/50 text-amber-300 animate-pulse"
            }`}
          >
            <span
              className={`w-2 h-2 rounded-full ${
                absData.status === "completed" ? "bg-emerald-400" : "bg-amber-400"
              }`}
            />
            {absData.status === "completed" ? "Evaluation Complete" : "Action Required"}
          </span>
        </div>
      </div>

      {/* Decision Questions Stepper & Interactive Selectors */}
      <div className="space-y-3">
        <div className="text-[11px] uppercase tracking-wider font-mono text-emerald-400/80 flex items-center gap-1.5">
          <Sprout className="w-3.5 h-3.5 text-emerald-400" />
          <span>Statutory Decision Flow (Click to Test Scenarios):</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {/* Q1: Sourced in India */}
          <div className="p-3.5 rounded-xl bg-black/40 border border-emerald-500/20 space-y-2">
            <div className="text-[10px] font-mono text-stone-400 uppercase">1. Resource Origin</div>
            <div className="text-xs font-medium text-stone-200 leading-snug">
              Sourced in India?
            </div>
            <div className="flex gap-1.5 pt-1">
              <button
                type="button"
                onClick={() => onOptionSelect(messageId, "is_sourced_from_india", true)}
                className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  absData.answers?.is_sourced_from_india === true
                    ? "bg-emerald-500 text-black font-semibold shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                    : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                }`}
              >
                India (Domestic)
              </button>
              <button
                type="button"
                onClick={() => onOptionSelect(messageId, "is_sourced_from_india", false)}
                className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  absData.answers?.is_sourced_from_india === false
                    ? "bg-rose-500 text-white font-semibold shadow-[0_0_10px_rgba(244,63,94,0.4)]"
                    : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                }`}
              >
                Outside India
              </button>
            </div>
          </div>

          {/* Q2: Purpose */}
          <div className="p-3.5 rounded-xl bg-black/40 border border-emerald-500/20 space-y-2">
            <div className="text-[10px] font-mono text-stone-400 uppercase">2. Utilization Purpose</div>
            <div className="text-xs font-medium text-stone-200 leading-snug">
              Commercial vs Research?
            </div>
            <div className="flex gap-1.5 pt-1">
              <button
                type="button"
                onClick={() => onOptionSelect(messageId, "is_commercial_use", true)}
                className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  absData.answers?.is_commercial_use === true
                    ? "bg-emerald-500 text-black font-semibold shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                    : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                }`}
              >
                Commercial / Export
              </button>
              <button
                type="button"
                onClick={() => onOptionSelect(messageId, "is_commercial_use", false)}
                className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  absData.answers?.is_commercial_use === false
                    ? "bg-emerald-500 text-black font-semibold shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                    : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                }`}
              >
                Research Only
              </button>
            </div>
          </div>

          {/* Q3: Entity Type */}
          <div className="p-3.5 rounded-xl bg-black/40 border border-emerald-500/20 space-y-2">
            <div className="text-[10px] font-mono text-stone-400 uppercase">3. Applicant Entity</div>
            <div className="text-xs font-medium text-stone-200 leading-snug">
              Domestic vs Foreign Entity?
            </div>
            <div className="flex gap-1.5 pt-1">
              <button
                type="button"
                onClick={() => onOptionSelect(messageId, "is_foreign_entity", false)}
                className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  absData.answers?.is_foreign_entity === false
                    ? "bg-emerald-500 text-black font-semibold shadow-[0_0_10px_rgba(16,185,129,0.4)]"
                    : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                }`}
              >
                Indian Entity
              </button>
              <button
                type="button"
                onClick={() => onOptionSelect(messageId, "is_foreign_entity", true)}
                className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                  absData.answers?.is_foreign_entity === true
                    ? "bg-amber-500 text-black font-semibold shadow-[0_0_10px_rgba(245,158,11,0.4)]"
                    : "bg-stone-900/80 text-stone-400 hover:text-stone-200 border border-white/5"
                }`}
              >
                Foreign / NRI (S. 3(2))
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Pending Question Callout if Needs Input */}
      {absData.status === "needs_input" && absData.next_question && (
        <div className="p-4 rounded-xl bg-amber-500/10 border border-amber-400/40 space-y-2">
          <div className="flex items-center gap-2 text-xs font-mono uppercase text-amber-300">
            <HelpCircle className="w-4 h-4 text-amber-400 shrink-0" />
            <span>Pending Compliance Clarification:</span>
          </div>
          <p className="text-sm font-medium text-[#f5eedb] leading-snug">
            {absData.next_question.question}
          </p>
          {absData.next_question.help_text && (
            <p className="text-xs text-stone-400 leading-relaxed">
              {absData.next_question.help_text}
            </p>
          )}
          <div className="flex flex-wrap gap-2.5 pt-1.5">
            {absData.next_question.options.map((opt, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => onOptionSelect(messageId, absData.next_question!.id, opt.value)}
                className="px-4 py-2 rounded-lg bg-amber-400 hover:bg-amber-300 text-black font-semibold text-xs transition-colors shadow-md flex items-center gap-2 cursor-pointer"
              >
                <span>{opt.label}</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Structured Results Card */}
      {absData.result && (
        <div className="p-4 sm:p-5 rounded-xl bg-black/50 border border-emerald-500/30 space-y-4">
          {/* Dual Approval Status Verdict Badges */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* NBA Approval Verdict */}
            <div
              className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 ${
                absData.result.requires_nba_approval
                  ? "bg-rose-950/40 border-rose-500/40 text-rose-200"
                  : "bg-emerald-950/30 border-emerald-500/30 text-emerald-200"
              }`}
            >
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-stone-400">
                  National Biodiversity Authority (NBA)
                </div>
                <div className="text-sm font-semibold mt-0.5">
                  {absData.result.requires_nba_approval ? "Prior Approval Required" : "No NBA Approval Required"}
                </div>
              </div>
              {absData.result.requires_nba_approval ? (
                <span className="px-2.5 py-1 rounded-md bg-rose-500/20 border border-rose-400/40 text-rose-300 text-xs font-mono font-bold">
                  MANDATORY
                </span>
              ) : (
                <span className="px-2.5 py-1 rounded-md bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-xs font-mono font-bold">
                  EXEMPT
                </span>
              )}
            </div>

            {/* SBB Intimation Verdict */}
            <div
              className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 ${
                absData.result.requires_sbb_intimation
                  ? "bg-amber-950/40 border-amber-500/40 text-amber-200"
                  : "bg-stone-900/60 border-white/10 text-stone-300"
              }`}
            >
              <div>
                <div className="text-[10px] font-mono uppercase tracking-wider text-stone-400">
                  State Biodiversity Board (SBB)
                </div>
                <div className="text-sm font-semibold mt-0.5">
                  {absData.result.requires_sbb_intimation
                    ? "Prior Intimation Required"
                    : "No SBB Intimation Required"}
                </div>
              </div>
              {absData.result.requires_sbb_intimation ? (
                <span className="px-2.5 py-1 rounded-md bg-amber-500/20 border border-amber-400/40 text-amber-300 text-xs font-mono font-bold">
                  INTIMATION
                </span>
              ) : (
                <span className="px-2.5 py-1 rounded-md bg-stone-800 border border-white/10 text-stone-400 text-xs font-mono">
                  N/A
                </span>
              )}
            </div>
          </div>

          {/* Applicable Provision & Statutory Basis */}
          <div className="p-3.5 rounded-xl bg-emerald-950/20 border border-emerald-500/20 space-y-1.5">
            <div className="flex items-center gap-2 text-xs font-mono text-emerald-300 font-semibold">
              <FileCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>Applicable Statutory Provision:</span>
            </div>
            <div className="text-xs text-stone-200 font-medium">
              {absData.result.applicable_provision}
            </div>
            {absData.result.exact_statutory_text && (
              <p className="text-[11px] text-stone-400 leading-relaxed font-light italic pt-1 border-t border-emerald-500/10">
                "{absData.result.exact_statutory_text}"
              </p>
            )}
          </div>

          {/* Localized SBB Authority if specified */}
          {absData.result.sbb_state && (
            <div className="p-3 rounded-xl bg-black/40 border border-emerald-500/20 flex items-center gap-3">
              <Building2 className="w-4 h-4 text-emerald-400 shrink-0" />
              <div>
                <span className="text-[10px] font-mono uppercase text-stone-400">Designated State Authority:</span>
                <div className="text-xs font-semibold text-emerald-200">
                  {absData.result.sbb_state}
                </div>
              </div>
            </div>
          )}

          {/* Relevant NBA / SBB Filing Forms */}
          {absData.result.relevant_forms && absData.result.relevant_forms.length > 0 && (
            <div className="space-y-1.5">
              <div className="text-[11px] font-mono text-stone-400 uppercase">Applicable Forms to File:</div>
              <div className="flex flex-wrap gap-2">
                {absData.result.relevant_forms.map((form, fIdx) => (
                  <span
                    key={fIdx}
                    className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-emerald-500/10 border border-emerald-400/30 text-xs font-mono text-emerald-300"
                  >
                    <CheckCircle2 className="w-3 h-3 text-emerald-400" />
                    <span>{form}</span>
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Recommended Next Steps */}
          {absData.result.next_steps && absData.result.next_steps.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <div className="text-[11px] font-mono text-stone-400 uppercase">Recommended Compliance Steps:</div>
              <ul className="space-y-1 text-xs text-stone-300">
                {absData.result.next_steps.map((step, sIdx) => (
                  <li key={sIdx} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-mono font-bold">•</span>
                    <span className="leading-snug">{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
