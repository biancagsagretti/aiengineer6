"""Nodo Supervisor: router inteligente + validador (rúbrica) + control de flujo."""
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from agents.utils import user_request
from config import MAX_REFINEMENTS, MAX_STEPS, get_llm
from state import NextNode, OrchestratorState

SUPERVISOR_PROMPT = f"""Eres el SUPERVISOR de un sistema multi-agente de análisis e investigación.
NO investigas ni calculas: delegas, VALIDAS y decides cuándo terminar.

EQUIPO (los valores de `next` deben ser exactamente estos):
- researcher : busca y reporta datos crudos (base interna / web). No analiza.
- analyst    : procesa datos (sentimiento, cálculos, estadísticas, validación). Solo usa los datos del investigador.
- synthesizer: redacta la respuesta final. Elígelo SOLO cuando la rúbrica se cumpla completa.

FLUJO NORMAL: researcher -> analyst -> synthesizer. Dada la conversación actual, decide quién debe
intervenir ahora o si es momento de finalizar.

RÚBRICA DE VALIDACIÓN (debe cumplirse TODO antes de elegir `synthesizer`):
1. COBERTURA: cada parte del pedido del usuario tiene un resultado concreto.
2. EVIDENCIA: la investigación contiene datos concretos con fuente [fuente: id], no generalidades.
3. CÁLCULO: toda cifra del análisis proviene de datos reales del investigador y de herramientas.
4. CONSISTENCIA: no hay contradicciones entre investigación y análisis (ej. el analista usa 10 reseñas
   y el investigador reportó 8; porcentajes que no suman 100).
5. SUFICIENCIA: la respuesta final se podría redactar sin información adicional.

RESOLUCIÓN DE CONFLICTOS ENTRE AGENTES:
- Para DATOS (qué dicen las fuentes) manda el researcher; para CÁLCULOS e interpretación manda el analyst.
- Si el analyst empieza con "DATOS_INSUFICIENTES:", reenvía al researcher indicando exactamente qué falta.
- Si una cifra no es consistente con los datos, reenvía al analyst citando la inconsistencia concreta.

REGLAS:
- `instruction` debe ser específica y accionable para el agente elegido (o una nota breve si es synthesizer).
  Si estás pidiendo un refinamiento, incluye el feedback concreto (qué falló y qué corregir).
- Nunca repitas una instrucción idéntica a una anterior.
- Límites duros: máximo {MAX_STEPS} pasos y {MAX_REFINEMENTS} refinamiento(s) por especialista.
  Si el sistema te corta, redactarás con lo disponible. Sé estricto pero no perfeccionista."""


class SupervisorDecision(BaseModel):
    reasoning: str = Field(description="Razonamiento breve de la decisión de ruteo.")
    rubric_check: str = Field(
        description="Evaluación de la rúbrica (1-5) sobre lo producido hasta ahora; 'N/A' si aún no hay resultados."
    )
    next: Literal["researcher", "analyst", "synthesizer"] = Field(description="Siguiente nodo.")
    instruction: str = Field(description="Instrucción específica para el siguiente agente.")


# ----------------------------------------------------------------------------
# Guardarraíles deterministas (no dependen del LLM): evitan el "Supervisor Infinito"
# ----------------------------------------------------------------------------
def _default_instruction(agent: str, request: str) -> str:
    if agent == "researcher":
        return f"Busca y reporta todos los datos necesarios para responder: {request}"
    if agent == "analyst":
        return f"Analiza los datos obtenidos para responder: {request}"
    return "Redacta la respuesta final."


def apply_guardrails(proposed: str, state: OrchestratorState) -> tuple[str, str | None]:
    """Devuelve (nodo_final, motivo_del_override | None)."""
    steps = state.get("step_count", 0)
    contribs = state.get("contributions", [])
    done = {a: sum(1 for c in contribs if c["agent"] == a) for a in ("researcher", "analyst")}

    if steps >= MAX_STEPS:
        return "synthesizer", f"Límite de {MAX_STEPS} pasos alcanzado: se cierra con lo disponible."

    # El analista no puede trabajar sin datos
    if proposed == "analyst" and done["researcher"] == 0:
        return "researcher", "El analista necesita datos: se investiga primero."

    # Tope de refinamientos por especialista
    if proposed in done and done[proposed] >= 1 + MAX_REFINEMENTS:
        if proposed == "researcher" and done["analyst"] == 0:
            return "analyst", f"researcher alcanzó el tope de refinamientos: se avanza al análisis."
        return "synthesizer", f"{proposed} alcanzó el tope de refinamientos: se sintetiza con lo disponible."

    # No se puede finalizar sin que hayan intervenido ambos dominios
    if proposed == "synthesizer":
        if done["researcher"] == 0:
            return "researcher", "No se puede finalizar sin investigación."
        if done["analyst"] == 0:
            return "analyst", "No se puede finalizar sin análisis."

    return proposed, None


def _render_status(state: OrchestratorState) -> str:
    contribs = state.get("contributions", [])
    if contribs:
        lines = [
            f"[paso {c['step']}] {c['agent']} | instrucción: {c['instruction'][:200]}\n"
            f"  salida:\n{c['output'][:2500]}"
            for c in contribs
        ]
        body = "\n\n".join(lines)
    else:
        body = "(ningún especialista ha intervenido todavía)"
    notes = "\n".join(f"- {n}" for n in state.get("supervisor_notes", [])[-4:]) or "(sin notas)"
    return (
        f"PEDIDO DEL USUARIO:\n{user_request(state)}\n\n"
        f"PASO ACTUAL: {state.get('step_count', 0) + 1}/{MAX_STEPS}\n\n"
        f"CONTRIBUCIONES HASTA AHORA:\n{body}\n\n"
        f"TUS NOTAS PREVIAS:\n{notes}"
    )


def supervisor_node(state: OrchestratorState) -> dict:
    step = state.get("step_count", 0)
    request = user_request(state)

    decision: SupervisorDecision = get_llm().with_structured_output(SupervisorDecision).invoke(
        [SystemMessage(content=SUPERVISOR_PROMPT), HumanMessage(content=_render_status(state))]
    )

    target, override = apply_guardrails(decision.next, state)
    instruction = decision.instruction if target == decision.next else _default_instruction(target, request)

    note = f"paso {step + 1}: {decision.next} -> {target} | {decision.reasoning} | rúbrica: {decision.rubric_check}"
    if override:
        note += f" | OVERRIDE: {override}"

    return {
        "next_agent": target,
        "current_instruction": instruction,
        "step_count": step + 1,
        "supervisor_notes": [note],
    }


def route_from_supervisor(state: OrchestratorState) -> NextNode:
    """Función de ruteo de la arista condicional (retorno tipado con Literal)."""
    return state["next_agent"]  # type: ignore[return-value]
