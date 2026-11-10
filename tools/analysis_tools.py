"""Herramientas del Agente de Análisis (cómputo determinista, sin red)."""
import ast
import json
import operator
import re
import statistics
import unicodedata

from langchain_core.tools import tool

# ---------- Calculadora segura ----------
_OPS = {
    ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
    ast.Div: operator.truediv, ast.Pow: operator.pow, ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv, ast.USub: operator.neg, ast.UAdd: operator.pos,
}


def _eval(node):
    if isinstance(node, ast.Expression):
        return _eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.left), _eval(node.right))
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_eval(node.operand))
    raise ValueError("Expresión no permitida")


@tool
def calculator(expression: str) -> str:
    """Evalúa una expresión aritmética (+ - * / ** % //, paréntesis). Ej: '(35/10)*100'."""
    try:
        return str(_eval(ast.parse(expression, mode="eval")))
    except Exception as e:  # noqa: BLE001
        return f"Error: {e}"


@tool
def compute_statistics(numbers: list[float]) -> str:
    """Estadísticas descriptivas de una lista de números: n, suma, media, mediana, mín, máx, desvío."""
    if not numbers:
        return json.dumps({"error": "lista vacía"})
    return json.dumps({
        "n": len(numbers),
        "sum": round(sum(numbers), 4),
        "mean": round(statistics.mean(numbers), 4),
        "median": round(statistics.median(numbers), 4),
        "min": min(numbers),
        "max": max(numbers),
        "stdev_pop": round(statistics.pstdev(numbers), 4),
    })


# ---------- Sentimiento (léxico en español) ----------
_POS = {"excelente", "buen", "buena", "bueno", "buenisimo", "recomendable", "recomiendo", "increible",
        "comodos", "comodo", "livianos", "encantan", "encanta", "mejor", "genial", "perfecto", "perfectos",
        "fantastico", "rapido", "util", "satisfecho", "feliz"}
_NEG = {"mala", "malo", "malos", "pesimo", "pesima", "decepcionante", "defectuosos", "defectuoso",
        "incomodos", "incomodo", "horrible", "lento", "roto", "terrible", "caro", "falla", "fallas"}
_NEGATORS = {"no", "nunca", "ni", "tampoco"}


def _tokens(text: str) -> list[str]:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.findall(r"\w+", text)


@tool
def analyze_sentiment(texts: list[str]) -> str:
    """Análisis de sentimiento (positivo/negativo/neutral) de una lista de textos en español.
    Devuelve el detalle por texto y un resumen con conteos y porcentajes."""
    results, counts = [], {"positive": 0, "negative": 0, "neutral": 0}
    for t in texts:
        toks = _tokens(t)
        score = 0
        for i, tok in enumerate(toks):
            val = 1 if tok in _POS else -1 if tok in _NEG else 0
            if val and i > 0 and toks[i - 1] in _NEGATORS:
                val = -val
            score += val
        label = "positive" if score > 0 else "negative" if score < 0 else "neutral"
        counts[label] += 1
        results.append({"text": t[:70], "score": score, "label": label})
    total = len(texts) or 1
    summary = {**counts, "total": len(texts),
               **{f"{k}_pct": round(100 * v / total, 1) for k, v in counts.items()}}
    return json.dumps({"results": results, "summary": summary}, ensure_ascii=False)


@tool
def validate_schema(json_string: str, required_fields: list[str]) -> str:
    """Valida que un JSON sea un objeto y contenga todos los campos requeridos."""
    try:
        obj = json.loads(json_string)
    except json.JSONDecodeError as e:
        return f"INVÁLIDO: JSON mal formado ({e})"
    if not isinstance(obj, dict):
        return "INVÁLIDO: se esperaba un objeto JSON"
    missing = [f for f in required_fields if f not in obj]
    return "VÁLIDO" if not missing else f"INVÁLIDO: faltan campos {missing}"


def get_analysis_tools() -> list:
    return [calculator, compute_statistics, analyze_sentiment, validate_schema]
