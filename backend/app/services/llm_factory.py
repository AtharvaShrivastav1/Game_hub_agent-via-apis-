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

def get_llm(temperature: Optional[float] = None) -> Any:

    """
    Returns an isolated LangChain ChatModel instance configured via environment variables.
    Supports Google Gemini (default) and OpenAI, with intelligent error recovery.
    """
    temp = temperature if temperature is not None else settings.GEMINI_TEMPERATURE

    if settings.LLM_PROVIDER == "openai" or (not settings.GEMINI_API_KEY and settings.OPENAI_API_KEY):
        try:
            from langchain_openai import ChatOpenAI
            logger.info(f"Using OpenAI model: {settings.OPENAI_MODEL}")
            return ChatOpenAI(
                model=settings.OPENAI_MODEL,
                temperature=temp,
                api_key=settings.OPENAI_API_KEY,
            )
        except Exception as e:
            logger.error(f"Failed to initialize ChatOpenAI: {e}")

    # Default to Gemini with automatic model fallback chain
    if settings.GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            
            # Parse models list from settings (e.g. gemini-3.5-flash, gemini-3.7-flash, gemini-3.5-flash-lite, gemini-3.6-flash)
            model_list = [m.strip() for m in settings.GEMINI_MODELS.split(",") if m.strip()]
            if settings.GEMINI_MODEL and settings.GEMINI_MODEL not in model_list:
                model_list.insert(0, settings.GEMINI_MODEL)
            if not model_list:
                model_list = ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]

            primary_model = model_list[0]
            logger.info(f"Initializing Gemini LLM with primary: {primary_model} and fallbacks: {model_list[1:]}")

            primary_llm = ChatGoogleGenerativeAI(
                model=primary_model,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=temp,
                request_timeout=15.0,
            )

            fallback_llms = [
                ChatGoogleGenerativeAI(
                    model=m,
                    google_api_key=settings.GEMINI_API_KEY,
                    temperature=temp,
                    request_timeout=15.0,
                )
                for m in model_list[1:]
            ]

            if fallback_llms:
                return primary_llm.with_fallbacks(fallback_llms)
            return primary_llm
        except Exception as e:
            logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}")


    logger.warning("No valid LLM configuration found. Agent will utilize rule-based fallbacks where needed.")
    return None
