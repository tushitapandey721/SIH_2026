"use client";

import React, { useState } from "react";
import { ThumbsUp, ThumbsDown, CheckCircle2 } from "lucide-react";
import { Citation } from "../types";

interface FeedbackDrawerProps {
  messageId: string;
  messageContent: string;
  citations?: Citation[];
  feedbackState?: {
    rating?: "up" | "down";
    showCommentInput?: boolean;
    comment?: string;
    submitted?: boolean;
  };
  onFeedback: (
    messageId: string,
    rating: "up" | "down",
    comment?: string,
    msgContent?: string,
    citations?: Citation[]
  ) => void;
}

export const FeedbackDrawer: React.FC<FeedbackDrawerProps> = ({
  messageId,
  messageContent,
  citations,
  feedbackState,
  onFeedback,
}) => {
  const [localComment, setLocalComment] = useState("");

  const diagnosticTags = [
    "Wrong jurisdiction",
    "Missing citation",
    "Confusing answer",
    "Outdated statute reference",
  ];

  if (feedbackState?.submitted) {
    return (
      <span className="inline-flex items-center gap-1 text-[11px] text-amber-300/90 font-sans font-medium">
        <CheckCircle2 className="w-3 h-3 text-amber-400" />
        <span>{feedbackState.rating === "up" ? "Helpful" : "Feedback recorded"}</span>
      </span>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center gap-1">
        <button
          type="button"
          onClick={() => onFeedback(messageId, "up", undefined, messageContent, citations)}
          title="Mark answer as helpful and accurate"
          className="p-1 rounded text-stone-400 hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors cursor-pointer"
        >
          <ThumbsUp className="w-3.5 h-3.5" />
        </button>
        <button
          type="button"
          onClick={() => onFeedback(messageId, "down", undefined, messageContent, citations)}
          title="Report inaccurate or unhelpful guidance"
          className="p-1 rounded text-stone-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors cursor-pointer"
        >
          <ThumbsDown className="w-3.5 h-3.5" />
        </button>
      </div>

      {feedbackState?.showCommentInput && (
        <div className="mt-2.5 p-3 rounded-xl bg-black/60 border border-amber-500/30 space-y-2 text-xs">
          <div className="flex items-center justify-between text-[11px] text-stone-300">
            <span>Help us improve this statutory answer:</span>
            <button
              type="button"
              onClick={() => onFeedback(messageId, "down", "", messageContent, citations)}
              className="text-stone-400 hover:text-stone-200 text-[11px] cursor-pointer"
            >
              Dismiss
            </button>
          </div>

          {/* Quick-select reason tags */}
          <div className="flex flex-wrap gap-1.5">
            {diagnosticTags.map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => onFeedback(messageId, "down", tag, messageContent, citations)}
                className="px-2.5 py-1 rounded-lg bg-stone-900 hover:bg-amber-950/60 border border-stone-700 hover:border-amber-400/50 text-stone-300 hover:text-amber-200 text-[11px] font-sans transition-all cursor-pointer"
              >
                {tag}
              </button>
            ))}
          </div>

          {/* Free-text comment input */}
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Specific feedback note..."
              value={localComment}
              onChange={(e) => setLocalComment(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  onFeedback(messageId, "down", localComment, messageContent, citations);
                }
              }}
              className="flex-1 px-3 py-1.5 rounded-lg bg-stone-900 border border-white/10 focus:border-amber-400/60 outline-none text-stone-200 text-xs placeholder-stone-500"
            />
            <button
              type="button"
              onClick={() => onFeedback(messageId, "down", localComment, messageContent, citations)}
              className="px-3 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-black font-semibold text-xs transition-colors cursor-pointer"
            >
              Submit
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
