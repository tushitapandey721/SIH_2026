"""Unified LLM Client with Groq primary and Mistral fallback with zero-backoff 429 failover."""

import os
import re
import time
import logging
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("IP-SAKTI.LLMClient")

# Model configurations
DEFAULT_GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
DEFAULT_MISTRAL_MODEL = os.getenv("MISTRAL_MODEL", "mistral-small-latest")


def _is_rate_limit_error(exc: Exception) -> bool:
    """Detects whether an exception represents a 429 Rate Limit error."""
    try:
        import groq
        if isinstance(exc, groq.RateLimitError):
            return True
    except Exception:
        pass

    status_code = getattr(exc, "status_code", None)
    if status_code == 429:
        return True

    err_str = str(exc).lower()
    return "429" in err_str or "rate limit" in err_str or "rate_limit" in err_str or "tpm" in err_str or "rpm" in err_str


def _call_groq(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    model: Optional[str] = None,
) -> str:
    """Invokes the Groq API for chat completion with max_retries=0 for immediate 429 failover."""
    import groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.strip() in ("", "gsk_your_groq_api_key_here"):
        raise ValueError("GROQ_API_KEY is not set or contains default placeholder.")

    model_name = model or DEFAULT_GROQ_MODEL
    # max_retries=0 disables internal exponential backoff so 429 raises immediately
    client = groq.Groq(api_key=api_key, max_retries=0)

    extra_params = {}
    if "gpt-oss" in model_name.lower():
        extra_params["reasoning_effort"] = "low"

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        **extra_params,
    )

    if not response.choices:
        raise ValueError("Groq returned empty choices.")

    content = response.choices[0].message.content
    return str(content).strip() if content is not None else ""


def _call_mistral(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    model: Optional[str] = None,
) -> str:
    """Invokes the Mistral API for chat completion."""
    try:
        from mistralai import Mistral
    except ImportError:
        from mistralai.client import Mistral

    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key or api_key.strip() in ("", "your_mistral_api_key_here"):
        raise ValueError("MISTRAL_API_KEY is not set or contains default placeholder.")

    raw_model = model or DEFAULT_MISTRAL_MODEL
    # Normalize model identifier if user passed human-readable name like 'Mistral Small 4'
    if raw_model.strip().lower() in ("mistral small 4", "mistral-small-4", "mistral-small"):
        model_name = "mistral-small-latest"
    else:
        model_name = raw_model

    client = Mistral(api_key=api_key)

    response = client.chat.complete(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
    )

    if not response.choices:
        raise ValueError("Mistral returned empty choices.")

    content = response.choices[0].message.content
    if isinstance(content, list):
        text = "".join(c if isinstance(c, str) else getattr(c, "text", str(c)) for c in content)
    else:
        text = str(content) if content is not None else ""

    return text.strip()


