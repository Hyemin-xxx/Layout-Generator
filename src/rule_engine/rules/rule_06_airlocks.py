"""Rule 6 — 전실(Air Lock) 배열.

근거: GMP Layout Logic_0510 §6 (전실의 배열)
- AL은 청정등급이 바뀌거나 공정 중요도 구분이 필요한 두 Room 사이에 위치
- One-way Room: 입구/출구 별도 → 입구 AL + 출구 AL 각각 배치
- AL 종류: PAL (Personnel), MAL (Material), CAL (Common, PAL+MAL 통합)
- Grade B + one-way → 4개 (PAL-in, MAL-in, PAL-out, MAL-out)
- Grade C + one-way → 공간 넉넉하면 4개, 부족하면 2개 (AL-in + AL-out)
- 양방향 Room → 1개 (AL)
- 양 Room 등급 같고 중요도 구분 불필요 → AL 생략

산출: state.airlocks[al_id] = Airlock(...)
이 단계에서 in/out, type만 정함. cascade/sink/bubble은 룰 7에서.
"""
from __future__ import annotations

from ..kb_loader import flow_policy_kb, rooms_kb
from ..schemas import Airlock
from ..working_state import WorkingState

# 면적 (룰 5.4 기준)
PAL_AREA = 12.0
MAL_AREA = 16.0
CAL_AREA = 16.0


def apply(state: WorkingState) -> None:
    modality = state.urs.product.modality
    rooms_kb_data = rooms_kb(modality)["rooms"]
    rooms_by_id = {r["id"]: r for r in rooms_kb_data}
    fp = flow_policy_kb(modality)

    # 공간 여유 판단: 주공정 비율로 추정
    # current 비율 > 0.55 면 공간 여유 부족 → C grade는 CAL 2개로 간소화
    ratio_now = state.constraints.process_zone_area_ratio.get("current", 0.5)
    space_tight = ratio_now > 0.55

    supply = "R_SUPPLY_CORRIDOR" if state.has_room("R_SUPPLY_CORRIDOR") else None
    ret = "R_RETURN_CORRIDOR" if state.has_room("R_RETURN_CORRIDOR") else None

    al_counter = 0

    def new_id() -> str:
        nonlocal al_counter
        al_counter += 1
        return f"AL_{al_counter:03d}"

    for rid, room in state.rooms.items():
        kb_room = rooms_by_id.get(rid)
        if not kb_room or not kb_room.get("needs_airlock"):
            continue

        in_one_way = kb_room.get("in_one_way_chain", False)
        grade = room.clean_grade

        # ---- Grade B + one_way → 4개 풀세트 ----
        if grade == "B" and in_one_way:
            _add(state, new_id(), "PAL_in",  room, supply, ret, "personnel_entry",  PAL_AREA, grade)
            _add(state, new_id(), "MAL_in",  room, supply, ret, "material_entry",   MAL_AREA, grade)
            _add(state, new_id(), "PAL_out", room, supply, ret, "personnel_exit",   PAL_AREA, grade)
            _add(state, new_id(), "MAL_out", room, supply, ret, "material_exit",    MAL_AREA, grade)
            room.one_way_flow = True
            state.log(
                rule_id="rule_6_airlocks",
                target=rid,
                decision="AL 4개 (PAL_in/MAL_in/PAL_out/MAL_out)",
                reason="Grade B + one-way → 풀세트 강제 (EU GMP Annex 1)",
            )
            continue

        # ---- Grade C + one_way ----
        if grade == "C" and in_one_way:
            if space_tight:
                # 공간 부족 → CAL_in + CAL_out
                _add(state, new_id(), "CAL_in",  room, supply, ret, "common_in",  CAL_AREA, grade)
                _add(state, new_id(), "CAL_out", room, supply, ret, "common_out", CAL_AREA, grade)
                room.one_way_flow = True
                state.log(
                    rule_id="rule_6_airlocks",
                    target=rid,
                    decision="AL 2개 (CAL_in/CAL_out, PAL+MAL 통합)",
                    reason=f"Grade C + one-way + 공간 부족 (process ratio={ratio_now:.0%}) → CAL 통합형",
                )
            else:
                # 공간 여유 → 4개
                _add(state, new_id(), "PAL_in",  room, supply, ret, "personnel_entry",  PAL_AREA, grade)
                _add(state, new_id(), "MAL_in",  room, supply, ret, "material_entry",   MAL_AREA, grade)
                _add(state, new_id(), "PAL_out", room, supply, ret, "personnel_exit",   PAL_AREA, grade)
                _add(state, new_id(), "MAL_out", room, supply, ret, "material_exit",    MAL_AREA, grade)
                room.one_way_flow = True
                state.log(
                    rule_id="rule_6_airlocks",
                    target=rid,
                    decision="AL 4개 (PAL_in/MAL_in/PAL_out/MAL_out)",
                    reason=f"Grade C + one-way + 공간 여유 (process ratio={ratio_now:.0%}) → 풀세트",
                )
            continue

        # ---- 양방향 / 그 외 ----
        if grade in ("C", "D") and kb_room.get("flow") == "both_way":
            # AL 1개로 충분
            _add(state, new_id(), "CAL", room, supply, supply, "common", CAL_AREA, grade)
            state.log(
                rule_id="rule_6_airlocks",
                target=rid,
                decision="AL 1개 (CAL)",
                reason=f"Grade {grade} + both-way → 단일 AL",
            )


def _add(
    state: WorkingState,
    al_id: str,
    al_type: str,
    room,
    higher_room_id: str | None,
    lower_room_id: str | None,
    purpose: str,
    area: float,
    inherited_grade: str,
) -> None:
    """AL grade는 인접 Room 둘 중 더 낮은 등급. 여기선 일단 room.grade로 두고 룰 7에서 정밀화."""
    # in 쪽은 supply corridor(high), out 쪽은 return corridor(low)와 연결
    al = Airlock(
        id=al_id,
        type=al_type,  # type: ignore[arg-type]
        clean_grade=inherited_grade,  # type: ignore[arg-type]
        area_m2=area,
        flow_type="cascade",  # 룰 7에서 정정
        connects_higher=room.id,
        connects_lower=(higher_room_id if "in" in al_type else (lower_room_id or higher_room_id or "")),
        purpose=purpose,  # type: ignore[arg-type]
        differential_pressure_Pa=0,
    )
    state.add_airlock(al)
