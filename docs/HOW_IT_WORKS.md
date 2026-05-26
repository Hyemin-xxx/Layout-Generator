# 엔진은 어떻게 도면을 만드는가

> Layout-Generator의 내부 작동 원리를 처음 보는 사람도 이해할 수 있게 풀어쓴 문서.
> 13개 룰이 빈 URS에서 어떻게 완성된 7-블록 spec과 도면까지 도달하는지 추적합니다.

---

## ⏱ 5분 요약

이 시스템은 **레시피(URS) → 조리 순서서(7-블록 JSON) → 음식(도면)** 으로 가는 자동 주방입니다.

```
   "mAb 8000L 만들고 싶어요"           스마트폰 주문 같은 거
              │
              ▼
   ┌─────────────────────────┐
   │  Rule Engine            │       자동 조리 매뉴얼 생성
   │  (13 룰 + KB)            │       "어떤 방을 / 어디에 / 어떤 등급으로"
   └─────────────────────────┘
              │
              ▼ 7-block JSON
              │
   ┌─────────────────────────┐
   │  Drawing Agent          │       실제 도면 그리기
   │  (DESIGN.md 토큰 적용)   │       BIG/SOM 컨셉 다이어그램 풍
   └─────────────────────────┘
              │
              ▼
   📄 floorplan.svg
```

**핵심 아이디어:**
1. **룰과 데이터를 분리합니다.** 13개 룰은 Python 코드, GMP 규정·장비·면적 데이터는 JSON.
2. **모든 결정은 근거가 남습니다.** 각 룰이 무엇을 왜 결정했는지 `rationale[]`에 자동 기록.
3. **위반은 자동으로 잡힙니다.** Hard Constraint(C1~C10) 검증기가 안전 룰을 보장.

---

## 1. 비유로 이해하기

### 1.1 식당 비유

레스토랑이 새 메뉴를 출시한다고 상상해보세요.

| 식당 | Layout-Generator |
|------|------------------|
| 손님 주문서 (스테이크, 미디엄, 와인 페어링) | URS (mAb, 8000L, 다층) |
| 셰프의 머리 속 룰 ("스테이크는 굽기 전 30분 상온") | 13개 GMP 룰 |
| 재료 목록 (소고기, 소금, 후추, 와인) | Knowledge Base (Room/장비/등급 데이터) |
| 조리 매뉴얼 (3분 굽고 뒤집고...) | 7-블록 JSON |
| 셰프의 위생 검사 | Hard Constraint Validator |
| 완성된 요리 | SVG 도면 |
| 음식 평가 점수 | Reward Function |

### 1.2 공장 조립 라인 비유

엔진은 **9개 작업대(Phase)**가 순서대로 작업하는 컨베이어 벨트입니다.

```
[Phase 1]  Room 부품들 선택  ──→  텅 빈 카트에 30개 Room 들어옴
[Phase 2]  방위/축 설정     ──→  "12시 방향이 자재 입구"
[Phase 3]  Room 모양 제약   ──→  "직사각형만 허용"
[Phase 4]  Room 크기 계산   ──→  장비 부피 기반으로 면적 산출
[Phase 5]  청정등급 부여    ──→  A/B/C/D/CNC/NC 도장 찍기
[Phase 6]  Room 그룹핑     ──→  공정/보조/NC 구역 분리
[Phase 7]  전실(Airlock) 결정 ──→  17개 AL 추가
[Phase 8]  전실 타입 선정   ──→  cascade/sink/bubble
[Phase 9]  연결 그래프 + 도어 ──→  41개 인접 관계
[Phase 10] 차압 cascade     ──→  Pa 단위 압력 부여
[Phase 11] 안전 검증       ──→  C1~C10 모두 통과 확인
[Phase 12] 7-블록 JSON 출력 ──→  Drawing Agent에게 인계
```

---

## 2. 한 Room을 따라가 보자 — Seed 접종실의 여정

**Inoculation Room (Seed 접종실)** 하나가 엔진을 통과하면서 어떻게 풍부해지는지 추적합니다.

### Phase 0: 빈 슬레이트

```python
# WorkingState 초기 상태
state.rooms = {}  # 텅 빔
state.airlocks = {}
state.adjacency = []
state.rationale = []
```

### Phase 1: Room 선택 (`_select_required_rooms`)

