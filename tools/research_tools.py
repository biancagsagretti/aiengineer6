"""Herramientas del Agente de Investigación (acotadas a búsqueda)."""
import os
import re
import unicodedata

from langchain_core.tools import tool

from data.knowledge_base import KNOWLEDGE_BASE


def _norm(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return [t for t in re.findall(r"\w+", text) if len(t) > 2]


@tool
def search_knowledge_base(query: str, top_k: int = 3) -> str:
    """Busca en la base de conocimiento interna (Vector DB simulada).
    Devuelve los documentos más relevantes con su id, título y texto completo.
    Úsala primero para datos de productos, reseñas, ventas y competencia."""
    q = set(_norm(query))
    scored = []
    for doc in KNOWLEDGE_BASE:
        words = set(_norm(doc["title"] + " " + doc["text"]))
        score = len(q & words) / (len(q) or 1)
        scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [(s, d) for s, d in scored[:top_k] if s > 0]
    if not hits:
        return "Sin resultados en la base de conocimiento."
    return "\n\n".join(
        f"[fuente: {d['id']}] {d['title']} (relevancia {s:.2f})\n{d['text']}" for s, d in hits
    )


def _build_web_search():
    """Tavily solo si hay API key; si no, el agente trabaja solo con la base simulada."""
    if not os.getenv("TAVILY_API_KEY"):
        return None
    try:
        from langchain_tavily import TavilySearch

        return TavilySearch(max_results=3)
    except ImportError:
        try:
            from langchain_community.tools.tavily_search import TavilySearchResults

            return TavilySearchResults(max_results=3)
        except ImportError:
            return None


def get_research_tools() -> list:
    tools = [search_knowledge_base]
    web = _build_web_search()
    if web is not None:
        tools.append(web)
    return tools
