"use client";

import React from "react";
import { Database, Shield, Globe2, FileText, ExternalLink, X } from "lucide-react";
import { CorpusProvenance } from "../types";
import { API_BASE_URL } from "../lib/constants";

interface CorpusProvenanceModalProps {
  isOpen: boolean;
  onClose: () => void;
  corpusData: CorpusProvenance | null;
}

export const CorpusProvenanceModal: React.FC<CorpusProvenanceModalProps> = ({
  isOpen,
  onClose,
  corpusData,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-lg animate-in fade-in duration-200">
      <div className="glass-panel p-6 sm:p-8 rounded-3xl max-w-4xl w-full max-h-[85vh] overflow-y-auto border-amber-500/40 shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-amber-500/20 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center">
              <Database className="w-5 h-5 text-amber-300" />
            </div>
            <div>
              <h2 className="font-display text-2xl text-[#f5eedb]">CORPUS PROVENANCE & AUTHORITIES</h2>
              <p className="text-xs text-stone-400">
                Dynamically retrieved from verified legal manifest (17 statutory sources)
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-stone-400 hover:text-white hover:bg-white/5 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* National Statutes Group */}
        <div>
          <div className="flex items-center gap-2 mb-3">
            <Shield className="w-4 h-4 text-amber-400" />
            <h3 className="font-display text-lg text-amber-300">
              NATIONAL JURISDICTION (INDIA) — {corpusData?.national_count || 12} SOURCES
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {corpusData?.national.map((doc) => (
              <div
                key={doc.id}
                className="p-3.5 rounded-2xl bg-black/50 border border-amber-500/20 hover:border-amber-400/40 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-xs font-semibold text-[#f5eedb] leading-snug">
                    {doc.title}
                  </h4>
                  <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/30 text-amber-300 shrink-0">
                    {doc.document_type}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between text-[11px] text-stone-400 font-mono">
                  <span>Authority: <strong className="text-stone-300 font-normal">{doc.authority}</strong></span>
                  <span>Year: {doc.year}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-amber-400/80 font-mono mt-1.5">
                  <span>Prefix: {doc.citation_prefix}</span>
                  <div className="flex items-center gap-3">
                    <a
                      href={doc.pdf_url || `${API_BASE_URL}/pdf/${encodeURIComponent(doc.pdf_filename || doc.title)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-amber-300 hover:text-white font-medium underline underline-offset-2"
                    >
                      <FileText className="w-2.5 h-2.5" />
                      <span>Open PDF</span>
                    </a>
                    {doc.official_url && (
                      <a
                        href={doc.official_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-stone-400 hover:text-amber-200 underline underline-offset-2"
                      >
                        <span>Registry</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* International Treaties Group */}
        <div className="pt-4 border-t border-amber-500/15">
          <div className="flex items-center gap-2 mb-3">
            <Globe2 className="w-4 h-4 text-amber-400" />
            <h3 className="font-display text-lg text-amber-300">
              INTERNATIONAL JURISDICTION (TREATIES & CONVENTIONS) — {corpusData?.international_count || 5} SOURCES
            </h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {corpusData?.international.map((doc) => (
              <div
                key={doc.id}
                className="p-3.5 rounded-2xl bg-black/50 border border-amber-500/20 hover:border-amber-400/40 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-xs font-semibold text-[#f5eedb] leading-snug">
                    {doc.title}
                  </h4>
                  <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/30 text-amber-300 shrink-0">
                    {doc.document_type}
                  </span>
                </div>
                <div className="mt-2 flex items-center justify-between text-[11px] text-stone-400 font-mono">
                  <span>Authority: <strong className="text-stone-300 font-normal">{doc.authority}</strong></span>
                  <span>Year: {doc.year}</span>
                </div>
                <div className="flex items-center justify-between text-[10px] text-amber-400/80 font-mono mt-1.5">
                  <span>Prefix: {doc.citation_prefix}</span>
                  <div className="flex items-center gap-3">
                    <a
                      href={doc.pdf_url || `${API_BASE_URL}/pdf/${encodeURIComponent(doc.pdf_filename || doc.title)}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-amber-300 hover:text-white font-medium underline underline-offset-2"
                    >
                      <FileText className="w-2.5 h-2.5" />
                      <span>Open PDF</span>
                    </a>
                    {doc.official_url && (
                      <a
                        href={doc.official_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-stone-400 hover:text-amber-200 underline underline-offset-2"
                      >
                        <span>Registry</span>
                        <ExternalLink className="w-2.5 h-2.5" />
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end pt-3">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-amber-400 text-black font-semibold text-xs hover:bg-amber-300 transition-colors shadow-md cursor-pointer"
          >
            Close Provenance View
          </button>
        </div>
      </div>
    </div>
  );
};
