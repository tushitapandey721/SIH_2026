"use client";

import React, { useState } from "react";
import { History, X, Plus, Trash2, ArrowRight } from "lucide-react";
import { ConversationItem } from "../types";

interface ChatHistoryDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  conversationsList: ConversationItem[];
  mySessionIds: string[];
  activeConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onDeleteConversation: (id: string, e: React.MouseEvent) => void;
  onNewSession: () => void;
}

export const ChatHistoryDrawer: React.FC<ChatHistoryDrawerProps> = ({
  isOpen,
  onClose,
  conversationsList,
  mySessionIds,
  activeConversationId,
  onSelectConversation,
  onDeleteConversation,
  onNewSession,
}) => {
  const [historyTab, setHistoryTab] = useState<"my" | "archive">("my");

  if (!isOpen) return null;

  const myConversations = conversationsList.filter((c) => mySessionIds.includes(c.id));
  const displayedConversations = historyTab === "my" ? myConversations : conversationsList;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-lg animate-in fade-in duration-200">
      <div className="glass-panel p-6 sm:p-8 rounded-3xl max-w-2xl w-full max-h-[80vh] overflow-y-auto border-amber-500/40 shadow-2xl space-y-5">
        <div className="flex items-center justify-between border-b border-amber-500/20 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-300">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-display text-2xl text-[#f5eedb]">INQUIRY SESSIONS & AUDIT LOGS</h2>
              <p className="text-xs text-stone-400">
                Persistent conversations stored in local SQLite database
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

        {/* Scoped Session Tabs */}
        <div className="flex items-center justify-between border-b border-white/10 pb-3">
          <div className="flex items-center gap-1.5 p-1 bg-black/60 rounded-xl border border-white/5">
            <button
              type="button"
              onClick={() => setHistoryTab("my")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                historyTab === "my"
                  ? "bg-amber-400 text-stone-950 font-bold shadow-sm"
                  : "text-stone-400 hover:text-stone-200"
              }`}
            >
              My Inquiries ({myConversations.length})
            </button>
            <button
              type="button"
              onClick={() => setHistoryTab("archive")}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                historyTab === "archive"
                  ? "bg-amber-400 text-stone-950 font-bold shadow-sm"
                  : "text-stone-400 hover:text-stone-200"
              }`}
            >
              System Archive ({conversationsList.length})
            </button>
          </div>

          <button
            onClick={() => {
              onNewSession();
              onClose();
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-400/15 border border-amber-400/30 hover:bg-amber-400/25 text-amber-300 text-xs font-semibold transition-all cursor-pointer"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>New Session</span>
          </button>
        </div>

        {displayedConversations.length === 0 ? (
          <div className="text-center py-12 text-stone-400 text-sm font-light">
            {historyTab === "my"
              ? "No inquiries saved in this session yet. Ask any question to start recording your personal inquiry history."
              : "No historical conversations found in the system archive."}
          </div>
        ) : (
          <div className="space-y-2.5 max-h-[50vh] overflow-y-auto pr-1">
            {displayedConversations.map((conv) => (
              <div
                key={conv.id}
                onClick={() => onSelectConversation(conv.id)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer flex items-center justify-between gap-3 group ${
                  activeConversationId === conv.id
                    ? "bg-amber-500/15 border-amber-400/60 shadow-[0_0_15px_rgba(234,179,8,0.15)]"
                    : "bg-black/50 border-amber-500/20 hover:border-amber-400/40 hover:bg-stone-900/60"
                }`}
              >
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-semibold text-[#f5eedb] group-hover:text-amber-300 transition-colors truncate">
                      {conv.title}
                    </span>
                    <span className="text-[9px] uppercase font-mono px-2 py-0.5 rounded-full bg-amber-500/10 border border-amber-400/20 text-amber-300 shrink-0">
                      {conv.jurisdiction}
                    </span>
                  </div>
                  <div className="flex items-center gap-3 text-[10px] text-stone-300 font-mono">
                    <span>{conv.message_count} messages</span>
                    <span>•</span>
                    <span>{new Date(conv.updated_at).toLocaleDateString()}</span>
                  </div>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={(e) => onDeleteConversation(conv.id, e)}
                    className="p-1.5 rounded-lg text-stone-400 hover:text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
                    title="Delete conversation"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                  <ArrowRight className="w-4 h-4 text-stone-400 group-hover:text-amber-300 group-hover:translate-x-0.5 transition-all" />
                </div>
              </div>
            ))}
          </div>
        )}

        <div className="flex justify-end pt-2 border-t border-amber-500/15">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-stone-800 text-stone-200 hover:bg-stone-700 font-semibold text-xs transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
