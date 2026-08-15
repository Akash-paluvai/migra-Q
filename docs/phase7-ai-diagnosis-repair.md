# Phase 7 — AI-Grounded Discrepancy Diagnosis & Repair Proposal Engine

## Executive Overview

Phase 7 introduces AI-driven reasoning to MIGRA-Q to answer two core questions for detected discrepancies:
1. **WHY does the discrepancy likely exist?** (`AIDiagnosis`)
2. **WHAT minimal candidate repair should be proposed?** (`RepairProposal`)

---

## Architectural Trust Boundary

```text
Phase 5 DiscrepancyReport (WHAT changed)
             │
             ▼
DiagnosisContext / EvidencePack Builder (E-001, E-002, E-003, E-004, E-005)
             │
             ▼
System Prompt + User Prompt (prompt_hash)
             │
             ▼
LLM Provider (OpenAIDiagnosisProvider / MockDiagnosisProvider) -> DiagnosisAIResponse
             │
             ▼
EvidenceGroundingValidator (Grounding check on GroundedClaim objects)
             │
             ▼
RepairProposalValidator (SQLGlot Syntax + Read-only Safety + REPAIR_CONTRACT_CHECK)
             │
             ▼
RepairScopeChecker (SQLGlot AST Structural Node Comparison vs changed_region)
             │
             ▼
Confidence Calculator (diagnosis_confidence & repair_confidence)
             │
             ▼
PostgreSQL Persistence (ai_diagnoses, repair_proposals, repair_changes) -> STOP
```

> [!IMPORTANT]
> **Trust Boundary Enforcement**:
> - Candidate repair status is strictly `PROPOSED` (or `NO_REPAIR` / `FAILED`).
> - Phase 7 **never** executes SQL, **never** runs Phase 3/4/5 validation, and **never** labels a repair `VERIFIED`, `APPROVED`, or `EQUIVALENT`.

---

## Key Enforcements & Validation Pipeline

1. **Evidence Grounding (`EvidenceGroundingValidator`)**:
   - Requires explicit `GroundedClaim` objects with `text` and `evidence_refs: list[str]`.
   - Validates every claim citation against `EvidencePack` stable IDs (`E-001`, `E-002`, `E-003`, `E-004`, `E-005`).
   - Rejects ungrounded claims or unknown evidence refs as `UNGROUNDED_CLAIM`.

2. **Read-Only Safety (`RepairProposalValidator`)**:
   - Enforces read-only safety policy using SQLGlot AST node walking.
   - Rejects `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `CREATE`, `MERGE` mutations.

3. **Target Contract Check (`REPAIR_CONTRACT_CHECK`)**:
   - Parses `target_sql` and `proposed_sql` in `target_dialect`.
   - Verifies output column aliases match between original target and candidate repair target SQL.

4. **AST Repair Scope Check (`RepairScopeChecker`)**:
   - Compares SQLGlot AST structures between original target SQL and candidate repair target SQL.
   - Verifies changes are strictly localized to `changed_region` (e.g. `columns[risk_class]`).
   - Rejects scope creep (e.g. modifying `JOIN`, `GROUP BY`, `WHERE`, or unrelated projections) as `UNJUSTIFIED_SCOPE_CHANGE`.

5. **Separate Confidence Scores**:
   - Computes distinct `diagnosis_confidence` and `repair_confidence` based on evidence grounding, scope localization, and contract preservation.

---

## Verification & Testing

- **329 of 329 tests passed** (`pytest -v`)
- **0 linter errors** (`ruff check backend/ tests/`)
- Verifies flagship boundary refund scenario, 9 mock provider scenarios, prompt injection defense, AST scope creep rejection, contract check rejection, and PostgreSQL persistence fallback.
