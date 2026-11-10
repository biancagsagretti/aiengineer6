"""Parámetros globales del orquestador."""
import os
from functools import lru_cache

# Condición de parada dura contra el "Supervisor Infinito":
# cuántas decisiones del supervisor se permiten como máximo.
MAX_STEPS = int(os.getenv("MAX_STEPS", "8"))

# Cuántas veces se puede RE-invocar a un especialista (además de su 1ª intervención).
MAX_REFINEMENTS = int(os.getenv("MAX_REFINEMENTS", "1"))


@lru_cache(maxsize=1)
def get_llm():
    """LLM compartido (lazy). Proveedores: openai | anthropic | gemini (vía LLM_PROVIDER)."""
    from dotenv import load_dotenv

    load_dotenv()
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    if provider in ("gemini", "google"):
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(model=os.getenv("LLM_MODEL", "gemini-3.6-flash-lite"), temperature=0)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(model=os.getenv("LLM_MODEL", "claude-sonnet-4-5"), temperature=0)

    from langchain_openai import ChatOpenAI

    return ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o-mini"), temperature=0)
