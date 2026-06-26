# Hyemin Kim

**B.S. in Architectural Engineering · B.A. in Electrical & Electronic Engineering · B.A. in Political Science & Diplomacy**
Sungkyunkwan University, Seoul, Korea (Student ID: 2021312709)

📞 +82-10-9838-4225 ・ ✉️ [bethany131334@naver.com](mailto:bethany131334@naver.com) / [bethany1313@g.skku.edu](mailto:bethany1313@g.skku.edu)
🔗 [github.com/Hyemin-xxx](https://github.com/Hyemin-xxx) ・ 💼 [linkedin.com/in/HyeminxxKim](https://www.linkedin.com/in/HyeminxxKim)

---

## Education

| Institution | Degree / Program | Period |
|---|---|---|
| Sungkyunkwan University, Seoul, Korea | B.S. Architectural Engineering; B.A. Electrical & Electronic Engineering, Political Science & Diplomacy | Mar. 2021 – Present |
| Yeongdeungpo Girls' High School, Seoul, Korea | High School Diploma | Feb. 2021 |
| Yeouido Middle School, Seoul, Korea | Middle School Diploma | Feb. 2018 |

---

## Research Achievements (연구성과: 특허 · SW · 논문)

### Patents (특허출원)
| Title | Management No. | Status | Filing Date | Inventors |
|---|---|---|---|---|
| 바이오의약품 제조시설의 개념 레이아웃 자동 생성 시스템 및 방법 (System and Method for Automatically Generating Conceptual Layout of Biopharmaceutical Manufacturing Facilities) | R-2026-0673-KR-1 | Filed / Submitted (제출) | 2026-06-26 | 정종필 (대표발명자), **김혜민 (공동발명자)** |

*Related software: **GMP-LayGen** (see below).*

### Software Registration (SW 등록)
| Program Title | Management No. | Status | Provisional Save Date | Lead Author |
|---|---|---|---|---|
| GMP-LayGen | R-2026-0661-KR-1 | Filed / Submitted (제출) | 2026-06-25 | 정종필 (대표창작자) |

### Publications — Individual / Team List (논문 — 개인별·팀별 리스트)
| Title | Type | Status | Venue |
|---|---|---|---|
| GMP-LayGen: URS 기반 GMP 준수 바이오의약품 제조시설 개념 레이아웃 자동 생성 시스템 *(가제, 제목 확정 필요)* | Team | In preparation (작성 중) | _TBD_ |

> ⚠️ 논문 제목은 초록을 토대로 임시로 붙인 가제입니다. 정확한 제목, 투고 예정 학회/저널, 공동저자 명단을 알려주시면 바로 수정하겠습니다.

**Abstract (국문 초록):**
> 바이오의약품 GMP(Good Manufacturing Practice) 제조시설의 구축을 위해서 가장 핵심적인 단계 중 하나는 최적의 개념 레이아웃(Conceptual Layout)을 도출하는 것이다. 그러나 이것은 EU GMP Annex 1으로 대표되는 규제 요건과 교차오염 방지를 위한 동선의 분리, 청정도 등급 구배 등 다수의 상호 의존적 제약을 동시에 만족해야 하는 고난도·고비용의 전문가 의존 영역이다. 기존의 자동 평면 생성 연구는 대부분 주거·사무·반도체 등 비규제 영역을 대상으로 하여, 오염 제어가 핵심 제약이 되는 GMP 제조시설에는 직접 적용하기 어렵다. 본 연구는 사용자 요구사항규격서(URS)로부터 GMP 준수 개념레이아웃을 자동으로 생성하는 시스템 'GMP-LayGen'을 개발하였다. 고안된 시스템은 바이오의약품 제조설계 원리의 규칙 기반과 GMP 제조시설 가이드라인의 검색증강생성(RAG) 기반의 검증을 통해 GMP 규정에 적합한 레이아웃의 제약사항을 생성하며 모든 설계 결정에 근거를 부착하여 GMP 제조시설 설계의 근거에 대한 추적성을 확보하였다.

---

## Capstone Design Project (캡스톤디자인)

### 1. GMP-LayGen — GMP-Compliant Biopharmaceutical Facility Conceptual Layout Auto-Generation System *(Current, 2026)*
- **Period:** 2026 – Present
- **Partner:** Industry R&D Project with GC Biopharma (GC녹십자) | ISPE Vol.6 (2023) compliance-driven
- **IP Status:** Patent filed (R-2026-0673-KR-1, 2026-06-26) · Software registered (R-2026-0661-KR-1, 2026-06-25)
- **Summary:** Developed an AI system, "GMP-LayGen," that automatically generates GMP-compliant conceptual layouts for biopharmaceutical manufacturing facilities directly from User Requirement Specifications (URS). The system combines rule-based generation grounded in biopharmaceutical facility design principles with RAG (Retrieval-Augmented Generation)-based verification against GMP guidelines, producing layout constraints that satisfy interdependent regulatory requirements (e.g., EU GMP Annex 1, cross-contamination prevention, cleanliness-grade gradients) while attaching traceable justification to every design decision.
- *Full technical write-up below under "GMP-LayGen — Project Details."*

### 2. Hakto — AI Service for Engineering Students *(Past, 2025)*
- **Period:** Sep. 2025 – Dec. 2025
- **Partner:** Industry–Academia Collaboration with Mediopia Tech
- **Tools & Technologies:** Python, RAG, OLLAMA, Flowise, LLM fine-tuning
- **Award:** 🏆 Excellence Award (우수상), AI Capstone Design Showcase, Sungkyunkwan University (2025)
- **Summary:** Designed and developed an AI-powered academic assistant for engineering students using RAG (Retrieval-Augmented Generation) and LLM fine-tuning, in collaboration with Mediopia Tech. Awarded the Excellence Prize at the AI Capstone Design showcase.

---

## GMP-LayGen — Project Details

### URS-based CCD Auto-Generation AI System for Biopharmaceutical Manufacturing Facilities
- **Period:** 2026 – Present
- **Partner:** Industry R&D Project with GC Biopharma (GC녹십자) | ISPE Vol.6 (2023) compliance-driven

**Topic:** Development of an AI system that auto-generates the full Conceptual Design (CCD) document package for biopharmaceutical manufacturing facilities from User Requirement Specifications (URS), covering both traditional process engineering (DS) and Industry 4.0 / Pharma 4.0 smart factory domains.

**Problem & Approach:** Korea's biopharma sector relies heavily on global EPCM firms (NNE Pharmaplan, Jacobs, CRB) for CCD, costing 6–8 months and 3–8억원 per project; their edge lies in quantitative know-how absent from public standards. Reverse-engineered NNE's real CCD packages (16 docs under NDA) to extract 10 formulas / lookup tables (F1–F10), including the Class ↔ Filter ↔ ACR ↔ Pressure rule validated across 61 cleanrooms.

**Architecture:** 7-module hybrid with strict separation of deterministic kernels (Python + SymPy + Z3 SMT solver + MILP) from LLM agents (Claude Sonnet 4.6 / Opus 4.6). All outputs linked through a Traceability Bus: `URS_ID → Assumption_ID → Formula_ID → Document_ID`. Knowledge graph (RDF/OWL) encodes ISPE Vol.6 (10 chapters + 4 appendices), ISA-95, GAMP 5, Annex 1, ALCOA+, ICH Q8-Q11.

**Three Novelty Axes:**
1. Unified CSP/SMT constraint propagation across Process/Facility/Utility/Automation domains with auto back-propagation on URS change
2. Modality-aware knowledge graph (mAb / viral vector / mRNA-LNP) with automatic ALCOA+ 9-attribute tagging
3. Deterministic kernel × LLM hybrid with full audit traceability aligned to ISPE Stage Gate Model (App.1) and Sample Rooms List (App.2)

**Role:** Led NNE package reverse-engineering, URS ↔ NNE ↔ ISPE tri-axis schema mapping (57 sheets × 16 docs), and Phase B calculation-engine specification; co-designed the end-to-end system architecture and the proposal document (20p full + 5p executive brief).

**Outcomes:**
(i) ✅ Patent filed — "바이오의약품 제조시설의 개념 레이아웃 자동 생성 시스템 및 방법" (R-2026-0673-KR-1, 2026-06-26); 2 more patents planned, one per remaining novelty axis
(ii) 🔄 1 paper in preparation — *GMP-LayGen* (Korean abstract drafted); 1 additional international journal paper targeting *Computers & Chemical Engineering* or *J. Pharmaceutical Innovation* still planned, featuring human-vs-AI deviation as the key figure
(iii) ✅ Software registration filed — **GMP-LayGen** (R-2026-0661-KR-1, 2026-06-25)
(iv) internal deployment at GC Biopharma to internalize CCD capability, progressively extending to Basic / Detailed Design phases, with later open release for Korean biopharma industry standardization

---

## Experience

### AI Service Planning & Strategy Intern — Mediopia Tech, Seoul, Korea
*Jan. 2026 – Present*
- Led planning and quality assurance of AI-based educational services, ensuring alignment with product goals and user needs.
- Built and maintained internal chatbot systems; conducted systematic QA and iterative improvement of AI outputs.
- Supported strategic business development initiatives and contributed to marketing planning for AI product launches.

### Independent Tutor — Private Tutoring (Math, Physics, Chemistry, Biology), Seoul, Korea
*Jan. 2021 – Present*
- Provided one-on-one tutoring in mathematics, physics, chemistry, and biology for middle and high school students.
- Developed customized study plans and materials tailored to individual student needs and exam objectives.

### Student Mentor — Samsung Junior SW Creative Contest, Seoul, Korea
*Jul. 9, 2022 – Sep. 3, 2022*
- Mentored participating students in software development concepts and project execution during the contest period.
- Provided technical guidance and feedback to support teams throughout the competition.

### QA Intern — Miroboard (Startup), Seoul, Korea
*Jan. 2023*
- Performed pre-launch compatibility testing to identify and document conflicts with third-party services and platforms.
- Organized and reported QA findings; provided actionable recommendations for product quality improvement.

---

## Other Projects

### Blockchain Governance DAO System — Blockchain Society (SKKrypto) Internal Project (2023)
- Tools & Technologies: Solidity, Ethereum, smart contracts
- Designed and implemented a DAO-based on-chain voting and governance system for use within the university blockchain society.

### Polkadot Korea — Substrate Node Setup (2022)
- Tools & Technologies: Rust, Substrate framework
- Contributed to setting up and configuring a Substrate-based blockchain node as part of the Polkadot Korea ecosystem initiative.

### Upbit Whitepaper Korean Translation Project — SKKrypto Blockchain Society × Dunamu (Upbit) (2022)
- Collaborated with Dunamu (operator of Upbit exchange) to translate the full set of cryptocurrency whitepapers listed on Upbit into Korean.
- Ensured technical accuracy and consistency across a large volume of blockchain documentation.

---

## Technical Skills and Interests

- **Languages:** Python, C, Rust, Solidity
- **Developer Tools:** Git, GitHub, Flowise, OLLAMA, Figma
- **Frameworks/Technologies:** RAG (Retrieval-Augmented Generation), LLM, Substrate, Ethereum
- **Areas of Interest:** AI/LLM Applications, Blockchain & Web3, EdTech, Strategic Planning, Product QA

---

## Extracurricular Activities

- **Member**, SKKrypto (Blockchain Society), Sungkyunkwan University — 2022 – 2023
- **Member**, Sungmihoe (Fine Arts Club), Sungkyunkwan University — 2022 – 2026

## Achievements

- **Excellence Award**, AI Capstone Design Project — Hakto, Sungkyunkwan University — 2025