def get_completion(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    groq_model: str = "openai/gpt-oss-120b",
    mistral_model: str = "Mistral Small 4",
) -> Dict[str, str]:
    """Retrieves completion by first attempting Groq with max_retries=0 and immediately falling back to Mistral.

    Args:
        system_prompt: The system instruction / context.
        user_prompt: The user query or prompt.
        max_tokens: Maximum tokens in response.
        groq_model: Primary model identifier for Groq.
        mistral_model: Fallback model identifier for Mistral.

    Returns:
        Dict with keys:
            - 'text': The generated completion text.
            - 'provider_used': 'groq' | 'mistral'
    """
    # 1. Attempt Groq
    try:
        text = _call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            model=groq_model,
        )
        msg = f"[LLM Provider] Served by Groq (model: {groq_model})"
        logger.info(msg)
        print(msg)
        return {
            "text": text,
            "provider_used": "groq",
        }
    except Exception as groq_err:
        if _is_rate_limit_error(groq_err):
            # Check if error specifies a short retry window (e.g. 10s TPM burst)
            m = re.search(r"try again in (\d+\.?\d*)s", str(groq_err))
            wait_s = float(m.group(1)) if m else 3.0
            if wait_s <= 15.0:
                retry_log = f"[RATE LIMIT RETRY] Groq 429 TPM burst: waiting {wait_s:.1f}s before retry..."
                logger.warning(retry_log)
                print(retry_log)
                time.sleep(wait_s + 0.5)
                try:
                    text = _call_groq(
                        system_prompt=system_prompt,
                        user_prompt=user_prompt,
                        max_tokens=max_tokens,
                        model=groq_model,
                    )
                    return {
                        "text": text,
                        "provider_used": "groq",
                    }
                except Exception as retry_err:
                    groq_err = retry_err

            rate_limit_msg = (
                f"[RATE LIMIT FALLBACK] Groq 429 RateLimitError (TPM/RPM quota reached on free-tier: {groq_err}). "
                f"Failing over to Mistral ({mistral_model})..."
            )
            logger.warning(rate_limit_msg)
            print(rate_limit_msg)
        else:
            warn_msg = f"[LLM Provider] Groq call failed ({groq_err}). Falling back to Mistral ({mistral_model})..."
            logger.warning(warn_msg)
            print(warn_msg)

    # 2. Fallback to Mistral
    try:
        text = _call_mistral(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            model=mistral_model,
        )
        msg = f"[LLM Provider] Served by Mistral (model: {mistral_model})"
        logger.info(msg)
        print(msg)
        return {
            "text": text,
            "provider_used": "mistral",
        }
    except Exception as mistral_err:
        err_msg = f"[LLM Provider] Both Groq and Mistral providers failed. Mistral error: {mistral_err}"
        logger.error(err_msg)
        print(err_msg)
        raise RuntimeError(err_msg) from mistral_err


def stream_completion(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    groq_model: str = "openai/gpt-oss-120b",
    mistral_model: str = "Mistral Small 4",
):
    """Streams completion chunks from Groq (primary, max_retries=0) or Mistral (fallback).

    Yields:
        Dict with keys:
            - 'delta': The token string fragment.
            - 'provider': 'groq' | 'mistral'
    """
    import groq

    api_key = os.getenv("GROQ_API_KEY")
    if api_key and api_key.strip() not in ("", "gsk_your_groq_api_key_here"):
        try:
            # max_retries=0 disables internal exponential backoff so 429 raises immediately
            client = groq.Groq(api_key=api_key, max_retries=0)
            model_name = groq_model or DEFAULT_GROQ_MODEL
            extra_params = {}
            if "gpt-oss" in model_name.lower():
                extra_params["reasoning_effort"] = "low"

            stream = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                stream=True,
                **extra_params,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield {"delta": delta, "provider": "groq"}
            return
        except Exception as e:
            if _is_rate_limit_error(e):
                rate_msg = (
                    f"[RATE LIMIT FALLBACK] Groq 429 RateLimitError during streaming (TPM/RPM quota reached). "
                    f"ZERO backoff wait — immediately switching stream to Mistral ({mistral_model})..."
                )
                logger.warning(rate_msg)
                print(rate_msg)
            else:
                warn_msg = f"[LLM Provider] Groq streaming failed ({e}), falling back to Mistral ({mistral_model})..."
                logger.warning(warn_msg)
                print(warn_msg)

    # Fallback to Mistral
    try:
        from mistralai import Mistral
    except ImportError:
        from mistralai.client import Mistral

    m_key = os.getenv("MISTRAL_API_KEY")
    if m_key and m_key.strip() not in ("", "your_mistral_api_key_here"):
        try:
            client = Mistral(api_key=m_key)
            m_model = "mistral-small-latest" if mistral_model.strip().lower() in ("mistral small 4", "mistral-small-4", "mistral-small") else mistral_model
            response = client.chat.stream(
                model=m_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
            )
            for chunk in response:
                delta = chunk.data.choices[0].delta.content if chunk.data.choices else None
                if delta:
                    yield {"delta": delta, "provider": "mistral"}
            return
        except Exception as e:
            logger.error(f"Mistral streaming failed: {e}")
            raise RuntimeError(f"Both LLM streaming providers failed: {e}")


