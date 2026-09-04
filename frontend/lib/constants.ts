import { Citation, SamplePrompt } from "../types";

export const SAMPLE_PROMPTS: SamplePrompt[] = [
  {
    title: "Compare: Traditional Knowledge Patenting",
    query: "Can I patent traditional knowledge?",
    jurisdiction: "national",
    answers: {},
    is_compare: true,
  },
  {
    title: "TKDL Classical Joint Oil",
    query: "My grandmother gave me a family recipe for a herbal joint pain oil made from classical Ayurvedic texts — can I patent it?",
    jurisdiction: "national",
    answers: {},
  },
  {
    title: "ABS Kerala Herbal Export",
    query: "I want to export a herbal supplement made from a plant sourced in Kerala — what approval do I need?",
    jurisdiction: "national",
    answers: {},
  },
  {
    title: "Classical Patentability",
    query: "Is a classical Ayurvedic formulation patentable under Indian Patent Law?",
    jurisdiction: "national",
    answers: { is_first_schedule_text: true },
  },
  {
    title: "Rule 158-B ASU Proof",
    query: "What safety and efficacy proof is required for a new Ayurvedic drug vs classical medicine?",
    jurisdiction: "national",
    answers: { is_first_schedule_text: false, requires_new_safety_efficacy: true },
  },
  {
    title: "Biodiversity Export Clearance",
    query: "Does an Ayurvedic company need NBA approval before exporting Indian biological resources?",
    jurisdiction: "national",
    answers: { is_first_schedule_text: false },
  },
  {
    title: "International Nagoya Access",
    query: "What are the prior informed consent rules under the Nagoya Protocol for traditional knowledge?",
    jurisdiction: "international",
    answers: {},
  },
];

export const TRANSLATE_LANGUAGES = [
  { code: "en", name: "English", native: "English", script: "Latin", short: "EN" },
  { code: "hi", name: "Hindi", native: "हिन्दी", script: "Devanagari", short: "HI" },
  { code: "pa", name: "Punjabi", native: "ਪੰਜਾਬੀ", script: "Gurmukhi", short: "PA" },
  { code: "ml", name: "Malayalam", native: "മലയാളം", script: "Malayalam", short: "ML" },
  { code: "ta", name: "Tamil", native: "தமிழ்", script: "Tamil", short: "TA" },
] as const;

export const VOICE_LANGUAGES = [
  { code: "en-IN", name: "English", short: "EN" },
  { code: "hi-IN", name: "Hindi", short: "HI" },
  { code: "pa-IN", name: "Punjabi", short: "PA" },
  { code: "ta-IN", name: "Tamil", short: "TA" },
  { code: "ml-IN", name: "Malayalam", short: "ML" },
] as const;

export const SPEECH_LANG_MAP: Record<string, string> = {
  en: "en-IN",
  hi: "hi-IN",
  pa: "pa-IN",
  ml: "ml-IN",
  ta: "ta-IN",
};

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"
).trim().replace(/\/+$/, "");

/**
 * Statutory Section-to-Page Index for Deep-Linking
 */
export const STATUTORY_PDF_PAGES: Record<string, Record<string, number>> = {
  "Patents Act, 1970.pdf": {
    "3(p)": 12, "3(d)": 11, "3(a)": 11, "3(e)": 11, "3": 11,
    "2(1)(ja)": 8, "2(1)(j)": 8, "2": 6, "25": 26, "64": 54,
  },
  "2016DrugsandCosmeticsAct1940Rules1945.pdf": {
    "158-b": 189, "158b": 189, "154-a": 185, "154a": 185, "161": 193,
    "122-e": 138, "122e": 138, "3(a)": 6, "3(h)": 7, "33a": 25, "33e": 27,
  },
  "Biological Diversity (Amendment) Act, 2023.pdf": {
    "3": 3, "4": 4, "6": 5, "7": 6, "19": 11, "20": 12, "21": 13,
  },
  "The Biological Diversity Rules, 2024.pdf": {
    "14": 9, "15": 10, "16": 11, "18": 14,
  },
  "trips_agreement.pdf": {
    "27": 13, "28": 14, "29": 14, "8": 4, "7": 4,
  },
  "Nagoya Protocol.pdf": {
    "5": 4, "6": 5, "7": 6, "15": 9, "12": 8,
  },
  "Convention on Biological Diversity (CBD).pdf": {
    "1": 2, "8(j)": 6, "15": 9, "16": 10,
  },
  "WIPO GRATK Treaty (2024).pdf": {
    "3": 4, "4": 5, "6": 6,
  },
  "PCT (Patent Cooperation Treaty).pdf": {
    "1": 3, "11": 8, "19": 13, "33": 19,
  },
};

