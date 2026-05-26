"""Rule Engine orchestrator.

URSInput → RuleEngineOutput 의 단일 엔트리포인트.

수행 순서:
  Phase 1 — Room 선택
    select_required_rooms()
  Phase 2 — Rules 1~5 (axis, shape, size, grade, arrangement)
  Phase 3 — Rules 6~7 (airlocks, AL type)
  Phase 4 — Adjacency build
  Phase 5 — Rules 8~10 (corridor, door, equipment)
  Phase 6 — Rules 11~12 (wash/prep, NC)
  Phase 7 — Rule 13 (pressure cascade) + door swing post-fix
  Phase 8 — Hard constraint validation
  Phase 9 — WorkingState → RuleEngineOutput
"""
from __future__ import annotations

from .adjacency_builder import build as build_adjacency
from .kb_loader import rooms_kb
from .rules import (
    rule_01_axis,
    rule_02_shape,
    rule_03_size,
    rule_04_clean_grade,
    rule_05_arrangement,
    rule_06_airlocks,
    rule_07_airlock_type,
    rule_08_corridor,
    rule_09_door,
    rule_10_equipment,
    rule_11_wash_prep,
    rule_12_nc,
    rule_13_pressure,
)
from .schemas import Room, RuleEngineOutput, URSInput
from .validators import validate_hard_constraints
from .working_state import WorkingState


def run_rule_engine(urs: URSInput, strict: bool = True) -> RuleEngineOutput:
    """Top-level pipeline.

    Args:
        urs: 사용자 요구사항.
        strict: True면 hard constraint 위반 시 raise. False면 rationale에 기록만.
    """
    state = WorkingState(urs=urs)

    # Phase 1: Room 선택
    _select_required_rooms(state)

    # Phase 2: 룰 1~5
    rule_01_axis.apply(state)
    rule_02_shape.apply(state)
    rule_03_size.apply(state)
    rule_04_clean_grade.apply(state)
    rule_05_arrangement.apply(state)

    # Phase 3: 룰 6~7
    rule_06_airlocks.apply(state)
    rule_07_airlock_type.apply(state)

    # Phase 4: Adjacency 그래프 생성
    build_adjacency(state)

    # Phase 5: 룰 8~10
    rule_08_corridor.apply(state)
    rule_09_door.apply(state)
    rule_10_equipment.apply(state)

    # Phase 6: 룰 11~12
    rule_11_wash_prep.apply(state)
    rule_12_nc.apply(state)

    # Phase 7: 룰 13 + door swing 보정
    rule_13_pressure.apply(state)
    rule_09_door.post_pressure_swing_fix(state)

    # Phase 8: Hard constraints 검증
    violations = validate_hard_constraints(state)
    if violations and strict:
        msg = "Hard constraint violations:\n" + "\n".join(
            f"  - {v['id']}: {v['message']}" for v in violations
        )
        raise ValueError(msg)

    # Phase 9: 변환
    return _to_output(state)


def _select_required_rooms(state: WorkingState) -> None:
    """KB의 Room 카탈로그에서 URS 정책에 맞는 Room들을 선택."""
    modality = state.urs.product.modality
    kb = rooms_kb(modality)
    rooms_data = kb["rooms"]

    org = state.urs.organization
    overrides = state.urs.overrides
    force_in = set(overrides.force_include_rooms)
    force_ex = set(overrides.force_exclude_rooms)

    # NC Room 활성화 플래그
    nc_flag = {
        "R_LOBBY":         org.include_lobby_onsite,
        "R_OFFICE":        org.include_office_onsite,
        "R_MONITORING":    org.include_monitoring_room_onsite,
        "R_TOILET_FEMALE": org.include_toilet_onsite,
        "R_TOILET_MALE":   org.include_toilet_onsite,
        "R_LOUNGE":        org.include_lounge_onsite,
        "R_VISITOR_CORRIDOR": False,  # 옵션
    }
    # 갱의실 성별 분리
    gender_split = org.gender_separated_gowning
    gender_flag = {
        "R_GOWNING_FEMALE": gender_split,
        "R_GOWNING_MALE":   gender_split,
    }

    for r in rooms_data:
        rid = r["id"]
        if rid in force_ex:
            continue
        # 명시 플래그 가진 Room
        if rid in nc_flag and not nc_flag[rid] and rid not in force_in:
            continue
        if rid in gender_flag and not gender_flag[rid] and rid not in force_in:
            continue

        state.add_room(_make_room(r))


def _make_room(r: dict) -> Room:
    grade = r.get("default_grade", "C")
    return Room(
        id=r["id"],
        name_ko=r["name_ko"],
        name_en=r["name_en"],
        category=r["category"],
        clean_grade=grade,
        area_m2=float(r.get("recommended_area_m2", 30)),
        ceiling_height_mm=int(r.get("recommended_ceiling_h_mm", 3000)),
        is_corridor=bool(r.get("is_corridor", False)),
        corridor_role=r.get("corridor_role"),
        process_step_ids=list(r.get("process_step_ids", [])),
    )


def _to_output(state: WorkingState) -> RuleEngineOutput:
    return RuleEngineOutput(
        project_name=state.urs.project_name,
        modality=state.urs.product.modality,
        rooms=list(state.rooms.values()),
        airlocks=list(state.airlocks.values()),
        adjacency=state.adjacency,
        flow_paths=state.flow_paths,
        zones=state.zones,
        constraints=state.constraints,
        rationale=state.rationale,
    )
