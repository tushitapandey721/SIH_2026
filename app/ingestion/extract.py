"""PDF extraction engine supporting native PyMuPDF text extraction, targeted ASU extraction for D&C Act, OCR fallback, and text cleaning."""

import io
import re
import os
import logging
from pathlib import Path
from typing import Tuple, Dict, Any, Optional

try:
    import pymupdf as fitz
except ImportError:
    fitz = None

try:
    from PIL import Image
    import pytesseract
except ImportError:
    Image = None
    pytesseract = None

logger = logging.getLogger(__name__)


def has_text_layer(path: str | Path, min_chars_threshold: int = 50, sample_pages: int = 5) -> bool:
    """Checks if a PDF has an extractable text layer using PyMuPDF.

    Args:
        path: Path to the PDF file.
        min_chars_threshold: Minimum average characters per page to consider as having text layer.
        sample_pages: Number of initial pages to sample.

    Returns:
        True if text layer is present and sufficient, False otherwise.
    """
    if fitz is None:
        raise ImportError("PyMuPDF is required. Install via 'pip install pymupdf'.")

    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        doc = fitz.open(str(pdf_path))
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return False

    total_pages = len(doc)
    if total_pages == 0:
        doc.close()
        return False

    pages_to_check = min(total_pages, sample_pages)
    total_chars = 0

    for i in range(pages_to_check):
        page = doc[i]
        text = page.get_text("text").strip()
        total_chars += len(text)

    doc.close()

    avg_chars = total_chars / pages_to_check
    return avg_chars >= min_chars_threshold or total_chars >= (min_chars_threshold * 2)


def extract_native(path: str | Path) -> str:
    """Extracts text page-by-page using PyMuPDF for text-based PDFs.

    Args:
        path: Path to the PDF file.

    Returns:
        Raw concatenated text extracted from all pages.
    """
    if fitz is None:
        raise ImportError("PyMuPDF is required. Install via 'pip install pymupdf'.")

    pdf_path = Path(path)
    doc = fitz.open(str(pdf_path))
    page_texts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            page_texts.append(text)

    doc.close()
    return "\n\n".join(page_texts)


def extract_dc_act_rules_targeted(path: str | Path) -> str:
    """Extracts targeted ASU / Ayurveda relevant statutory and regulatory portions from the 635-page D&C Act & Rules PDF.

    Target ranges:
    1. Act Section 3 (Definitions of ASU Drug, Patent/Proprietary medicine, Cosmetic, Drug) [Pages 6-10]
    2. Act Chapter IV-A (Sections 33A-33N, 33D Consultative Committee, 33EEA, 33EEC, First Schedule) [Pages 25-37]
    3. Rule 122E (New Drugs / Phytopharmaceuticals) [Pages 138-142]
    4. Rules Part XVI & XVII (Rules 151-170, Rule 158B Licensing Guidelines, Standards & Labelling) [Pages 177-202]
    5. Schedule T (Good Manufacturing Practices for ASU Drugs) [Pages 473-478]
    """
    if fitz is None:
        raise ImportError("PyMuPDF is required. Install via 'pip install pymupdf'.")

    pdf_path = Path(path)
    doc = fitz.open(str(pdf_path))

    ranges = [
        (5, 10),    # Act Section 3 (Definitions)
        (24, 37),   # Act Chapter IV-A (Sections 33A - 33N + First Schedule)
        (137, 142), # Rule 122E (New Drugs / Phytopharmaceuticals)
        (176, 202), # Rules Part XVI & XVII (Rules 151 - 170, Rule 158B)
        (472, 478), # Schedule T (GMP for ASU Drugs)
    ]

    extracted = []
    for start, end in ranges:
        for p in range(start, min(end, len(doc))):
            text = doc[p].get_text("text")
            if text.strip():
                extracted.append(text)

    doc.close()
    return "\n\n".join(extracted)


def extract_scanned(path: str | Path, dpi: int = 200) -> str:
    """Extracts text from scanned PDFs without a text layer using OCR."""
    if fitz is None:
        raise ImportError("PyMuPDF is required. Install via 'pip install pymupdf'.")
    if pytesseract is None or Image is None:
        raise ImportError("pytesseract and Pillow are required for OCR fallback.")

    pdf_path = Path(path)
    doc = fitz.open(str(pdf_path))
    ocr_texts = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)

        img_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_bytes))

        try:
            page_text = pytesseract.image_to_string(image, lang="eng")
            if page_text.strip():
                ocr_texts.append(page_text)
        except Exception as e:
            logger.warning(f"OCR failed on page {page_num + 1} of {pdf_path.name}: {e}")
            ocr_texts.append(f"[OCR Extraction Warning: {e}]")

    doc.close()
    return "\n\n".join(ocr_texts)


def clean_text(text: str) -> str:
    """Strips repeated headers, footers, page numbers, and collapses excess whitespace."""
    if not text:
        return ""

    # Replace null and non-printable control characters
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", " ", text)

    # Remove standalone page numbers or "Page X of Y" / "Page X" patterns
    text = re.sub(r"(?im)^\s*(?:page\s+\d+(?:\s*(?:of|/)\s*\d+)?|\d+)\s*$", "", text)

    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Replace multiple horizontal spaces/tabs on a line with a single space
    lines = []
    for line in text.split("\n"):
        cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
        lines.append(cleaned_line)

    rejoined = "\n".join(lines)

    # Collapse 3 or more consecutive newlines into double newline
    cleaned = re.sub(r"\n{3,}", "\n\n", rejoined)

    return cleaned.strip()


def extract_document(path: str | Path) -> Tuple[str, str]:
    """Auto-detects extraction method and returns cleaned text and method used."""
    pdf_path = Path(path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")

    # For the 635-page full D&C Act + Rules, apply the targeted ASU / Ayurveda statutory extraction
    if "2016drugsandcosmeticsact" in pdf_path.name.lower():
        raw_text = extract_dc_act_rules_targeted(pdf_path)
        method = "targeted_native"
    elif has_text_layer(pdf_path):
        raw_text = extract_native(pdf_path)
        method = "native"
    else:
        raw_text = extract_scanned(pdf_path)
        method = "OCR"

    cleaned = clean_text(raw_text)
    return cleaned, method


def locate_corpus_file(filename: str, base_dir: Optional[str | Path] = None) -> Optional[Path]:
    """Helper to locate a corpus file across national and international folders."""
    base = Path(base_dir) if base_dir else Path(__file__).resolve().parent.parent.parent / "data" / "corpus"
    candidates = [
        base / "national" / filename,
        base / "international" / filename,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    clean_target = filename.lower().replace("_", " ").replace("-", " ")
    for p in base.rglob("*.pdf"):
        if p.name.lower() == filename.lower():
            return p
        p_clean = p.name.lower().replace("_", " ").replace("-", " ")
        if clean_target in p_clean or p_clean in clean_target:
            return p

    return None
