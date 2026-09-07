import os
import logging
from typing import Optional, Any
from app.config import settings

logger = logging.getLogger(__name__)

def stringify_content(content: Any) -> str:
    """
    Safely converts LLM message content into a clean string.
    Handles strings, lists of content dicts (as returned by Gemini 3.5/3.7), and other formats.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = []
        for item in content:
            if isinstance(item, str):
                text_parts.append(item)
            elif isinstance(item, dict) and "text" in item:
                text_parts.append(str(item["text"]))
            elif hasattr(item, "text"):
                text_parts.append(str(item.text))
            else:
                text_parts.append(str(item))
        return "".join(text_parts).strip()
    return str(content)

_llm_cache: dict = {}

def clear_llm_cache() -> None:
    """Clears the in-memory LLM cache."""
    _llm_cache.clear()

def get_llm(temperature: Optional[float] = None) -> Any:
    """
    Returns a cached/reusable LangChain ChatModel instance configured via environment variables.
    Supports Google Gemini (default) and OpenAI, with fast failover and intelligent error recovery.
    """
    temp = temperature if temperature is not None else settings.GEMINI_TEMPERATURE
    cache_key = f"{settings.LLM_PROVIDER}_{temp}_{settings.GEMINI_MODEL}_{settings.GEMINI_MODELS}"
    
    if cache_key in _llm_cache:
        return _llm_cache[cache_key]

    if settings.LLM_PROVIDER == "openai" or (not settings.GEMINI_API_KEY and settings.OPENAI_API_KEY):
        try:
            from langchain_openai import ChatOpenAI
            logger.info(f"Using OpenAI model: {settings.OPENAI_MODEL}")
            instance = ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=temp,
                api_key=settings.OPENAI_API_KEY,
                request_timeout=10.0,
                max_retries=1,
            )
            _llm_cache[cache_key] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to initialize ChatOpenAI: {e}")

    # Default to Gemini with automatic model fallback chain
    if settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # Parse models list from settings
            raw_models = [m.strip() for m in settings.GEMINI_MODELS.split(",") if m.strip()]
            if settings.GEMINI_MODEL and settings.GEMINI_MODEL not in raw_models:
                raw_models.insert(0, settings.GEMINI_MODEL)
            if not raw_models:
                raw_models = ["gemini-3.5-flash-lite", "gemini-3.6-flash", "gemini-flash-lite-latest"]

            primary_model = raw_models[0]
            fallback_model_names = raw_models[1:]
            logger.info(f"Initializing Gemini LLM with primary: {primary_model} and fallbacks: {fallback_model_names}")

            primary_llm = ChatGoogleGenerativeAI(
                model=primary_model,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=temp,
                request_timeout=10.0,
                max_retries=1,
            )

            fallback_llms = [
                ChatGoogleGenerativeAI(
                    model=m,
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=temp,
                    request_timeout=10.0,
                    max_retries=1,
                )
                for m in fallback_model_names
            ]

            if fallback_llms:
                instance = primary_llm.with_fallbacks(fallback_llms)
            else:
                instance = primary_llm

            _llm_cache[cache_key] = instance
            return instance
        except Exception as e:
            logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")

    logger.warning("No valid LLM configuration found. Agent will utilize rule-based fallbacks where needed.")
    return None

