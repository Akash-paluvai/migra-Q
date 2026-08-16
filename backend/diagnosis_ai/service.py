"""Orchestration service for Phase 7 AI Diagnosis & Repair Engine."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.diagnosis_ai.context_builder import build_diagnosis_context, build_evidence_pack
from backend.diagnosis_ai.evidence import EvidenceGroundingValidator
from backend.diagnosis_ai.models import (
    AIDiagnosis,
    DiagnosisAIMetadata,
    DiagnosisAIResult,
    DiagnosisContext,
    DiagnosisStatus,
    RepairProposal,
    RepairStatus,
)
from backend.diagnosis_ai.prompts import (
    SYSTEM_PROMPT,
    build_diagnosis_user_prompt,
    compute_prompt_hash,
)
from backend.diagnosis_ai.provider import (
    AIDiagnosisProvider,
    MockDiagnosisProvider,
    OpenAIDiagnosisProvider,
)
from backend.diagnosis_ai.reasoning.confidence import (
    compute_diagnosis_confidence,
    compute_repair_confidence,
)
from backend.diagnosis_ai.repository import save_diagnosis_ai_result
from backend.diagnosis_ai.scope import RepairScopeChecker
from backend.diagnosis_ai.validator import RepairProposalValidator


class DiagnosisAIService:
    """Service orchestrating AI-grounded diagnosis and candidate repair proposal generation."""

    @classmethod
    def diagnose_discrepancy(
        cls,
        discrepancy_id: str,
        category: str,
        severity: str,
        source_sql: str,
        target_sql: str,
        source_dialect: str = "teradata",
        target_dialect: str = "bigquery",
        source_expression: str | None = None,
        target_expression: str | None = None,
        analysis_path: str | None = None,
        affected_row_count: int = 0,
        affected_percentage: float = 0.0,
        affected_columns: list[str] | None = None,
        representative_examples: list[dict] | None = None,
        structural_differences: list[str] | None = None,
        validation_id: str = "val-default",
        translation_id: str = "trans-default",
        provider_name: str | None = None,
        mock_mode: str | None = None,
        db_session: Session | None = None,
    ) -> DiagnosisAIResult:
        """Run Phase 7 AI Diagnosis & Candidate Repair Proposal pipeline.

        NOTE: This function generates a PROPOSED candidate repair. It explicitly does NOT execute
        repaired SQL or perform downstream Phase 3/4/5 validation.
        """
        diagnosis_id = f"diag-ai-{uuid.uuid4().hex[:12]}"
        repair_id = f"rep-{uuid.uuid4().hex[:12]}"
        created_at = datetime.now(timezone.utc).isoformat()

        # 1. Build EvidencePack & DiagnosisContext
        evidence_pack = build_evidence_pack(
            discrepancy_id=discrepancy_id,
            category=category,
            severity=severity,
            source_expression=source_expression,
            target_expression=target_expression,
            analysis_path=analysis_path,
            affected_row_count=affected_row_count,
            affected_percentage=affected_percentage,
            affected_columns=affected_columns,
            representative_examples=representative_examples,
            structural_differences=structural_differences,
        )

        context: DiagnosisContext = build_diagnosis_context(
            discrepancy_id=discrepancy_id,
            validation_id=validation_id,
            translation_id=translation_id,
            source_sql=source_sql,
            target_sql=target_sql,
            source_dialect=source_dialect,
            target_dialect=target_dialect,
            evidence_pack=evidence_pack,
        )

        # 2. Prompts & Hashing
        user_prompt = build_diagnosis_user_prompt(context)
        prompt_hash = compute_prompt_hash(SYSTEM_PROMPT, user_prompt)

        # 3. Provider Selection
        provider_type = (provider_name or settings.LLM_PROVIDER).lower()
        provider: AIDiagnosisProvider
        if mock_mode or provider_type == "mock":
            mode = mock_mode if (mock_mode and mock_mode.startswith("MOCK_")) else "MOCK_BOUNDARY_REPAIR"
            if mode == "MOCK_BOUNDARY_BUG":
                mode = "MOCK_BOUNDARY_REPAIR"
            provider = MockDiagnosisProvider(mode=mode)
            p_name = "mock"
            p_model = mode
        elif provider_type in ("openai", "openrouter", "groq"):
            provider = OpenAIDiagnosisProvider()
            p_name = provider_type
            p_model = settings.LLM_MODEL or "llama3-70b-8192"
        else:
            provider = MockDiagnosisProvider(mode="MOCK_BOUNDARY_REPAIR")
            p_name = "mock"
            p_model = "MOCK_BOUNDARY_REPAIR"

        # 4. Generate Provider Response
        ai_resp, raw_resp = provider.generate_diagnosis_and_repair(
            system_prompt=SYSTEM_PROMPT,
            user_prompt=user_prompt,
            context=context,
        )

        # 5. Evidence Grounding Check
        grounded, ground_msg = EvidenceGroundingValidator.validate_grounding(
            diagnosis_claims=ai_resp.diagnosis_claims,
            repair_claims=ai_resp.repair_claims,
            evidence_pack=evidence_pack,
        )

        if not grounded:
            meta = DiagnosisAIMetadata(
                diagnosis_id=diagnosis_id,
                discrepancy_id=discrepancy_id,
                provider=p_name,
                model=p_model,
                context_hash=context.context_hash,
                prompt_hash=prompt_hash,
                created_at=created_at,
                duration_ms=raw_resp.duration_ms,
                input_token_count=raw_resp.input_tokens,
                output_token_count=raw_resp.output_tokens,
                total_token_count=raw_resp.total_tokens,
                error_code="UNGROUNDED_CLAIM",
                error_message=ground_msg,
            )
            diag = AIDiagnosis(
                diagnosis_id=diagnosis_id,
                discrepancy_id=discrepancy_id,
                status=DiagnosisStatus.FAILED,
                observed_change=ai_resp.observed_change,
                likely_mechanism=ai_resp.likely_mechanism,
                possible_cause=ai_resp.possible_cause,
                uncertainty=ground_msg,
                claims=ai_resp.diagnosis_claims,
                diagnosis_confidence=0.0,
            )
            rep = RepairProposal(
                repair_id=repair_id,
                discrepancy_id=discrepancy_id,
                status=RepairStatus.FAILED,
                original_sql=target_sql,
                proposed_sql="",
                changed_region=ai_resp.changed_region or "",
                rationale="Repair rejected due to ungrounded claims.",
                expected_effect="",
                claims=ai_resp.repair_claims,
                constraints_checked=[],
                repair_confidence=0.0,
            )
            result = DiagnosisAIResult(metadata=meta, diagnosis=diag, repair_proposal=rep)
            save_diagnosis_ai_result(result, db_session)
            return result

        # 6. Candidate Repair Checks (Syntax, Read-only, Contract, Scope)
        proposed_sql = ai_resp.proposed_sql or ""
        changed_region = ai_resp.changed_region or analysis_path or "columns[target]"

        repair_status = RepairStatus.PROPOSED
        diag_status = DiagnosisStatus.DIAGNOSED
        scope_valid = True
        contract_valid = True
        constraints_checked: list[str] = []
        has_insufficient = (
            ai_resp.diagnosis_claims and "insufficient evidence" in ai_resp.observed_change.lower()
        )
        if not proposed_sql or has_insufficient:
            repair_status = RepairStatus.NO_REPAIR
            diag_status = DiagnosisStatus.INSUFFICIENT_EVIDENCE
        else:
            # A. Syntax & Read-Only Safety Check
            syn_valid, syn_msg = RepairProposalValidator.validate_repair_syntax_and_safety(
                proposed_sql=proposed_sql,
                target_dialect=target_dialect,
            )
            if not syn_valid:
                repair_status = RepairStatus.FAILED
                scope_valid = False

            # B. Contract Preservation Check (REPAIR_CONTRACT_CHECK)
            if repair_status == RepairStatus.PROPOSED:
                contract_valid, contract_msg = RepairProposalValidator.validate_target_contract(
                    original_sql=target_sql,
                    proposed_sql=proposed_sql,
                    target_dialect=target_dialect,
                )
                if not contract_valid:
                    repair_status = RepairStatus.FAILED

            # C. AST Repair Scope Check
            if repair_status == RepairStatus.PROPOSED:
                scope_valid, scope_msg, constraints_checked = RepairScopeChecker.verify_repair_scope(
                    original_sql=target_sql,
                    proposed_sql=proposed_sql,
                    target_dialect=target_dialect,
                    changed_region=changed_region,
                )
                if not scope_valid:
                    repair_status = RepairStatus.FAILED

            # D. Effective Change Check (Must not be identical to candidate SQL)
            if repair_status == RepairStatus.PROPOSED:
                diff_valid, diff_msg = RepairProposalValidator.validate_effective_change(
                    original_sql=target_sql,
                    proposed_sql=proposed_sql,
                )
                if not diff_valid:
                    repair_status = RepairStatus.FAILED
                    scope_valid = False

        # 7. Confidence Score Calculations
        diag_conf = compute_diagnosis_confidence(evidence_pack)
        if diag_status == DiagnosisStatus.INSUFFICIENT_EVIDENCE:
            diag_conf = min(diag_conf, 0.50)

        rep_conf = compute_repair_confidence(
            diagnosis_confidence=diag_conf,
            scope_valid=scope_valid and (repair_status == RepairStatus.PROPOSED),
            contract_valid=contract_valid and (repair_status == RepairStatus.PROPOSED),
        )

        meta = DiagnosisAIMetadata(
            diagnosis_id=diagnosis_id,
            discrepancy_id=discrepancy_id,
            provider=p_name,
            model=p_model,
            context_hash=context.context_hash,
            prompt_hash=prompt_hash,
            created_at=created_at,
            duration_ms=raw_resp.duration_ms,
            input_token_count=raw_resp.input_tokens,
            output_token_count=raw_resp.output_tokens,
            total_token_count=raw_resp.total_tokens,
        )

        diag = AIDiagnosis(
            diagnosis_id=diagnosis_id,
            discrepancy_id=discrepancy_id,
            status=diag_status,
            observed_change=ai_resp.observed_change,
            likely_mechanism=ai_resp.likely_mechanism,
            possible_cause=ai_resp.possible_cause,
            uncertainty=ai_resp.uncertainty,
            claims=ai_resp.diagnosis_claims,
            diagnosis_confidence=diag_conf,
        )

        rep = RepairProposal(
            repair_id=repair_id,
            discrepancy_id=discrepancy_id,
            discrepancy_fingerprint=context.discrepancy_fingerprint,
            status=repair_status,
            original_sql=target_sql,
            proposed_sql=proposed_sql if repair_status == RepairStatus.PROPOSED else "",
            changed_region=changed_region,
            changes=ai_resp.changes if repair_status == RepairStatus.PROPOSED else [],
            rationale=ai_resp.repair_rationale or "",
            expected_effect=ai_resp.expected_effect or "",
            claims=ai_resp.repair_claims,
            constraints_checked=constraints_checked,
            repair_confidence=rep_conf,
        )

        result = DiagnosisAIResult(metadata=meta, diagnosis=diag, repair_proposal=rep)
        save_diagnosis_ai_result(result, db_session)
        return result
