"""LLM clients (Groq with Mistral fallback) and prompt management."""

from app.llm.client import get_completion

__all__ = ["get_completion"]
