"use client";

import React from "react";
import { Scale, X } from "lucide-react";

interface FacilitatorModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const FacilitatorModal: React.FC<FacilitatorModalProps> = ({
  isOpen,
  onClose,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="glass-panel p-6 sm:p-7 rounded-3xl max-w-lg w-full border-amber-500/40 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-amber-500/20 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300">
              <Scale className="w-4 h-4 text-amber-400" />
            </div>
            <h3 className="font-display text-xl text-[#f5eedb]">HUMAN IP FACILITATOR</h3>
          </div>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-white p-1 rounded hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <p className="text-sm text-stone-300 leading-relaxed font-light">
          Since the automated statutory corpus did not contain high-confidence provisions for this inquiry, you can connect directly with registered Ayush patent attorneys and regulatory facilitators.
        </p>

        <div className="space-y-2 text-xs font-mono text-stone-400 bg-black/40 p-4 rounded-xl border border-amber-500/20">
          <div><span className="text-stone-500">Facilitation Desk:</span> <strong className="text-stone-300 font-normal">AYUSH IP Facilitation Cell (AIPFC)</strong></div>
          <div><span className="text-stone-500">Email:</span> <strong className="text-amber-300/90 font-normal">ip-facilitator@ayush-sahayak.gov.in</strong></div>
          <div><span className="text-stone-500">Emergency Clearance:</span> Form 25D / Rule 158B Expedited</div>
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl bg-amber-400 text-black font-semibold text-xs hover:bg-amber-300 transition-colors shadow-md cursor-pointer"
          >
            Close & Return to Assistant
          </button>
        </div>
      </div>
    </div>
  );
};
