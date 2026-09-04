/**
 * Normalizes statutory legal text for natural, accurate SpeechSynthesis playback.
 * Converts Section 3(p) -> Section 3 p, Rule 158-B -> Rule 158 B, expands Indian legal acronyms, and strips markdown symbols.
 */
export function cleanLegalTextForTTS(text: string): string {
  if (!text) return "";
  let cleaned = text;

  // 1. Remove markdown bold/italics markers first before matching words
  cleaned = cleaned.replace(/\*\*([^*]+)\*\*/g, "$1");
  cleaned = cleaned.replace(/\*([^*]+)\*/g, "$1");
  cleaned = cleaned.replace(/__([^_]+)__/g, "$1");
  cleaned = cleaned.replace(/_([^_]+)_/g, "$1");

  // 2. Expand common Indian legal & regulatory acronyms for natural pronunciation
  cleaned = cleaned.replace(/\bTKDL\b/g, "T K D L, Traditional Knowledge Digital Library");
  cleaned = cleaned.replace(/\bABS\b/g, "A B S, Access and Benefit Sharing");
  cleaned = cleaned.replace(/\bNBA\b/g, "National Biodiversity Authority");
  cleaned = cleaned.replace(/\bSBBs?\b/g, "State Biodiversity Board");
  cleaned = cleaned.replace(/\bBMC\b/g, "Biodiversity Management Committee");
  cleaned = cleaned.replace(/\bBDA\b/g, "Biological Diversity Act");
  cleaned = cleaned.replace(/\bAYUSH\b/g, "Ayush");
  cleaned = cleaned.replace(/\bASU\b/g, "Ayurveda, Siddha, and Unani");
  cleaned = cleaned.replace(/\bASU&H\b/g, "Ayurveda, Siddha, Unani and Homeopathy");
  cleaned = cleaned.replace(/\bD&C\b/g, "Drugs and Cosmetics");
  cleaned = cleaned.replace(/\bCDSCO\b/g, "Central Drugs Standard Control Organisation");
  cleaned = cleaned.replace(/\bFSSAI\b/g, "F S S A I");
  cleaned = cleaned.replace(/\bIPC\b/g, "Indian Pharmacopoeia Commission");
  cleaned = cleaned.replace(/\bTRIPS\b/g, "Trips Agreement");
  cleaned = cleaned.replace(/\bCBD\b/g, "Convention on Biological Diversity");
  cleaned = cleaned.replace(/\bGRATK\b/g, "G R A T K Treaty");
  cleaned = cleaned.replace(/\bPCT\b/g, "Patent Cooperation Treaty");
  cleaned = cleaned.replace(/\bWIPO\b/g, "World Intellectual Property Organization");
  cleaned = cleaned.replace(/\bIPR\b/g, "Intellectual Property Rights");
  cleaned = cleaned.replace(/\bFER\b/g, "First Examination Report");

  // 3. Spoken statutory section & subclause normalization
  cleaned = cleaned.replace(/Section\s+(\d+)\s*\(([a-zA-Z0-9]+)\)\s*\(([a-zA-Z0-9]+)\)/gi, "Section $1 $2 $3");
  cleaned = cleaned.replace(/Section\s+(\d+)\s*\(([a-zA-Z0-9]+)\)/gi, "Section $1 $2");
  cleaned = cleaned.replace(/Rule\s+(\d+)\s*[-–—]\s*([a-zA-Z0-9]+)/gi, "Rule $1 $2");
  cleaned = cleaned.replace(/Rule\s+(\d+)\s*\(([a-zA-Z0-9]+)\)/gi, "Rule $1 $2");
  cleaned = cleaned.replace(/Form\s+(\d+)\s*[-–—]\s*([a-zA-Z0-9]+)/gi, "Form $1 $2");
  cleaned = cleaned.replace(/Form\s+(\d+)([a-zA-Z]+)/gi, "Form $1 $2");
  cleaned = cleaned.replace(/\s*\(([0-9]+)\)/g, " subsection $1");

  // 4. Remove markdown headers, bullets, links, code blocks
  cleaned = cleaned.replace(/`{1,3}[^`]*`{1,3}/g, "");
  cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, "$1");
  cleaned = cleaned.replace(/^#+\s+/gm, "");
  cleaned = cleaned.replace(/^\s*[-*+]\s+/gm, "");

  // 5. HTML entities
  cleaned = cleaned.replace(/&bull;/g, " ");
  cleaned = cleaned.replace(/&mdash;/g, " — ");
  cleaned = cleaned.replace(/&amp;/g, " and ");
  cleaned = cleaned.replace(/&quot;/g, '"');
  cleaned = cleaned.replace(/&apos;/g, "'");

  // 6. Excess whitespace & punctuation smoothing
  cleaned = cleaned.replace(/\n+/g, ". ");
  cleaned = cleaned.replace(/\s+/g, " ").trim();

  return cleaned;
}