/**
 * Resolves the statutory source PDF file URL to view official Act / Treaty documents with #page=X deep linking.
 */
export function getCitationPdfUrl(cit: Citation): string {
  // If backend provided a relative or full PDF URL, rewrite host to active API_BASE_URL
  if (cit.pdf_url && cit.pdf_url.trim()) {
    const rawUrl = cit.pdf_url.trim();
    if (rawUrl.startsWith("http://localhost:8000")) {
      return rawUrl.replace("http://localhost:8000", API_BASE_URL);
    }
    if (rawUrl.startsWith("/pdf/")) {
      return `${API_BASE_URL}${rawUrl}`;
    }
    return rawUrl;
  }
  
  if (cit.url && cit.url.includes("/pdf/")) {
    const idx = cit.url.indexOf("/pdf/");
    return `${API_BASE_URL}${cit.url.slice(idx)}`;
  }

  const text = `${cit.source || ""} ${cit.section || ""}`.toLowerCase();
  let filename = "Patents Act, 1970.pdf";

  if (text.includes("pct") || text.includes("patent cooperation")) {
    filename = "PCT (Patent Cooperation Treaty).pdf";
  } else if (text.includes("gratk")) {
    filename = "WIPO GRATK Treaty (2024).pdf";
  } else if (text.includes("nagoya")) {
    filename = "Nagoya Protocol.pdf";
  } else if (text.includes("trips") || text.includes("wto")) {
    filename = "trips_agreement.pdf";
  } else if (text.includes("cbd") || text.includes("convention on biological diversity")) {
    filename = "Convention on Biological Diversity (CBD).pdf";
  } else if (text.includes("magic remedies") || text.includes("dmr") || text.includes("advertisement")) {
    filename = "Drugs and Magic Remedies (Objectionable Advertisements) Act.pdf";
  } else if (text.includes("aahara") || text.includes("fssai")) {
    filename = "Gazette_Notification_Ayurveda_Aahara.pdf";
  } else if (text.includes("phytopharmaceutical") || text.includes("ipc")) {
    filename = "Phytopharmaceutical-Drugs-General-Guidance-for-Development.pdf";
  } else if (text.includes("2025") && (text.includes("rule") || text.includes("diversity"))) {
    filename = "The Biological Diversity (Amendment) Rules, 2025.pdf";
  } else if (text.includes("bd rules") || (text.includes("rule") && text.includes("diversity")) || text.includes("rules, 2024")) {
    filename = "The Biological Diversity Rules, 2024.pdf";
  } else if (text.includes("biological diversity") || text.includes("bda") || text.includes("biodiversity")) {
    filename = "Biological Diversity (Amendment) Act, 2023.pdf";
  } else if (text.includes("drug") || text.includes("cosmetic") || text.includes("d&c") || text.includes("158-b") || text.includes("158b") || text.includes("schedule t") || text.includes("schedule e")) {
    filename = "2016DrugsandCosmeticsAct1940Rules1945.pdf";
  } else if (text.includes("trademark") || text.includes("trade mark") || text.includes("tm act")) {
    filename = "The Trade Marks Act, 1999.pdf";
  } else if (text.includes("copyright")) {
    filename = "The Copyright Act, 1957.pdf";
  } else if (text.includes("geographical indication") || text.includes("gi act")) {
    filename = "Geographical Indications of Goods.pdf";
  } else if (text.includes("design")) {
    filename = "The Designs Act, 2000 (Act No. 16 of 2000).pdf";
  } else if (text.includes("patent")) {
    filename = "Patents Act, 1970.pdf";
  }

  // Calculate page number anchor
  let pageNo = cit.page_number;
  if (!pageNo && STATUTORY_PDF_PAGES[filename]) {
    const secKey = (cit.section || "").toLowerCase().replace(/^(section|rule|art\.|article|reg\.)\s+/i, "").trim();
    if (STATUTORY_PDF_PAGES[filename][secKey]) {
      pageNo = STATUTORY_PDF_PAGES[filename][secKey];
    }
  }

  const anchor = pageNo ? `#page=${pageNo}` : "";
  return `${API_BASE_URL}/pdf/${encodeURIComponent(filename)}${anchor}`;
}
