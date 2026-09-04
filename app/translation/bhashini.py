"""Government of India Bhashini (National Language Translation Mission) API Client.

Integrates with the Bhashini Dhruva ULCA NMT pipeline with graceful fallback
to the existing legal LLM translator when unconfigured or unreachable.
"""

import os
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

logger = logging.getLogger("IP-SAKTI.Bhashini")

DEFAULT_BHASHINI_URL = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
DEFAULT_TIMEOUT_SEC = 6.0

# Supported Indian language code mapping (ISO-639 / Bhashini language tags)
BHASHINI_LANG_MAP = {
    "en": "en",
    "hi": "hi",
    "sa": "sa",  # Sanskrit
    "bn": "bn",  # Bengali
    "ta": "ta",  # Tamil
    "te": "te",  # Telugu
    "mr": "mr",  # Marathi
    "gu": "gu",  # Gujarati
    "kn": "kn",  # Kannada
    "ml": "ml",  # Malayalam
    "pa": "pa",  # Punjabi
    "or": "or",  # Odia
    "as": "as",  # Assamese
    "ur": "ur",  # Urdu
}


def is_bhashini_configured() -> bool:
    """Checks whether valid Bhashini credentials are present in the environment."""
    api_key = os.getenv("BHASHINI_API_KEY", "").strip()
    user_id = os.getenv("BHASHINI_USER_ID", "").strip()

    if not api_key or api_key in ("your_bhashini_api_key_here", "your_bhashini_api_key"):
        return False
    if not user_id or user_id in ("your_bhashini_user_id_here", "your_bhashini_user_id"):
        return False
    return True


def translate_text(
    text: str,
    source_lang: str,
    target_lang: str,
    timeout: float = DEFAULT_TIMEOUT_SEC,
    inference_url: Optional[str] = None,
) -> Optional[str]:
    """Translates text between Indian languages and English using the Bhashini Dhruva API.

    Args:
        text: Text to be translated.
        source_lang: Source language code (e.g., 'hi', 'en', 'sa').
        target_lang: Target language code (e.g., 'en', 'hi').
        timeout: HTTP request timeout in seconds.
        inference_url: Optional custom endpoint override.

    Returns:
        Translated text string if successful, or None to signal fallback to LLM.
    """
    if not text or not text.strip():
        return text

    src = source_lang.lower().strip()
    tgt = target_lang.lower().strip()

    if src == tgt:
        return text

    if not is_bhashini_configured():
        logger.debug("[Bhashini] Credentials not configured or using placeholders. Skipping Bhashini API.")
        return None

    api_key = os.getenv("BHASHINI_API_KEY", "").strip()
    user_id = os.getenv("BHASHINI_USER_ID", "").strip()
    url = inference_url or os.getenv("BHASHINI_INFERENCE_URL", DEFAULT_BHASHINI_URL).strip()

    src_mapped = BHASHINI_LANG_MAP.get(src, src)
    tgt_mapped = BHASHINI_LANG_MAP.get(tgt, tgt)

    payload: Dict[str, Any] = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": src_mapped,
                        "targetLanguage": tgt_mapped,
                    }
                },
            }
        ],
        "inputData": {
            "input": [
                {
                    "source": text,
                }
            ]
        },
    }

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": api_key,
            "userID": user_id,
            "User-Agent": "IP-SAKTI-Sahayak/1.0",
        },
        method="POST",
    )

    try:
        logger.info(f"[Bhashini] Requesting translation: {src_mapped} -> {tgt_mapped} ({len(text)} chars)...")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            if status_code != 200:
                logger.warning(f"[Bhashini] Non-200 response from Bhashini API: {status_code}")
                return None

            raw_body = response.read().decode("utf-8")
            res_json = json.loads(raw_body)

            pipeline_responses = res_json.get("pipelineResponse", [])
            for p_res in pipeline_responses:
                if p_res.get("taskType") == "translation":
                    outputs = p_res.get("output", [])
                    if outputs and "target" in outputs[0]:
                        translated = outputs[0]["target"].strip()
                        if translated:
                            logger.info(f"[Bhashini] Translation succeeded via Bhashini Dhruva ({src_mapped} -> {tgt_mapped}).")
                            return translated

            logger.warning("[Bhashini] Translation response did not contain expected target field.")
            return None

    except urllib.error.HTTPError as http_err:
        logger.warning(f"[Bhashini] HTTP Error {http_err.code}: {http_err.reason}. Falling back to LLM translator.")
        return None
    except urllib.error.URLError as url_err:
        logger.warning(f"[Bhashini] Connection error: {url_err.reason}. Falling back to LLM translator.")
        return None
    except Exception as exc:
        logger.warning(f"[Bhashini] Unexpected error during translation: {exc}. Falling back to LLM translator.")
        return None
