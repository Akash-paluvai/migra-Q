# MIGRA-Q Phase 10 — Product UI & Control Plane Architecture

## 1. Overview

Phase 10 introduces the MIGRA-Q Enterprise Product UI, an orchestration control plane inspired by Incedo's AI & Data Modernization platforms. The UI acts as a thin presentation layer powered 100% by MIGRA-Q Phase 1–9 backend APIs.

```
       MIGRA-Q ENTERPRISE PRODUCT UI (React + Vite + Light Enterprise Theme)
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                                                                         │
  │  LandingPage ──► MigrationsPage ──► NewMigration ──► Workspace (Tabs)   │
  │       │                                                       │         │
  │  Hero Visual                                            WorkflowStepper │
  │  (LOGIC → BEHAVIOR → EVIDENCE → REPAIR → ASSURE)              │         │
  │                                                               │         │
  └───────────────────────────────────┬─────────────────────────────────────┘
                                      │ REST API Calls
                                      ▼
  ┌─────────────────────────────────────────────────────────────────────────┐
  │                       MIGRA-Q BACKEND API ENGINE                        │
  │                                                                         │
  │  GET /api/v1/migrations              (List workbench data)              │
  │  GET /api/v1/migrations/flagship     (Instant retrieval shortcut)       │
  │  POST /api/v1/migrations/run         (Execute migration workflow)       │
  │  GET /api/v1/migrations/{id}         (Get record status)                │
  │  GET /api/v1/migrations/{id}/assurance (Full Phase 9 Assurance Report)    │
  │  GET /api/v1/migrations/{id}/lineage   (Audit provenance chain)         │
  └─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Incedo-Inspired Design System

- **Typography**: Inter headings in Deep Navy (`#0A192F`, `#0F172A`) and Slate body copy (`#475569`, `#64748B`). JetBrains Mono for SQL code.
- **Surfaces**: Crisp white background (`#FFFFFF`), light slate panels (`#F8FAFC`, `#F1F5F9`), thin borders (`#E2E8F0`), soft elevated shadows.
- **Accents**: Deep Navy top header (`#0A192F`), Enterprise Blue CTAs (`#2563EB`, `#1D4ED8`), status green (`#16A34A`), amber (`#D97706`), red (`#DC2626`).
- **Signature Visuals**:
  - `HeroVisual`: `LEGACY LOGIC → AI TRANSLATION → BEHAVIOR CHECK → EVIDENCE → REPAIR → VERIFIED`
  - `WorkflowStepper`: `ANALYZE → TRANSLATE → EXECUTE → VALIDATE → DIAGNOSE → REPAIR → VERIFY → ASSURE`

---

## 3. Strict Backend Truth Principles

1. **No Hardcoded Literals**: Frontend components display dynamic values retrieved from API responses (`report.verification_summary.affected_rows_before`, `report.score.evidence_score`, etc.).
2. **Itemized Gate Rendering**: Hard gates render precise outcomes (`N PASS, N NOT APPLICABLE, N FAIL`) without converting `NOT_APPLICABLE` to `PASS`.
3. **Concept Separation**:
   - *Assurance Score*: How well evaluated validation dimensions performed.
   - *Evidence Coverage*: How much of the configured validation scope was actually evaluated.
   - *Final Decision*: Determined by hard gates and verification evidence.
4. **Flagship Retrieval Shortcut**: `GET /api/v1/migrations/flagship` retrieves an existing persisted flagship record instantly without forcing re-computation.

---

## 4. Key Page Views

| Route | View | Description |
| :--- | :--- | :--- |
| `/` | `LandingPage` | Hero proposition, process flow diagram, outcome strip, capability cards 01/02/03, CTAs. |
| `/migrations` | `MigrationsPage` | Enterprise workbench data table, status filters, search input. |
| `/migrations/new` | `NewMigrationPage` | Dialect selection, dataset profile, SQL editor, flagship prefill button. |
| `/migrations/:id` | `MigrationWorkspace` | Overview tab, top KPI cards, workflow stepper, tab navigation bar. |
| `/migrations/:id/translation` | `TranslationView` | Code comparison, syntax status labels, structured logic breakdown. |
| `/migrations/:id/validation` | `ValidationView` | Multi-layer validation checklist, mismatch counts, affected record metrics. |
| `/migrations/:id/discrepancies` | `DiscrepanciesView` | Discrepancies table, boundary comparison diff, observed row evidence. |
| `/migrations/:id/diagnosis` | `DiagnosisView` | AI-grounded diagnosis report (Observed change, Mechanism, Cause, Uncertainty). |
| `/migrations/:id/repair` | `RepairView` | Repair SQL diff, safety checklist, `✓ INDEPENDENTLY VERIFIED` badge. |
| `/migrations/:id/verification` | `VerificationView` | Hero proof page (`BEFORE N → AFTER 0`, 100% reduction, dataset unchanged). |
| `/migrations/:id/assurance` | `AssuranceView` | Score vs Coverage vs Decision grid, `CoverageChecklist`, `HardGateTable`, `HowDecidesBlock`. |
| `/migrations/:id/lineage` | `LineageView` | Visual audit lineage timeline linking artifact IDs across all phases. |

---

## 5. Verification & Testing

- **Backend Pytest Suite**: 97 assurance tests pass (`python -m pytest tests/assurance/`).
- **Frontend Vitest Suite**: Component & routing tests pass (`npm test`).
- **Production Build**: Compiles cleanly with TypeScript (`npm run build`).
