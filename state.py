"""Estado compartido estructurado del orquestador.

Hereda de MessagesState (campo `messages` con reducer add_messages) y agrega
campos que permiten rastrear QUIÉN aportó QUÉ, en qué paso y con qué instrucción.
"""
import operator
from typing import Annotated, Literal, TypedDict

from langgraph.graph import MessagesState

AgentName = Literal["researcher", "analyst"]
NextNode = Literal["researcher", "analyst", "synthesizer"]


class Contribution(TypedDict):
    """Registro auditable de una intervención de un especialista."""

    step: int          # paso del supervisor en el que se delegó
    agent: str         # "researcher" | "analyst"
    instruction: str   # instrucción puntual que recibió
    output: str        # lo que devolvió


class OrchestratorState(MessagesState):
    # --- Control de flujo (lo escribe el Supervisor) ---
    next_agent: str                 # nodo destino de la arista condicional
    current_instruction: str        # instrucción específica para el próximo especialista
    task_completed: bool            # True cuando el sintetizador cerró la tarea
    step_count: int                 # contador de pasos (corta el bucle infinito)

    # --- Trazabilidad: reducers que ACUMULAN en lugar de pisar ---
    contributions: Annotated[list[Contribution], operator.add]
    supervisor_notes: Annotated[list[str], operator.add]  # decisiones + validaciones

    # --- Salidas por dominio (último valor vigente de cada especialista) ---
    research_findings: str
    analysis_results: str

    # --- Resultado final ---
    final_answer: str


def initial_state(user_query: str) -> dict:
    """Estado inicial con todos los campos definidos."""
    return {
        "messages": [("user", user_query)],
        "next_agent": "",
        "current_instruction": "",
        "task_completed": False,
        "step_count": 0,
        "contributions": [],
        "supervisor_notes": [],
        "research_findings": "",
        "analysis_results": "",
        "final_answer": "",
    }
