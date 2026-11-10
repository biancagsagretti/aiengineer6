"""Utilidades compartidas por los nodos de agentes."""
from langchain_core.messages import HumanMessage


def text_of(content) -> str:
    """Normaliza el contenido de un mensaje (str o lista de bloques) a texto."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            b.get("text", "") if isinstance(b, dict) else str(b) for b in content
        )
    return str(content)


def user_request(state) -> str:
    """Pedido original del usuario (primer mensaje humano)."""
    for m in state["messages"]:
        if getattr(m, "type", None) == "human":
            return text_of(m.content)
    return ""


def invoke_agent(agent, prompt: str) -> str:
    """Invoca un agente ReAct con un contexto AISLADO: solo recibe `prompt`,
    no el historial completo del grafo (evita contaminación de contexto)."""
    result = agent.invoke(
        {"messages": [HumanMessage(content=prompt)]},
        config={"recursion_limit": 12},
    )
    return text_of(result["messages"][-1].content)
