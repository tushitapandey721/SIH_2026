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


GROQ_CANDIDATE_MODELS = [
    "openai/gpt-oss-120b",
    "openai/gpt-oss-20b",
    "qwen/qwen3.6-27b",
]


def _call_groq(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1024,
    model: Optional[str] = None,
) -> str:
    """Invokes the Groq API for chat completion with max_retries=0 and candidate failover."""
    import groq

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.strip() in ("", "gsk_your_groq_api_key_here"):
        raise ValueError("GROQ_API_KEY is not set or contains default placeholder.")

    # max_retries=0 disables internal exponential backoff so 429 raises immediately
    client = groq.Groq(api_key=api_key, max_retries=0)
    
    primary = model or DEFAULT_GROQ_MODEL
    models_to_try = [primary] + [m for m in GROQ_CANDIDATE_MODELS if m != primary]

    last_err = None
    for model_name in models_to_try:
        try:
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

            if response.choices:
                content = response.choices[0].message.content
                return str(content).strip() if content is not None else ""
        except Exception as e:
            last_err = e
            if _is_rate_limit_error(e):
                logger.warning(f"[Groq Model Failover] 429 on {model_name}, trying next candidate model...")
                continue
            raise e

    if last_err:
        raise last_err
    raise RuntimeError("All Groq candidate models failed.")


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
    """Retrieves completion by first attempting Groq with candidate fallback and immediately falling back to Mistral."""
    # 1. Attempt Groq
    try:
        text = _call_groq(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            model=groq_model,
        )
        msg = f"[LLM Provider] Served by Groq"
        logger.info(msg)
        print(msg)
        return {
            "text": text,
            "provider_used": "groq",
        }
    except Exception as groq_err:
        warn_msg = f"[LLM Provider] Groq calls failed ({groq_err}). Falling back to Mistral ({mistral_model})..."
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
    """Streams completion chunks across Groq candidate models and Mistral fallback.

    Yields:
        Dict with keys:
            - 'delta': The token string fragment.
            - 'provider': 'groq' | 'mistral'
    """
    import groq

    api_key = os.getenv("GROQ_API_KEY")
    if api_key and api_key.strip() not in ("", "gsk_your_groq_api_key_here"):
        client = groq.Groq(api_key=api_key, max_retries=0)
        primary = groq_model or DEFAULT_GROQ_MODEL
        models_to_try = [primary] + [m for m in GROQ_CANDIDATE_MODELS if m != primary]

        for model_name in models_to_try:
            try:
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
                yielded_any = False
                for chunk in stream:
                    delta = chunk.choices[0].delta.content if chunk.choices else None
                    if delta:
                        yielded_any = True
                        yield {"delta": delta, "provider": "groq"}
                if yielded_any:
                    return
            except Exception as e:
                if _is_rate_limit_error(e):
                    logger.warning(f"[Groq Stream Failover] 429 on {model_name}, trying next model...")
                    continue
                logger.warning(f"[Groq Stream Error] {e}")
                break

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



