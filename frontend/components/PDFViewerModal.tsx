"use client";

import React from "react";
import { FileText, X, ExternalLink, Download } from "lucide-react";
import { Citation } from "../types";
import { getCitationPdfUrl } from "../lib/constants";

interface PDFViewerModalProps {
  citation: Citation | null;
  isOpen: boolean;
  onClose: () => void;
}

export const PDFViewerModal: React.FC<PDFViewerModalProps> = ({
  citation,
  isOpen,
  onClose,
}) => {
  if (!isOpen || !citation) return null;

  const pdfUrl = getCitationPdfUrl(citation);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 bg-black/90 backdrop-blur-xl animate-in fade-in duration-200">
      <div className="glass-panel rounded-3xl max-w-5xl w-full h-[90vh] flex flex-col border-amber-500/40 shadow-[0_0_50px_rgba(0,0,0,0.8)] overflow-hidden">
        {/* Modal Header */}
        <div className="p-4 sm:p-5 border-b border-amber-500/20 bg-stone-950/80 flex items-center justify-between gap-3 shrink-0">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300 shrink-0">
              <FileText className="w-5 h-5" />
            </div>
            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <h3 className="font-display text-sm sm:text-base font-semibold text-[#f5eedb] truncate">
                  {citation.source}
                </h3>
                {citation.page_number && (
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-500/20 border border-amber-400/40 text-amber-300 shrink-0">
                    Page {citation.page_number}
                  </span>
                )}
              </div>
              <p className="text-xs text-stone-400 font-mono truncate">
                Target Provision: <span className="text-amber-300">{citation.section}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 shrink-0">
            {citation.official_url && (
              <a
                href={citation.official_url}
                target="_blank"
                rel="noopener noreferrer"
                className="hidden sm:inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-stone-900 border border-white/10 hover:border-amber-400/40 text-stone-300 hover:text-amber-200 text-xs font-mono transition-colors"
              >
                <span>Registry Portal</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}

            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-400 text-black font-semibold text-xs hover:bg-amber-300 transition-colors shadow-md"
            >
              <Download className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">New Tab</span>
            </a>

            <button
              onClick={onClose}
              className="p-2 rounded-xl text-stone-400 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Embedded PDF Viewer Frame */}
        <div className="flex-1 bg-stone-950 relative w-full h-full">
          <iframe
            src={pdfUrl}
            title={`Statutory Document: ${citation.source}`}
            className="w-full h-full border-0"
          />
        </div>
      </div>
    </div>
  );
};
