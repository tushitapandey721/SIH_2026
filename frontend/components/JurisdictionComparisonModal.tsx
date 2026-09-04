"use client";

import React from "react";
import {
  Columns2,
  ShieldCheck,
  AlertTriangle,
  Shield,
  Globe2,
  CheckCircle2,
  FileCheck,
  FileText,
  ExternalLink,
} from "lucide-react";
import { JurisdictionComparisonData, Citation } from "../types";
import { getCitationPdfUrl } from "../lib/constants";

interface JurisdictionComparisonModalProps {
  comparisonData: JurisdictionComparisonData;
}

export const JurisdictionComparisonModal: React.FC<JurisdictionComparisonModalProps> = ({
  comparisonData: cmp,
}) => {
  if (!cmp) return null;

  return (
    <div className="w-full space-y-4 animate-in fade-in-50 duration-300">
      {/* Top Comparative Header & Zero Overlap Badge */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-4 sm:p-5 rounded-2xl bg-[#0d0b09]/95 border border-amber-500/30 backdrop-blur-xl shadow-2xl">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400/20 via-amber-600/30 to-black border border-amber-400/40 flex items-center justify-center text-amber-300 shadow-[0_0_15px_rgba(245,158,11,0.25)] shrink-0">
            <Columns2 className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm sm:text-base font-display font-semibold text-[#f5eedb] tracking-wide">
                Side-by-Side Jurisdiction Comparison
              </h2>
              <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-400/30 text-amber-300">
                Dual Parallel RAG
              </span>
            </div>
            <p className="text-xs text-stone-400 font-light">
              Independent statutory pipelines: National (India) vs International (Treaties)
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Parallel Latency Badge */}
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-white/5 border border-white/10 text-stone-300">
            <span className="text-stone-400">Parallel Latency:</span>
            <span className="text-amber-300 font-semibold">{cmp.latency_ms}ms</span>
          </span>

          {/* Zero Overlap Badge */}
          {cmp.is_zero_overlap ? (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-emerald-950/70 border border-emerald-500/50 text-emerald-300 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span>0 shared sources — jurisdictions kept separate</span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-rose-950/70 border border-rose-500/50 text-rose-300">
              <AlertTriangle className="w-3.5 h-3.5 text-rose-400" />
              <span>{cmp.shared_citations_count} Shared Sources Overlap</span>
            </div>
          )}
        </div>
      </div>

      {/* Dual Panels Grid: Side-by-Side on Desktop (grid-cols-2), Stacked on Mobile (grid-cols-1) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5 w-full items-stretch">
        {/* Left Panel: India (National) */}
        <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-amber-500/30 bg-gradient-to-b from-[#120f0b]/95 to-[#090806]/95 shadow-2xl flex flex-col justify-between">
          <div>
            {/* Panel Header */}
            <div className="flex items-center justify-between border-b border-amber-500/15 pb-3.5 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-amber-500/15 border border-amber-400/30 flex items-center justify-center text-amber-300">
                  <Shield className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-display text-sm font-semibold tracking-wide text-amber-100 uppercase">
                    India (National)
                  </span>
                  <span className="block text-[10px] text-stone-400 font-mono">
                    Patents Act, Biological Diversity, D&C
                  </span>
                </div>
              </div>
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium uppercase ${
                  cmp.national.confidence?.toLowerCase() === "high"
                    ? "bg-emerald-950/60 border border-emerald-500/40 text-emerald-300"
                    : cmp.national.confidence?.toLowerCase() === "medium"
                    ? "bg-amber-950/60 border border-amber-500/40 text-amber-300"
                    : "bg-rose-950/60 border border-rose-500/40 text-rose-300"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    cmp.national.confidence?.toLowerCase() === "high"
                      ? "bg-emerald-400"
                      : cmp.national.confidence?.toLowerCase() === "medium"
                      ? "bg-amber-400"
                      : "bg-rose-400"
                  }`}
                />
                {cmp.national.confidence} Confidence
              </span>
            </div>

            {/* Classification badge if present */}
            {cmp.national.classification && (
              <div className="mb-3">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/20 text-amber-300 text-[11px] font-mono uppercase">
                  <CheckCircle2 className="w-3 h-3 text-amber-400" />
                  {cmp.national.classification.replace(/_/g, " ")}
                </span>
              </div>
            )}

            {/* Answer Content or Abstention */}
            {cmp.national.abstained ? (
              <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-400/30 text-amber-200 text-xs sm:text-sm space-y-2">
                <div className="flex items-center gap-2 font-semibold text-amber-300 uppercase tracking-wider">
                  <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
                  <span>No Relevant National Authority (Abstained)</span>
                </div>
                <p className="text-stone-300 leading-relaxed font-light whitespace-pre-line">
                  {cmp.national.answer}
                </p>
              </div>
            ) : (
              <div className="prose prose-invert prose-amber max-w-none text-xs sm:text-sm leading-relaxed text-[#ede8d5] font-light whitespace-pre-line">
                {cmp.national.answer}
              </div>
            )}
          </div>

          {/* Citation Ledger Underneath National Panel */}
          <div className="mt-6 pt-4 border-t border-amber-500/15">
            <div className="text-xs font-mono uppercase tracking-wider text-amber-400/90 mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileCheck className="w-3.5 h-3.5 text-amber-400" />
                <span>National Statutory Citations ({cmp.national.citations?.length || 0})</span>
              </div>
              <span className="text-[10px] text-stone-500 font-mono">Domestic Law</span>
            </div>

            {cmp.national.citations && cmp.national.citations.length > 0 ? (
              <div className="space-y-2">
                {cmp.national.citations.map((cit, cIdx) => {
                  const pdfUrl = getCitationPdfUrl(cit);
                  return (
                    <div
                      key={cIdx}
                      className="p-3 rounded-xl bg-black/40 border border-amber-500/20 hover:border-amber-400/50 transition-all flex flex-col justify-between"
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-[11px] font-mono text-amber-300 font-bold">
                          {cit.section}
                        </span>
                        <a
                          href={pdfUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-500/15 border border-amber-400/30 text-[10px] text-amber-300 hover:bg-amber-400 hover:text-black transition-all"
                        >
                          <FileText className="w-2.5 h-2.5" />
                          <span>PDF</span>
                          {cit.page_number && (
                            <span className="text-[9px] font-mono">p.{cit.page_number}</span>
                          )}
                          <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                        </a>
                      </div>
                      <div className="text-xs text-stone-300 font-normal leading-snug">
                        {cit.source}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-stone-500 italic">No national statutory citations recorded.</p>
            )}
          </div>
        </div>

        {/* Right Panel: International (Treaties) */}
        <div className="glass-panel rounded-2xl p-5 sm:p-6 border border-sky-500/30 bg-gradient-to-b from-[#0b1016]/95 to-[#07090e]/95 shadow-2xl flex flex-col justify-between">
          <div>
            {/* Panel Header */}
            <div className="flex items-center justify-between border-b border-sky-500/15 pb-3.5 mb-4">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-sky-500/15 border border-sky-400/30 flex items-center justify-center text-sky-300">
                  <Globe2 className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-display text-sm font-semibold tracking-wide text-sky-100 uppercase">
                    International (Treaties)
                  </span>
                  <span className="block text-[10px] text-stone-400 font-mono">
                    Nagoya Protocol, WIPO GRATK, TRIPS, CBD
                  </span>
                </div>
              </div>
              <span
                className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-mono font-medium uppercase ${
                  cmp.international.confidence?.toLowerCase() === "high"
                    ? "bg-emerald-950/60 border border-emerald-500/40 text-emerald-300"
                    : cmp.international.confidence?.toLowerCase() === "medium"
                    ? "bg-amber-950/60 border border-amber-500/40 text-amber-300"
                    : "bg-rose-950/60 border border-rose-500/40 text-rose-300"
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    cmp.international.confidence?.toLowerCase() === "high"
                      ? "bg-emerald-400"
                      : cmp.international.confidence?.toLowerCase() === "medium"
                      ? "bg-amber-400"
                      : "bg-rose-400"
                  }`}
                />
                {cmp.international.confidence} Confidence
              </span>
            </div>

            {/* Answer Content or Abstention */}
            {cmp.international.abstained ? (
              <div className="p-4 rounded-xl bg-sky-950/20 border border-sky-400/30 text-sky-200 text-xs sm:text-sm space-y-2">
                <div className="flex items-center gap-2 font-semibold text-sky-300 uppercase tracking-wider">
                  <AlertTriangle className="w-4 h-4 text-sky-400 shrink-0" />
                  <span>No Relevant Treaty Authority (Abstained)</span>
                </div>
                <p className="text-stone-300 leading-relaxed font-light whitespace-pre-line">
                  {cmp.international.answer}
                </p>
              </div>
            ) : (
              <div className="prose prose-invert prose-sky max-w-none text-xs sm:text-sm leading-relaxed text-[#ede8d5] font-light whitespace-pre-line">
                {cmp.international.answer}
              </div>
            )}
          </div>

          {/* Citation Ledger Underneath International Panel */}
          <div className="mt-6 pt-4 border-t border-sky-500/15">
            <div className="text-xs font-mono uppercase tracking-wider text-sky-400/90 mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Globe2 className="w-3.5 h-3.5 text-sky-400" />
                <span>International Treaty Authorities ({cmp.international.citations?.length || 0})</span>
              </div>
              <span className="text-[10px] text-stone-500 font-mono">Global Conventions</span>
            </div>

            {cmp.international.citations && cmp.international.citations.length > 0 ? (
              <div className="space-y-2">
                {cmp.international.citations.map((cit, cIdx) => {
                  const pdfUrl = getCitationPdfUrl(cit);
                  return (
                    <div
                      key={cIdx}
                      className="p-3 rounded-xl bg-black/40 border border-sky-500/20 hover:border-sky-400/50 transition-all flex flex-col justify-between"
                    >
                      <div className="flex items-center justify-between gap-2 mb-1">
                        <span className="text-[11px] font-mono text-sky-300 font-bold">
                          {cit.section}
                        </span>
                        <a
                          href={pdfUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-sky-500/15 border border-sky-400/30 text-[10px] text-sky-300 hover:bg-sky-400 hover:text-black transition-all"
                        >
                          <FileText className="w-2.5 h-2.5" />
                          <span>PDF</span>
                          {cit.page_number && (
                            <span className="text-[9px] font-mono">p.{cit.page_number}</span>
                          )}
                          <ExternalLink className="w-2.5 h-2.5 ml-0.5" />
                        </a>
                      </div>
                      <div className="text-xs text-stone-300 font-normal leading-snug">
                        {cit.source}
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-xs text-stone-500 italic">No international treaty citations recorded.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
