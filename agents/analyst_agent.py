"""Agente especialista de Análisis/Cómputo."""
from functools import lru_cache

from langchain_core.messages import AIMessage
from langgraph.prebuilt import create_react_agent

from agents.utils import invoke_agent, user_request
from config import get_llm
from state import OrchestratorState
from tools.analysis_tools import get_analysis_tools

ANALYST_PROMPT = """Eres el AGENTE DE ANÁLISIS de un sistema multi-agente.

Tu ÚNICA responsabilidad es PROCESAR los datos que te entregan (sentimiento, cálculos, estadísticas, validación).
- Trabaja SOLO con los datos provistos en "DATOS DISPONIBLES". NUNCA inventes ni asumas datos.
- Todo número que reportes debe provenir de una herramienta (`calculator`, `compute_statistics`,
  `analyze_sentiment`, `validate_schema`). No hagas aritmética "de cabeza".
- Reporta resultados de forma estructurada: qué calculaste, con qué datos y el valor obtenido.
- Si los datos son insuficientes o inconsistentes, comienza tu respuesta con "DATOS_INSUFICIENTES:"
  y explica exactamente qué falta, para que el Supervisor pueda pedir más investigación.
- Si detectas una contradicción entre los datos y la instrucción, repórtala explícitamente."""


@lru_cache(maxsize=1)
def get_analyst_agent():
    return create_react_agent(get_llm(), get_analysis_tools(), prompt=ANALYST_PROMPT)


def analyst_node(state: OrchestratorState) -> dict:
    instruction = state.get("current_instruction") or f"Analiza los datos para responder: {user_request(state)}"
    findings = state.get("research_findings", "") or "(sin datos)"
    previous = state.get("analysis_results")

    # Contexto mínimo necesario: instrucción + datos del investigador (no el historial completo)
    prompt = f"INSTRUCCIÓN:\n{instruction}\n\nDATOS DISPONIBLES (del Agente de Investigación):\n{findings}"
    if previous:
        prompt += f"\n\nTU ANÁLISIS ANTERIOR (corrígelo según la instrucción):\n{previous}"

    output = invoke_agent(get_analyst_agent(), prompt)
    step = state.get("step_count", 0)
    return {
        "analysis_results": output,
        "contributions": [
            {"step": step, "agent": "analyst", "instruction": instruction, "output": output}
        ],
        "messages": [AIMessage(content=output, name="analyst")],
    }
