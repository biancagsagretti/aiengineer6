"""CLI de demo: muestra paso a paso la delegación Supervisor -> Especialistas -> Síntesis."""
import argparse

from dotenv import load_dotenv

load_dotenv()

from graph import build_graph, save_diagram  # noqa: E402
from state import initial_state  # noqa: E402

DEFAULT_QUERY = (
    "Investiga las reseñas de clientes de los auriculares AuraPods en la base de conocimiento, "
    "analiza el sentimiento de cada reseña y calcula el porcentaje de reseñas positivas "
    "y la calificación promedio."
)


def run(query: str) -> str:
    graph = build_graph()
    final = ""
    for update in graph.stream(initial_state(query), config={"recursion_limit": 40}, stream_mode="updates"):
        for node, delta in update.items():
            print(f"\n{'=' * 70}\n▶ NODO: {node.upper()}")
            if node == "supervisor":
                print(f"  → delega a: {delta['next_agent']}  (paso {delta['step_count']})")
                print(f"  instrucción: {delta['current_instruction']}")
                print(f"  nota: {delta['supervisor_notes'][-1]}")
            elif node in ("researcher", "analyst"):
                print(delta["contributions"][-1]["output"][:1200])
            elif node == "synthesizer":
                final = delta["final_answer"]
    print(f"\n{'=' * 70}\n✅ RESPUESTA FINAL\n{'=' * 70}\n{final}")
    return final


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Orquestador multi-agente (LangGraph)")
    ap.add_argument("query", nargs="?", default=DEFAULT_QUERY)
    ap.add_argument("--diagram", action="store_true", help="solo guarda docs/graph.mmd y .png")
    args = ap.parse_args()
    if args.diagram:
        save_diagram()
    else:
        run(args.query)
