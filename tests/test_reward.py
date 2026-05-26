"""Reward function smoke + behavioral tests."""
from __future__ import annotations

from src.drawing_agent.floorplan import generate_floorplan
from src.reward.scorer import ScoreReport, score
from src.rule_engine.engine import run_rule_engine
from src.rule_engine.schemas import URSInput


def test_baseline_passes_hard():
    spec = run_rule_engine(URSInput(), strict=True)
    _, layout = generate_floorplan(spec)
    r = score(spec, layout)
    assert r.passed
    assert r.total > 100  # baseline 도면이 100점 이상이어야 의미 있음


def test_score_breakdown_keys():
    spec = run_rule_engine(URSInput(), strict=True)
    _, layout = generate_floorplan(spec)
    r = score(spec, layout)
    for k in [
        "hard_penalty",
        "soft_penalty",
        "flow_separation",
        "pressure_smoothness",
        "corridor_efficiency",
        "equipment_margin",
        "area_ratio_fit",
        "aesthetics",
    ]:
        assert k in r.breakdown


def test_score_without_layout():
    """layout=None 일 때도 Hard/Soft만 평가하고 정상 동작."""
    spec = run_rule_engine(URSInput(), strict=True)
    r = score(spec, layout=None)
    # geometric quality 없음, 100 - penalty만
    assert isinstance(r, ScoreReport)
    assert "flow_separation" not in r.breakdown
    assert r.passed


def test_hard_violation_drops_score():
    """Hard constraint 위반이 있으면 점수가 baseline보다 -50 이상 낮음."""
    spec = run_rule_engine(URSInput(), strict=True)
    baseline = score(spec).total
    # 강제 위반 주입
    from src.rule_engine.schemas import Adjacency
    spec.adjacency.append(
        Adjacency(
            from_id="R_SUPPLY_CORRIDOR",
            to_id="R_RETURN_CORRIDOR",
            relationship="door",
        )
    )
    bad = score(spec).total
    assert bad < baseline - 40
