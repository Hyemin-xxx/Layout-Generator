"""
Pydantic schemas for Layout-Generator Rule Engine.

URSInput  : 사용자 요구사항 (1단계)
RuleEngineOutput : 7-블록 산출물 (2단계 → 3단계 Drawing Agent 인계)

Source: GMP_Layout_RuleEngine_IO_Spec.md v0.1 + 사용자 정의 7블록 명세
"""
from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Common types
# ============================================================================
Grade = Literal["A", "B", "C", "D", "CNC", "NC"]
Direction = Literal["N", "S", "E", "W"]
Modality = Literal["mAb", "vaccine", "ADC", "cell_therapy"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


# ============================================================================
# 1. INPUT — URS (User Requirements Specification)
# ============================================================================
class ProductSpec(StrictModel):
    """제품/공정 특성. 룰 1, 3, 4의 1차 입력."""
    modality: Modality = "mAb"
    culture_scale_L: int = Field(8000, gt=0, description="배양 규모(L)")
    n_product_types: int = Field(1, ge=1, description="동시 생산 품목 수")
    production_mode: Literal["single_batch", "overlap_batch", "multi_product"] = "single_batch"
    aseptic_filling_onsite: bool = Field(False, description="True면 Grade A/B 필요")
    virus_filtration_required: bool = Field(True, description="One-way flow 종단점")
    closed_system_main_process: bool = Field(False, description="True면 주공정 Grade D 허용")


class BuildingSpec(StrictModel):
    """건축물 제약. 룰 1의 1차 입력."""
    total_floor_area_m2: float = Field(3300, gt=0)
    width_mm: int = Field(78500, gt=0, description="전체 가로(X)")
    depth_mm: int = Field(42500, gt=0, description="전체 세로(Y)")
    floor_level: int = Field(1, ge=1)
    personnel_entry_clock: int = Field(3, ge=1, le=12, description="시계방향 출입구 위치(시)")
    material_inlet_clock: int = Field(12, ge=1, le=12)
    waste_outlet_clock: int = Field(9, ge=1, le=12)
    elevator_position_clock: Optional[int] = Field(None, ge=1, le=12, description="다층일 때 필요")
    support_area_position_preference: Literal["near_material_inlet", "near_personnel_entry", "any"] = "near_material_inlet"


class FlowPolicy(StrictModel):
    """동선/흐름 정책. 룰 6, 7, 8."""
    one_way_flow_required_until: Literal["virus_filtration", "harvest", "none"] = "virus_filtration"
    supply_return_corridor_separate: bool = True
    airlock_default_type: Literal["cascade", "sink", "bubble"] = "cascade"
    biological_safety_isolation: bool = Field(False, description="True면 sink/bubble 강제")


class OrganizationSpec(StrictModel):
    """조직/인적 정책. 룰 12 (NC 포함 여부)."""
    gender_separated_gowning: bool = True
    include_office_onsite: bool = True
    include_toilet_onsite: bool = True
    include_monitoring_room_onsite: bool = True
    include_lobby_onsite: bool = True
    include_lounge_onsite: bool = False


class Overrides(StrictModel):
    """세부 조정. 옵션."""
    force_include_rooms: list[str] = Field(default_factory=list)
    force_exclude_rooms: list[str] = Field(default_factory=list)
    area_overrides_m2: dict[str, float] = Field(default_factory=dict, description="{room_id: area_m2}")
    grade_overrides: dict[str, Grade] = Field(default_factory=dict, description="{room_id: grade}")


class URSInput(StrictModel):
    """전체 URS 입력. Rule Engine의 단일 진입점."""
    project_name: str = "mAb 8000L Conceptual Design"
    product: ProductSpec = Field(default_factory=ProductSpec)
    building: BuildingSpec = Field(default_factory=BuildingSpec)
    flow_policy: FlowPolicy = Field(default_factory=FlowPolicy)
    organization: OrganizationSpec = Field(default_factory=OrganizationSpec)
    overrides: Overrides = Field(default_factory=Overrides)


# ============================================================================
# 2. OUTPUT — 7 Blocks
# ============================================================================

# ---- Block 1: rooms[] ----
class Equipment(StrictModel):
    name: str
    W_mm: int
    D_mm: int
    H_mm: int
    weight_kg: float = 0
    max_op_weight_kg: float = 0
    process_step: Optional[str] = None
    footprint_m2: float = 0  # computed: W*D / 1e6


class Room(StrictModel):
    id: str
    name_ko: str
    name_en: str
    category: Literal["process", "auxiliary", "NC"]
    clean_grade: Grade
    area_m2: float
    ceiling_height_mm: int = 3000
    has_well_ceiling: bool = False
    volume_m3: float = 0
    background_color: str = "#FFFFFF"
    color_pattern: str = "solid"
    transparency_pct: int = 50
    differential_pressure_Pa: float = 0
    air_changes_per_hour: Optional[int] = None
    recovery_time_min: Optional[int] = None
    gowning_type: Optional[str] = None
    gowning_method: Optional[str] = None
    equipment: list[Equipment] = Field(default_factory=list)
    one_way_flow: bool = False
    is_corridor: bool = False
    corridor_role: Optional[Literal["supply", "return", "auxiliary", "visitor"]] = None
    process_step_ids: list[str] = Field(default_factory=list)
    notes: str = ""


# ---- Block 2: airlocks[] ----
AirlockType = Literal[
    "CAL", "CAL_in", "CAL_out",
    "MAL", "MAL_in", "MAL_out",
    "PAL", "PAL_in", "PAL_out",
]
AirlockPurpose = Literal[
    "personnel_entry", "personnel_exit",
    "material_entry", "material_exit",
    "common", "common_in", "common_out",
]


class Airlock(StrictModel):
    id: str
    type: AirlockType
    clean_grade: Grade
    area_m2: float
    flow_type: Literal["cascade", "sink", "bubble"]
    connects_higher: str = Field(description="더 높은 청정등급 Room id")
    connects_lower: str = Field(description="더 낮은 청정등급 Room id")
    purpose: AirlockPurpose
    differential_pressure_Pa: float = 0


# ---- Block 3: adjacency[] ----
class Adjacency(StrictModel):
    from_id: str
    to_id: str
    relationship: Literal["door", "shared_wall", "passthrough_only"]
    door_count: int = 1
    door_size_mm: int = 1000
    door_swing_to: Optional[str] = Field(None, description="차압 흐름 방향 (= 낮은 압력 쪽 Room id)")
    flow_direction: Literal["one_way_in", "one_way_out", "bidirectional"] = "bidirectional"
    notes: str = ""


# ---- Block 4: flow_paths ----
class FlowPaths(StrictModel):
    personnel_entry: list[str] = Field(default_factory=list)
    personnel_exit: list[str] = Field(default_factory=list)
    material_entry: list[str] = Field(default_factory=list)
    waste_exit: list[str] = Field(default_factory=list)
    product_process_order: list[str] = Field(default_factory=list)


# ---- Block 5: zones ----
class Zones(StrictModel):
    process_zone: list[str] = Field(default_factory=list)
    auxiliary_zone: list[str] = Field(default_factory=list)
    nc_zone: list[str] = Field(default_factory=list)


# ---- Block 6: constraints ----
class RangeMM(StrictModel):
    min: Optional[int] = None
    preferred_min: Optional[int] = None
    preferred_max: Optional[int] = None
    max: Optional[int] = None


class Constraints(StrictModel):
    corridor_width_mm: RangeMM
    airlock_size_mm: dict = Field(default_factory=dict)
    ceiling_height_mm: dict = Field(default_factory=dict)
    equipment_clearance_mm: dict = Field(default_factory=dict)
    process_zone_area_ratio: dict = Field(default_factory=dict)
    supply_return_no_direct_connection: bool = True
    wash_prep_no_personnel_crossing: bool = True
    color_legend: dict[str, str] = Field(default_factory=dict)
    pressure_differential_min_pa: float = 10
    pressure_grade_order: list[Grade] = Field(default_factory=lambda: ["A", "B", "C", "D", "CNC", "NC"])


# ---- Block 7: rationale[] ----
class Rationale(StrictModel):
    rule_id: str = Field(description="e.g. rule_4_clean_grade")
    target: str = Field(description="대상 Room id, Airlock id, Adjacency 등")
    decision: str
    reason: str
    source: str = Field(default="GMP Layout Logic_0510", description="근거 문서/시트")


# ---- Top-level output ----
class RuleEngineOutput(StrictModel):
    """7-블록 산출물. Drawing Agent의 단일 입력."""
    project_name: str
    modality: Modality
    rooms: list[Room]
    airlocks: list[Airlock]
    adjacency: list[Adjacency]
    flow_paths: FlowPaths
    zones: Zones
    constraints: Constraints
    rationale: list[Rationale] = Field(default_factory=list)
