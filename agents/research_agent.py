"""Agente especialista de Búsqueda/Investigación."""
from functools import lru_cache

from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from agents.utils import invoke_agent, user_request
from config import get_llm
from state import OrchestratorState
from tools.research_tools import get_research_tools

RESEARCH_PROMPT = """Eres el AGENTE DE INVESTIGACIÓN de un sistema multi-agente.

Tu ÚNICA responsabilidad es ENCONTRAR información y reportarla fielmente.
- Usa `search_knowledge_base` primero. Si hay búsqueda web disponible, úsala solo si la base interna no alcanza.
- NO analices, NO calcules, NO saques conclusiones: eso lo hace el Agente de Análisis.
- Devuelve los datos COMPLETOS y textuales (números, reseñas, tablas), sin resumir ni omitir elementos,
  porque el analista solo verá lo que tú reportes.
- Cita siempre la fuente como [fuente: id].
- Si no encuentras algo, dilo explícitamente: no inventes datos."""


@lru_cache(maxsize=1)
def get_research_agent():
    return create_react_agent(get_llm(), get_research_tools(), prompt=RESEARCH_PROMPT)


def research_node(state: OrchestratorState) -> dict:
    instruction = state.get("current_instruction") or user_request(state)
    previous = state.get("research_findings")

    prompt = f"INSTRUCCIÓN:\n{instruction}"
    if previous:  # ronda de refinamiento: se le pasa su salida previa, no todo el historial
        prompt += f"\n\nTU RESULTADO ANTERIOR (mejóralo según la instrucción):\n{previous}"

    output = invoke_agent(get_research_agent(), prompt)
    step = state.get("step_count", 0)
    return {
        "research_findings": output,
        "contributions": [
            {"step": step, "agent": "researcher", "instruction": instruction, "output": output}
        ],
        "messages": [AIMessage(content=output, name="researcher")],
    }
