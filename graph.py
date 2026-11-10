"""Construcción del grafo jerárquico: Supervisor -> {researcher, analyst, synthesizer}."""
from langgraph.graph import END, START, StateGraph

try:  # langgraph recientes
    from langgraph.types import RetryPolicy
except ImportError:  # versiones anteriores
    from langgraph.pregel import RetryPolicy

from agents import analyst_node, research_node, synthesizer_node
from state import OrchestratorState
from supervisor import route_from_supervisor, supervisor_node


_TRANSIENT_MARKERS = ("503", "unavailable", "429", "resource_exhausted", "overloaded",
                      "high demand", "timeout", "timed out", "rate limit", "connection")


def is_transient(exc: Exception) -> bool:
    """Reintenta solo errores temporales del proveedor (503/429/timeouts), no errores de código o config."""
    msg = f"{type(exc).__name__}: {exc}".lower()
    # Cuota DIARIA agotada: esperar segundos no ayuda, se falla de inmediato
    if "perday" in msg or "per day" in msg:
        return False
    return any(m in msg for m in _TRANSIENT_MARKERS)


# Backoff exponencial: ~3s, 6s, 12s, 24s entre intentos (máx. 5 intentos por nodo)
RETRY = RetryPolicy(max_attempts=5, initial_interval=3.0, backoff_factor=2.0, max_interval=30.0,
                    retry_on=is_transient)


def build_graph():
    builder = StateGraph(OrchestratorState)

    builder.add_node("supervisor", supervisor_node, retry_policy=RETRY)
    builder.add_node("researcher", research_node, retry_policy=RETRY)
    builder.add_node("analyst", analyst_node, retry_policy=RETRY)
    builder.add_node("synthesizer", synthesizer_node, retry_policy=RETRY)

    builder.add_edge(START, "supervisor")

    # Aristas condicionales: el supervisor decide dinámicamente a quién delegar
    builder.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {"researcher": "researcher", "analyst": "analyst", "synthesizer": "synthesizer"},
    )

    # Los especialistas SIEMPRE devuelven el control al supervisor (topología jerárquica)
    builder.add_edge("researcher", "supervisor")
    builder.add_edge("analyst", "supervisor")
    builder.add_edge("synthesizer", END)

    return builder.compile()


def save_diagram(path_prefix: str = "docs/graph") -> None:
    """Guarda el diagrama Mermaid (.mmd, offline) y el PNG (requiere internet: mermaid.ink)."""
    g = build_graph().get_graph()
    with open(f"{path_prefix}.mmd", "w", encoding="utf-8") as f:
        f.write(g.draw_mermaid())
    try:
        with open(f"{path_prefix}.png", "wb") as f:
            f.write(g.draw_mermaid_png())
    except Exception as e:  # noqa: BLE001
        print(f"(PNG no generado: {e}). El .mmd sí se guardó.")


graph = build_graph()
