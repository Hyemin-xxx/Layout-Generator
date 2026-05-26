"""Reward Function — 도면 채점.

3계층 점수:
  1. Hard penalty (C1~C10)  — 위반 시 큰 음수. RL이 절대 피해야 함.
  2. Soft penalty (C9 + 룰 ratio + AL completeness)
  3. Geometric quality
       · 동선 분리도 (personnel/material/waste 경로 교차 없음)
       · 차압 cascade 평활도
       · 복도 효율 (직사각형 정렬)
       · 장비 clearance 마진
       · 면적 비율 fit
       · 미적 품질 (대칭/정렬/Room aspect ratio)

return: ScoreReport(total, hard_violations, soft_violations, breakdown)

RL의 step reward로 쓰일 때는 ScoreReport.total을 baseline 대비 delta로 줘도 됨.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from src.drawing_agent.layout_solver import Layout, Rect
from src.rule_engine.schemas import RuleEngineOutput
from src.rule_engine.validators import (
    validate_hard_constraints,
    validate_soft_constraints,
)
from src.rule_engine.working_state import WorkingState


@dataclass
class ScoreReport:
    total: float
    hard_violations: list[dict] = field(default_factory=list)
    soft_violations: list[dict] = field(default_factory=list)
    breakdown: dict[str, float] = field(default_factory=dict)

    @property
    def passed(self) -> bool:
        return not self.hard_violations


# 가중치 (튜닝 가능)
W_HARD = -50.0     # 1건당
W_SOFT = -5.0
W_FLOW_SEPARATION = 8.0
W_PRESSURE_SMOOTH = 6.0
W_CORRIDOR_EFFICIENCY = 4.0
W_EQUIPMENT_MARGIN = 5.0
W_AREA_RATIO_FIT = 3.0
W_AESTHETICS = 4.0


def score(spec: RuleEngineOutput, layout: Optional[Layout] = None) -> ScoreReport:
    """spec(+ optional layout)에 점수를 매김.

    layout이 None이면 spec만으로 평가 가능한 항목만 계산 (Hard/Soft).
    layout이 주어지면 Geometric quality 항목 추가.
    """
    breakdown: dict[str, float] = {}

    # ── Hard constraints ──
    state = _rebuild_working_state(spec)
    hard = validate_hard_constraints(state)
    breakdown["hard_penalty"] = W_HARD * len(hard)

    # ── Soft constraints ──
    soft = validate_soft_constraints(state)
    breakdown["soft_penalty"] = W_SOFT * len(soft)

    # 시작값: 100
    total = 100.0 + breakdown["hard_penalty"] + breakdown["soft_penalty"]

    # ── Geometric quality (layout이 있을 때만) ──
    if layout is not None:
        flow_sep = _flow_separation_quality(spec, layout)
        pres_smooth = _pressure_cascade_smoothness(spec, layout)
        corr_eff = _corridor_efficiency(layout)
        eq_margin = _equipment_margin_quality(layout)
        area_fit = _area_ratio_fit(spec)
        aesthetics = _aesthetic_score(layout)

        breakdown["flow_separation"] = W_FLOW_SEPARATION * flow_sep
        breakdown["pressure_smoothness"] = W_PRESSURE_SMOOTH * pres_smooth
        breakdown["corridor_efficiency"] = W_CORRIDOR_EFFICIENCY * corr_eff
        breakdown["equipment_margin"] = W_EQUIPMENT_MARGIN * eq_margin
        breakdown["area_ratio_fit"] = W_AREA_RATIO_FIT * area_fit
        breakdown["aesthetics"] = W_AESTHETICS * aesthetics

        total += sum(
            [
                breakdown["flow_separation"],
                breakdown["pressure_smoothness"],
                breakdown["corridor_efficiency"],
                breakdown["equipment_margin"],
                breakdown["area_ratio_fit"],
                breakdown["aesthetics"],
            ]
        )

    return ScoreReport(
        total=round(total, 2),
        hard_violations=hard,
        soft_violations=soft,
        breakdown={k: round(v, 2) for k, v in breakdown.items()},
    )


# ──────────────────────────────────────────────────────────────────────
# WorkingState 재구축 — validators는 WorkingState를 입력으로 받음
# ──────────────────────────────────────────────────────────────────────
def _rebuild_working_state(spec: RuleEngineOutput) -> WorkingState:
    from src.rule_engine.schemas import URSInput
    ws = WorkingState(urs=URSInput(project_name=spec.project_name))
    for r in spec.rooms:
        ws.rooms[r.id] = r
    for a in spec.airlocks:
        ws.airlocks[a.id] = a
    ws.adjacency = list(spec.adjacency)
    ws.zones = spec.zones
    ws.flow_paths = spec.flow_paths
    ws.constraints = spec.constraints
    return ws


# ──────────────────────────────────────────────────────────────────────
# Geometric quality — 0~1 점수
# ──────────────────────────────────────────────────────────────────────
def _flow_separation_quality(spec: RuleEngineOutput, layout: Layout) -> float:
    """personnel/material/waste 경로의 공간 분리도. corridor 분리 + AL 분리도로 측정.
    v1: supply↔return 분리 + waste exit이 return 통하는지로 단순 측정.
    """
    score = 0.0
    has_sup = "R_SUPPLY_CORRIDOR" in layout.rooms
    has_ret = "R_RETURN_CORRIDOR" in layout.rooms
    if has_sup and has_ret:
        score += 0.5
    # waste path가 return을 거치는지
    if "R_RETURN_CORRIDOR" in spec.flow_paths.waste_exit:
        score += 0.25
    # personnel exit이 return을 거치는지
    if "R_RETURN_CORRIDOR" in spec.flow_paths.personnel_exit:
        score += 0.25
    return min(score, 1.0)


def _pressure_cascade_smoothness(spec: RuleEngineOutput, layout: Layout) -> float:
    """인접 Room 간 차압 차이의 표준편차 → 작을수록 좋음. 1 - normalized_std."""
    diffs = []
    rooms_by_id = {r.id: r for r in spec.rooms}
    for adj in spec.adjacency:
        a = rooms_by_id.get(adj.from_id)
        b = rooms_by_id.get(adj.to_id)
        if not a or not b:
            continue
        if a.clean_grade != b.clean_grade:
            diffs.append(abs(a.differential_pressure_Pa - b.differential_pressure_Pa))
    if not diffs:
        return 0.8
    mean = sum(diffs) / len(diffs)
    var = sum((d - mean) ** 2 for d in diffs) / len(diffs)
    std = var ** 0.5
    # 표준편차가 5Pa 이하면 1.0, 20Pa 이상이면 0.0
    return max(0.0, min(1.0, 1.0 - (std - 5.0) / 15.0))


def _corridor_efficiency(layout: Layout) -> float:
    """복도의 aspect ratio (직사각형 길쭉함). 가로/세로 비율 ≥ 4 권장."""
    ratios = []
    for pr in layout.rooms.values():
        if not pr.room.is_corridor:
            continue
        long, short = max(pr.rect.w, pr.rect.h), min(pr.rect.w, pr.rect.h)
        if short > 0:
            ratios.append(long / short)
    if not ratios:
        return 0.5
    avg = sum(ratios) / len(ratios)
    # ratio 4 이상이면 1.0, 1.5 이하면 0.0
    return max(0.0, min(1.0, (avg - 1.5) / 2.5))


def _equipment_margin_quality(layout: Layout) -> float:
    """장비 ↔ 장비 최소 간격이 1000mm 이상인 비율."""
    total = 0
    ok = 0
    for pr in layout.rooms.values():
        equips = pr.equipment
        for i, ei in enumerate(equips):
            for ej in equips[i+1:]:
                total += 1
                gap = _rect_gap(ei.rect, ej.rect)
                if gap >= 1000:
                    ok += 1
    return ok / total if total else 0.7


def _area_ratio_fit(spec: RuleEngineOutput) -> float:
    """주공정 비율이 50% 근처에 있을수록 좋음."""
    r = spec.constraints.process_zone_area_ratio
    cur = r.get("current", 0.5)
    # 50% 근처에서 최대치, 40% 또는 70%에서 0
    delta = abs(cur - 0.55)
    return max(0.0, 1.0 - delta / 0.15)


def _aesthetic_score(layout: Layout) -> float:
    """Room aspect ratio가 0.5~2 사이면 좋음 (너무 길쭉하지 않음).
    is_corridor 제외."""
    if not layout.rooms:
        return 0.5
    scores = []
    for pr in layout.rooms.values():
        if pr.room.is_corridor:
            continue
        if pr.rect.w <= 0 or pr.rect.h <= 0:
            continue
        ar = pr.rect.w / pr.rect.h
        # log scale: ar=1이면 1.0, ar=0.25 또는 4면 0
        if ar < 1:
            ar = 1 / ar
        scores.append(max(0.0, 1.0 - (ar - 1.0) / 3.0))
    return sum(scores) / len(scores) if scores else 0.5


def _rect_gap(a: Rect, b: Rect) -> float:
    """두 사각형의 최단 거리 (mm). 겹치면 0."""
    dx = max(0, max(a.x, b.x) - min(a.x2, b.x2))
    dy = max(0, max(a.y, b.y) - min(a.y2, b.y2))
    return (dx ** 2 + dy ** 2) ** 0.5
