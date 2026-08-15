"""Evidence grounding validator for Phase 7 AI Diagnosis Engine.

Ensures every claim made by the AI references valid evidence IDs in the EvidencePack.
Rejects ungrounded claims or unknown evidence references.
"""

from __future__ import annotations

from backend.diagnosis_ai.models import EvidencePack, GroundedClaim


class EvidenceGroundingValidator:
    """Validates evidence citations in AI-generated claims."""

    @staticmethod
    def validate_grounding(
        diagnosis_claims: list[GroundedClaim],
        repair_claims: list[GroundedClaim],
        evidence_pack: EvidencePack,
    ) -> tuple[bool, str]:
        """Validate that all claims reference valid, existing evidence IDs in the EvidencePack.

        Returns (is_valid, error_message).
        """
        valid_ids = {item.evidence_id for item in evidence_pack.items}

        if not valid_ids:
            return False, "EvidencePack contains no valid evidence items for citation."

        all_claims = diagnosis_claims + repair_claims
        if not all_claims:
            return False, "AI response contained no grounded claims."

        for i, claim in enumerate(all_claims, 1):
            if not claim.evidence_refs:
                return False, f"Claim {i} ('{claim.text}') contains no evidence references."

            for ref in claim.evidence_refs:
                if ref not in valid_ids:
                    return (
                        False,
                        f"Claim {i} ('{claim.text}') references unknown evidence ID '{ref}'. "
                        f"Valid IDs are: {sorted(valid_ids)}",
                    )

        return True, "All claims successfully grounded in valid EvidencePack IDs."
