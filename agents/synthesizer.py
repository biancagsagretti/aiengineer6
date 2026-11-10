"""Fase de síntesis final: redacta la respuesta al usuario con lo validado."""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from agents.utils import text_of, user_request
from config import get_llm
from state import OrchestratorState

SYNTH_PROMPT = """Eres el SINTETIZADOR final de un sistema multi-agente.
Redacta una respuesta clara y bien estructurada en español para el usuario, usando EXCLUSIVAMENTE
la investigación y el análisis provistos. No agregues datos nuevos ni recalcules números.
Incluye: (1) respuesta directa, (2) datos clave y cifras, (3) fuentes citadas.
Si las notas del supervisor indican limitaciones o que el proceso se cortó por límite de pasos,
menciónalo brevemente al final como "Limitaciones"."""


def synthesizer_node(state: OrchestratorState) -> dict:
    notes = "\n".join(f"- {n}" for n in state.get("supervisor_notes", [])[-4:])
    content = (
        f"PEDIDO ORIGINAL:\n{user_request(state)}\n\n"
        f"INVESTIGACIÓN:\n{state.get('research_findings') or '(vacía)'}\n\n"
        f"ANÁLISIS:\n{state.get('analysis_results') or '(vacío)'}\n\n"
        f"NOTAS DEL SUPERVISOR:\n{notes or '(ninguna)'}"
    )
    result = get_llm().invoke([SystemMessage(content=SYNTH_PROMPT), HumanMessage(content=content)])
    answer = text_of(result.content)
    return {
        "final_answer": answer,
        "task_completed": True,
        "messages": [AIMessage(content=answer, name="synthesizer")],
    }
