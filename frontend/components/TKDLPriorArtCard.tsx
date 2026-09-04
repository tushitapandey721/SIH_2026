"use client";

import React from "react";
import { BookOpen, History, ExternalLink } from "lucide-react";
import { TKDLPointerData, HistoricalCaseStudyData } from "../types";

interface TKDLPriorArtCardProps {
  tkdlData?: TKDLPointerData;
  caseStudyData?: HistoricalCaseStudyData;
}

export const TKDLPriorArtCard: React.FC<TKDLPriorArtCardProps> = ({
  tkdlData,
  caseStudyData,
}) => {
  const cs = caseStudyData || tkdlData?.case_study;

  return (
    <div className="space-y-4 my-4">
      {/* CONDITIONAL INLINE TKDL PRIOR-ART NOTE */}
      {tkdlData && tkdlData.triggered && (
        <div className="p-4 rounded-xl bg-indigo-950/30 border border-indigo-500/30 text-xs text-stone-300 flex items-start gap-3 shadow-sm">
          <BookOpen className="w-4 h-4 text-indigo-400 shrink-0 mt-0.5" />
          <div className="space-y-1.5 leading-relaxed">
            <div>
              <span className="font-semibold text-indigo-300">Prior-Art Clearance (TKDL): </span>
              <span>
                Classical formulations belong to the public domain under Section 3(p) of the Patents Act, 1970 and are catalogued in the Traditional Knowledge Digital Library (
              </span>
              <a
                href={tkdlData.official_portal_url || "https://www.tkdl.res.in"}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-0.5 text-indigo-300 hover:text-indigo-100 underline font-mono text-[11px]"
              >
                <span>tkdl.res.in</span>
                <ExternalLink className="w-2.5 h-2.5" />
              </a>
              <span>).</span>
            </div>
            <p className="text-[11px] text-stone-400 font-light">
              TKDL is accessed directly by patent examiners during examination rather than via open public search.
            </p>

            {/* Optional Hints: IPC Classes and Classical Source Texts */}
            {tkdlData.hints && (
              <div className="pt-2 border-t border-indigo-500/20 space-y-2">
                {tkdlData.hints.ipc_classes && tkdlData.hints.ipc_classes.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                    <span className="text-stone-400">Relevant IPC Classes:</span>
                    {tkdlData.hints.ipc_classes.map((ipc, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-indigo-500/20 border border-indigo-400/30 text-indigo-200">
                        {ipc.code} ({ipc.description})
                      </span>
                    ))}
                  </div>
                )}
                {tkdlData.hints.classical_source_texts && tkdlData.hints.classical_source_texts.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 text-[10px] font-mono">
                    <span className="text-stone-400">First-Schedule Texts:</span>
                    {tkdlData.hints.classical_source_texts.map((text, idx) => (
                      <span key={idx} className="px-2 py-0.5 rounded bg-stone-900 border border-stone-700 text-amber-200/90">
                        {text}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* HISTORICAL BIOPIRACY PRECEDENTS CARD (TURMERIC & NEEM) */}
      {cs && cs.triggered && (
        <div className="rounded-2xl bg-gradient-to-b from-[#14100b]/95 via-[#19130d]/90 to-[#0f0c08]/95 border border-amber-600/35 p-4 sm:p-5 shadow-[0_0_30px_rgba(217,119,6,0.12)] space-y-4">
          {/* Header */}
          <div className="flex flex-wrap items-center justify-between gap-2 border-b border-amber-500/20 pb-3">
            <div className="flex items-center gap-2.5">
              <div className="w-7 h-7 rounded-lg bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300 shadow-[0_0_10px_rgba(245,158,11,0.25)] shrink-0">
                <History className="w-4 h-4 text-amber-400" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs sm:text-sm font-semibold tracking-wide text-amber-200">
                    Historical Landmark Precedents: Turmeric &amp; Neem Revocations
                  </span>
                  <span className="hidden sm:inline-block px-2 py-0.5 rounded-full text-[9px] font-mono uppercase bg-amber-500/15 border border-amber-400/30 text-amber-300">
                    Case Law
                  </span>
                </div>
                <p className="text-[11px] text-stone-400 font-light">
                  Real-world patent office precedents establishing Section 3(p) &amp; TKDL
                </p>
              </div>
            </div>
            <span className="text-[10px] font-mono px-2.5 py-1 rounded-md bg-stone-900/80 border border-white/10 text-stone-400">
              USPTO &amp; EPO Revocation Records
            </span>
          </div>

          {/* Two Landmark Case Cards Side-by-Side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {/* Turmeric Case */}
            <div className="p-3.5 rounded-xl bg-black/45 border border-amber-500/25 space-y-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-xs font-mono font-bold text-amber-300 tracking-wide">
                    TURMERIC CASE
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-400/30 text-rose-300 font-semibold">
                    Revoked 1997
                  </span>
                </div>
                <div className="text-[11px] font-mono text-stone-400 mb-2 flex items-center justify-between">
                  <span>USPTO &bull; US Patent 5,401,504</span>
                  <span className="text-stone-400 text-[10px]">Granted 1995</span>
                </div>
                <p className="text-xs text-stone-300 leading-relaxed font-light">
                  {cs.turmeric_case?.facts ||
                    "In 1995, the US Patent and Trademark Office granted US Patent 5,401,504 to the University of Mississippi Medical Center for turmeric powder's wound-healing use. India's CSIR filed a re-examination request in 1996 with 32 prior-art references from traditional and scientific literature, and the USPTO revoked the patent in 1997 after finding the use was already known traditional knowledge, not a novel invention."}
                </p>
              </div>
            </div>

            {/* Neem Case */}
            <div className="p-3.5 rounded-xl bg-black/45 border border-amber-500/25 space-y-2 flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-xs font-mono font-bold text-amber-300 tracking-wide">
                    NEEM CASE
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-rose-500/15 border border-rose-400/30 text-rose-300 font-semibold">
                    Revoked 2000 (Appeal 2005)
                  </span>
                </div>
                <div className="text-[11px] font-mono text-stone-400 mb-2 flex items-center justify-between">
                  <span>EPO &bull; EP 436257</span>
                  <span className="text-stone-400 text-[10px]">Granted 1994</span>
                </div>
                <p className="text-xs text-stone-300 leading-relaxed font-light">
                  {cs.neem_case?.facts ||
                    "In 1994, the European Patent Office granted a patent (EP 436257) to the US Department of Agriculture and W.R. Grace for a neem-based fungicide. Following opposition on grounds that neem's antifungal use was centuries-old Indian traditional knowledge, the EPO revoked the patent in 2000, a decision upheld on final appeal in 2005 — the world's first patent revoked specifically on biopiracy grounds."}
                </p>
              </div>
            </div>
          </div>

          {/* Closing Statutory Takeaway Banner */}
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-400/25 text-xs text-amber-200/95 leading-relaxed font-light">
            <span className="font-semibold text-amber-300">Statutory Significance: </span>
            {cs.closing_line ||
              "These cases are part of why Section 3(p) of the Patents Act, 1970 excludes traditional knowledge from patentability, and why the Traditional Knowledge Digital Library (TKDL) exists — to document India's traditional knowledge so it can be used as prior art before a wrongful patent is even granted, rather than fought after the fact."}
          </div>

          {/* Footnote Citation */}
          <div className="pt-2 border-t border-white/5 flex flex-wrap items-center justify-between gap-2 text-[10px] font-mono text-stone-400">
            <span>
              {cs.source_footnote ||
                "Sources: WIPO Traditional Knowledge Case Studies (WIPO/GRTKF); USPTO Reexamination Certificate B1 5,401,504; EPO Opposition Decision EP 0436257 B1."}
            </span>
            <span className="text-stone-400">Public historical patent office records</span>
          </div>
        </div>
      )}
    </div>
  );
};