엔진이 `kb/rooms_mab.json`을 열어 30개 Room 카탈로그를 봅니다. URS에 따라 필요한 Room만 골라냅니다.

```json
// rooms_mab.json 발췌
{
  "id": "R_INOCULATION",
  "name_ko": "Seed 접종실",
  "name_en": "Inoculation",
  "category": "process",
  "grade_options": ["B", "C"],
  "default_grade": "C",
  "recommended_area_m2": 40,
  "needs_airlock": true,
  "in_one_way_chain": true,
  "process_step_ids": ["P3-1", "P3-2"],
  "equipment_room_key": "Inoculation"
}
```

엔진은 이걸 미리 만들어진 `Room` 객체로 변환:

```python
state.rooms["R_INOCULATION"] = Room(
    id="R_INOCULATION",
    name_ko="Seed 접종실",
    name_en="Inoculation",
    category="process",
    clean_grade="C",          # default_grade
    area_m2=40,               # recommended
    ceiling_height_mm=3000,   # default
    # 나머지는 아직 비어있음 — 다음 룰들이 채울 것
    differential_pressure_Pa=0,
    air_changes_per_hour=None,
    gowning_type=None,
    equipment=[],
    one_way_flow=False,
    background_color="#FFFFFF",
)
```

> **포인트**: 이 시점에서는 *템플릿*만 있습니다. 룰들이 차례로 와서 채워줍니다.

### Phase 2-5: Rule 1~5 적용

#### Rule 1 (axis) — Inoculation은 직접 안 건드림
건물 차원 결정이라 Room별 적용 X. 하지만 `state.axis`에 다음 정보 기록:
```python
state.axis = {
    "material_inlet_clock": 12,      # 자재 입구 12시
    "process_start_side": "near_material_inlet",
    "process_end_side": "near_waste_outlet",
}
```
→ Inoculation은 process 순서상 3번째라, **상부 어딘가에 배치**될 운명.

#### Rule 2 (shape) — 직사각형 제약
모든 Room이 직사각형(또는 합)이어야 한다는 제약을 `constraints`에 등록.
→ Inoculation도 직사각형으로만 그려집니다.

#### Rule 3 (size) — 면적 정밀화 ⭐
이 룰이 진짜 일을 합니다. `kb/equipment.json`에서 Inoculation 장비를 찾습니다:

```json
"Inoculation": [
  { "name": "Isolator",    "W": 4000, "D": 2000, "H": 3000, ... },
  { "name": "Centrifuge",  "W": 1000, "D": 600,  "H": 500,  ... },
  { "name": "Incubator",   "W": 1200, "D": 800,  "H": 600,  ... },
  { "name": "Cleanbench",  "W": 2000, "D": 800,  "H": 2000, ... }
]
```

엔진은 장비 4대를 Room에 부착하고, 면적 최소값을 계산:

```python
# 각 장비를 (W+1000)×(D+1000) 사각형으로 보고 합산 → ×1.30 통행 마진
Isolator:   (4000+1000) × (2000+1000) = 15 m²
Centrifuge: (1000+1000) × (600+1000)  = 3.2 m²
Incubator:  (1200+1000) × (800+1000)  = 4 m²
Cleanbench: (2000+1000) × (800+1000)  = 5.4 m²
──────────────────────────────────────
SUM = 27.6 → × 1.30 = 36 m²    (Area_min)

권장값: 40 m²
→ max(36, 40) = 40 m² 채택
```

장비 중 가장 큰 H는 Isolator(3000mm). Default 천장(3000mm)과 같으므로 well-ceiling 불필요.

```python
state.rooms["R_INOCULATION"].area_m2 = 40
state.rooms["R_INOCULATION"].ceiling_height_mm = 3000
state.rooms["R_INOCULATION"].volume_m3 = 40 × 3 = 120
state.rooms["R_INOCULATION"].equipment = [Isolator, Centrifuge, Incubator, Cleanbench]
```

`rationale[]`에 기록:
```python
{
  "rule_id": "rule_3_size",
  "target": "R_INOCULATION",
  "decision": "area=40 m², ceiling=3000mm, volume=120 m³",
  "reason": "권장 40 m² > 장비 기반 36 m² → 권장 채택."
}
```

#### Rule 4 (clean_grade) — 등급 부여 + 색깔
KB의 `default_grade="C"`를 따릅니다. `grade_colors.json`에서 색 토큰 가져옴:

