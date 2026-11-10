"""Tests offline (no requieren API keys ni LLM)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import MAX_REFINEMENTS, MAX_STEPS  # noqa: E402
from supervisor import apply_guardrails  # noqa: E402
from tools.analysis_tools import analyze_sentiment, calculator, compute_statistics  # noqa: E402
from tools.research_tools import search_knowledge_base  # noqa: E402


def _state(step=0, researcher=0, analyst=0):
    c = [{"step": 1, "agent": "researcher", "instruction": "", "output": ""}] * researcher
    c += [{"step": 2, "agent": "analyst", "instruction": "", "output": ""}] * analyst
    return {"step_count": step, "contributions": c}


def test_calculator():
    assert calculator.invoke({"expression": "(35/10)*100"}) == "350.0"
    assert calculator.invoke({"expression": "__import__('os')"}).startswith("Error")


def test_statistics():
    out = json.loads(compute_statistics.invoke({"numbers": [5, 4, 2, 5, 1, 4, 3, 5, 2, 4]}))
    assert out["mean"] == 3.5 and out["n"] == 10


def test_sentiment():
    out = json.loads(analyze_sentiment.invoke({"texts": ["Excelente producto", "Pésimo servicio", "Sonido correcto"]}))
    assert out["summary"]["positive"] == 1 and out["summary"]["negative"] == 1


def test_kb_search():
    assert "doc-001" in search_knowledge_base.invoke({"query": "reseñas AuraPods"})


def test_guardrail_analyst_needs_research():
    assert apply_guardrails("analyst", _state())[0] == "researcher"


def test_guardrail_no_finish_without_both():
    assert apply_guardrails("synthesizer", _state(researcher=1))[0] == "analyst"


def test_guardrail_max_steps():
    assert apply_guardrails("researcher", _state(step=MAX_STEPS))[0] == "synthesizer"


def test_guardrail_refinement_cap():
    st = _state(researcher=1, analyst=1 + MAX_REFINEMENTS)
    assert apply_guardrails("analyst", st)[0] == "synthesizer"
