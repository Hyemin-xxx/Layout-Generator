"""Rule 7 — 전실 타입 선택 (Cascade / Sink / Bubble).

근거: GMP Layout Logic_0510 §6 후반부
- Cascade: 인접 Room 기준 높은 차압 → 전실 → 낮은 차압 (default)
- Sink: 양쪽 Room보다 더 낮은 압력 (Biological safety: 양쪽 Room의 공기를 격리)
- Bubble: 양쪽 Room보다 더 높은 압력 (외부 침입 차단)

판단:
- biological_safety_isolation=True 인 Room에 인접한 AL → sink/bubble로 강제
  · Inoculation, Cell Culture 등 bio-hazard 가능성 → sink (격리)
  · A/B grade barrier → bubble (외부로부터 보호)
- 그 외 → cascade
"""
from __future__ import annotations

from ..kb_loader import flow_policy_kb
from ..working_state import WorkingState

# 어떤 Room에 인접한 AL을 sink/bubble로 보호할지의 기본 정책
SINK_ROOMS = {"R_HARVEST", "R_PURIFICATION_1"}  # 잠재 bio-hazard
BUBBLE_GRADES = {"A", "B"}  # A/B는 외부 침입 방어 우선


def apply(state: WorkingState) -> None:
    fp = flow_policy_kb(state.urs.product.modality)
    bio_iso = state.urs.flow_policy.biological_safety_isolation
    default_type = state.urs.flow_policy.airlock_default_type or fp["airlock_default_type"]

    for al in state.airlocks.values():
        # 가장 강한 룰: A/B 등급 → bubble
        connected_grade = state.rooms[al.connects_higher].clean_grade if al.connects_higher in state.rooms else None

        if connected_grade in BUBBLE_GRADES:
            al.flow_type = "bubble"
            reason = f"인접 Room grade={connected_grade} → bubble (외부 침입 차단)"
        elif bio_iso and al.connects_higher in SINK_ROOMS:
            al.flow_type = "sink"
            reason = f"biological_safety_isolation=True + bio-hazard Room({al.connects_higher}) → sink"
        else:
            al.flow_type = default_type  # type: ignore[assignment]
            reason = f"default flow_type={default_type} (cascade)"

        state.log(
            rule_id="rule_7_al_flow_type",
            target=al.id,
            decision=al.flow_type,
            reason=reason,
            source="GMP Layout Logic_0510 §6",
        )