```python
state.rooms["R_INOCULATION"].clean_grade = "C"
state.rooms["R_INOCULATION"].background_color = "#FCD34D"  # Amber-300 (DESIGN.md)
state.rooms["R_INOCULATION"].color_pattern = "solid"
state.rooms["R_INOCULATION"].transparency_pct = 50
```

> 만약 URS에 `aseptic_filling_onsite=true`였다면? → Inoculation은 **Grade B로 격상**되었을 것.
> Grade B는 emerald-300 (#6EE7B7). 이게 룰이 데이터에 맞춰 자동 적응하는 예시.

#### Rule 5 (arrangement) — 그룹핑 + 동선
Inoculation은 `category="process"` 이므로 `zones.process_zone`에 들어감.
또한 `process_order`의 3번째라서 `flow_paths.product_process_order`에 포함:
```python
state.flow_paths.product_process_order = [
    "R_MEDIA_PREP",    # 1
    "R_BUFFER_PREP",   # 2
    "R_INOCULATION",   # 3  ← Seed 접종
    "R_CELL_CULTURE",  # 4
    "R_HARVEST",       # 5
    "R_PURIFICATION_1",
    "R_PURIFICATION_2",
    "R_DS_STORAGE",
]
```

### Phase 6-7: 전실 만들기

#### Rule 6 (airlocks)
Inoculation은 `needs_airlock=true` + `in_one_way_chain=true` + `Grade C` + 공간 여유 → **4개 전실 풀세트** 부여.

```python
# 4개 AL 생성
state.airlocks["AL_001"] = Airlock(type="PAL_in",  connects_higher="R_INOCULATION", ...)
state.airlocks["AL_002"] = Airlock(type="MAL_in",  connects_higher="R_INOCULATION", ...)
state.airlocks["AL_003"] = Airlock(type="PAL_out", connects_higher="R_INOCULATION", ...)
state.airlocks["AL_004"] = Airlock(type="MAL_out", connects_higher="R_INOCULATION", ...)

state.rooms["R_INOCULATION"].one_way_flow = True  # 입구≠출구 확정
```

#### Rule 7 (AL flow type)
Inoculation은 grade C → 기본 **cascade** 적용.
> Grade B/A 였다면 bubble, bio-hazard 시 sink로 바뀜.

```python
for al in [AL_001, AL_002, AL_003, AL_004]:
    al.flow_type = "cascade"
```

### Phase 8: Adjacency (인접 그래프 구축)

`adjacency_builder.build()`가 작동. 각 AL은 두 개의 도어를 만듭니다:

```python
# AL_001 (PAL_in)
state.adjacency.append(Adjacency(
    from_id="R_SUPPLY_CORRIDOR",
    to_id="AL_001",
    relationship="door",
    flow_direction="one_way_in",
))
state.adjacency.append(Adjacency(
    from_id="AL_001",
    to_id="R_INOCULATION",
    relationship="door",
    flow_direction="one_way_in",
))

# AL_003 (PAL_out)
state.adjacency.append(Adjacency(
    from_id="AL_003",
    to_id="R_RETURN_CORRIDOR",  # 출구는 리턴!
    relationship="door",
    flow_direction="one_way_out",
))
# ... 등등
```

이 시점에서 Inoculation은:
```
공급복도 ──→ PAL_in ──→ 접종실 ──→ PAL_out ──→ 리턴복도
공급복도 ──→ MAL_in ──→ 접종실 ──→ MAL_out ──→ 리턴복도
```
이렇게 4갈래로 연결됩니다.

### Phase 9-10: Rules 8-13

#### Rule 8 (corridor): supply/return 분리 확인
Inoculation 자체는 안 건드리지만, supply↔return 직접 연결 금지가 `constraints`에 박힘.

#### Rule 9 (door): MAL 도어 폭 상향
MAL_in/MAL_out은 자재용이므로 도어 폭 1000mm → 1800mm 자동 상향.

#### Rule 10 (equipment): 정량 룰 확정
"장비 간격 ≥ 1000mm, 장비-벽 600~1200mm"가 `constraints.equipment_clearance_mm`에 박힘.
Inoculation의 4개 장비를 process_step 순서로 정렬(P3-1 → P3-2):
```python
[Isolator (P3-1), Centrifuge (P3-1), Incubator (P3-2), Cleanbench (P3-2)]
```

#### Rule 11 (wash/prep): Inoculation 무관
세척실↔준비실 룰. Inoculation은 영향 없음.

#### Rule 12 (NC): Inoculation 무관
NC 룰. Inoculation은 process category라 무관.

#### Rule 13 (pressure cascade) ⭐
드디어 차압 부여. Grade C → **15 Pa**.

```python
state.rooms["R_INOCULATION"].differential_pressure_Pa = 15.0

# AL 차압은 flow_type에 따라
AL_001 (cascade): (15 + 5) / 2 = 10 Pa    # 공급(15) ↔ 리턴(5) 사이
AL_002 (cascade): 10 Pa
AL_003 (cascade): 10 Pa
AL_004 (cascade): 10 Pa
```

ACPH도 KB의 Grade C 값으로 attach:
```python
state.rooms["R_INOCULATION"].air_changes_per_hour = 40
state.rooms["R_INOCULATION"].recovery_time_min = 20
state.rooms["R_INOCULATION"].gowning_type = "무진복"
state.rooms["R_INOCULATION"].gowning_method = "over gowning"
```

#### Rule 9 post-fix (door swing)
이제 차압이 정해졌으므로, 모든 도어의 swing 방향 = 낮은 압력 쪽으로 자동 설정.

### Phase 11: Hard Constraint 검증

`validate_hard_constraints(state)`가 C1~C10을 한 번씩 검사. Inoculation은:
- **C3**: one-way Room의 입구 AL(PAL_in, MAL_in)과 출구 AL(PAL_out, MAL_out) 분리 ✅
- **C5**: Inoculation(15Pa, C) ↔ 공급복도(15Pa, C) — 같은 등급이라 skip
- **C6**: 같은 등급 적용 X
- **C10**: 도어 swing이 낮은 압력 방향 ✅

위반 0건 → strict 모드 통과.

### Phase 12: 최종 출력

WorkingState → `RuleEngineOutput` 변환. JSON으로 직렬화하면:

```json
{
  "id": "R_INOCULATION",
  "name_ko": "Seed 접종실",
  "name_en": "Inoculation",
  "category": "process",
  "clean_grade": "C",
  "area_m2": 40.0,
  "ceiling_height_mm": 3000,
  "volume_m3": 120.0,
  "background_color": "#FCD34D",
  "transparency_pct": 50,
  "differential_pressure_Pa": 15.0,
  "air_changes_per_hour": 40,
  "recovery_time_min": 20,
  "gowning_type": "무진복",
  "gowning_method": "over gowning",
  "one_way_flow": true,
  "equipment": [
    {"name": "Isolator",   "W_mm": 4000, "D_mm": 2000, "H_mm": 3000, ...},
    {"name": "Centrifuge", "W_mm": 1000, "D_mm": 600,  "H_mm": 500,  ...},
    {"name": "Incubator",  "W_mm": 1200, "D_mm": 800,  "H_mm": 600,  ...},
    {"name": "Cleanbench", "W_mm": 2000, "D_mm": 800,  "H_mm": 2000, ...}
  ],
  "process_step_ids": ["P3-1", "P3-2"]
}
```

**이게 Drawing Agent (혜민님)에게 넘어가는 인계서입니다.**

---

## 3. 코드 구조 한눈에

```
src/rule_engine/
├── schemas.py          ┐
│  ├ URSInput           │  Pydantic 모델 (입력/출력 계약)
│  └ RuleEngineOutput   ┘
│
├── kb_loader.py        ── JSON KB 캐시 로더
├── kb/                 ┐
│  ├ rooms_mab.json     │
│  ├ equipment.json     │  데이터 소스 (룰과 분리)
│  ├ grade_colors.json  │
│  ├ acph_table.json    │
│  ├ gowning_table.json │
│  └ flow_policy.json   ┘
│
├── working_state.py    ── 파이프라인 누적 상태 (mutable)
│
├── rules/              ┐
│  ├ rule_01_axis.py    │
│  ├ rule_02_shape.py   │
│  ├ rule_03_size.py    │  각 룰 = 함수 1개: apply(state)
│  ├ rule_04_grade.py   │  반드시 state.log() 호출
│  ├ ...                │
│  └ rule_13_pressure.py┘
│
├── adjacency_builder.py── AL 기반 Room 연결 그래프
├── validators.py       ── C1~C10 hard / C9 soft
└── engine.py           ── 9 Phase 오케스트레이터 (지휘자)
```

### 핵심 디자인 결정

| 결정 | 이유 |
|------|------|
| 룰과 데이터 분리 (Python vs JSON) | modality 추가 시 JSON만 추가, 코드는 안 건드림 |
| 각 룰은 함수 1개 | 단위 테스트 쉽고 RL이 룰별 토글 가능 |
| 모든 결정 rationale 로깅 | 감사 추적·디버깅·논문 결과 정리 |
| Hard vs Soft 분리 | 안전 룰 != 효율 룰. RL은 soft만 최적화 |
| WorkingState mutable | 룰 순서가 중요하고 의존성이 있어 단순함 |
| Pydantic strict mode | 오타 = 즉시 에러. 인터페이스 보호 |

---

## 4. 자주 묻는 질문

### Q1. 왜 좌표(x, y)는 룰엔진이 안 정하나요?
**A**: 룰엔진의 책임은 "어떤 Room이 어떤 관계로 있어야 하는가". 좌표는 그 위에서 결정되는 다른 문제예요. 분리하면:
- 룰 결정 = 결정론적, 빠름, 테스트 쉬움
- 좌표 = 최적화 문제 → **RL이 학습**

이게 Step 8 Drawing Agent와 Step 10 RL이 분리된 이유.

### Q2. URS가 바뀌면 어떻게 되나요?
**A**: 같은 룰이 다른 결과를 냅니다.
- `aseptic_filling_onsite=true` → Inoculation Grade B 자동 격상
- `closed_system_main_process=true` → 주공정 Grade D 허용
- `floor_level=1` → 엘리베이터 룰 skip
- `area_overrides_m2={"R_PURIFICATION_1": 350}` → 권장 무시하고 350 적용

### Q3. 룰 추가하고 싶으면?
**A**:
1. `src/rule_engine/rules/rule_14_xxx.py` 만들기
2. `apply(state)` 함수 1개 정의 (state 받고, log하고, mutate)
3. `engine.py`에 import + 호출 한 줄 추가
4. 테스트 추가
끝.

### Q4. 새 modality (예: vaccine) 지원하려면?
**A**:
1. `kb/rooms_vaccine.json` 만들기 (40종 정도)
2. `kb/flow_policy_defaults.json`에 `"vaccine": {...}` 추가
3. 룰 코드 0줄 수정
4. URS에서 `modality="vaccine"`

### Q5. Validator가 왜 raise까지 가나요? 경고만 하면 안 돼요?
**A**: Strict 모드(default)에서는 hard 위반 = ValueError. 이유:
- GMP는 *안전 직결*. 위반 도면을 묵묵히 통과시키면 사고로 이어짐.
- RL 학습 시 `strict=False`로 두면 위반도 reward 페널티로만 처리 (학습 가능).
- 의도된 듀얼 모드.

### Q6. rationale을 어떻게 쓰면 좋나요?
**A**: 3가지 용도:
- **디버깅**: 왜 이 Room이 Grade B로 갔는지 추적
- **감사**: FDA 같은 규제 기관 제출 시 "이 결정의 근거" 자료
- **논문**: 실험 결과로 "엔진이 N건의 결정을 했으며 모두 룰 X에 근거" 같은 그래프

---

## 5. 다음에 보면 좋은 곳

| 더 자세히 알고 싶다면 | 어디로 |
|---|---|
| 7-블록 인터페이스 스펙 | [ARCHITECTURE.md §2](../ARCHITECTURE.md) |
| 색·타이포·그리드 시스템 | [DESIGN.md](../DESIGN.md) |
| 13 룰 원문 (Layout Logic) | URS_ConceptualDesign + GMP Layout Logic_0510 PDF |
| RL이 이 위에 어떻게 얹히나 | [docs/rl_guide.md](rl_guide.md) |
| 실제 코드 | `src/rule_engine/engine.py`부터 읽기 시작 |

엔진의 모든 결정에는 이유가 있고, 그 이유는 두 곳에 있습니다 — **GMP Layout Logic 문서**와 **출력 JSON의 `rationale[]`**. 막히면 둘을 비교해보세요.
