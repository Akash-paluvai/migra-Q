# Repair Report: join_drift

## Source SQL
```sql
SELECT p.ref_code, COUNT(s.detail_id) AS detail_count FROM primary_entity p LEFT JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code
```

## Target SQL
```sql
SELECT p.ref_code, COUNT(s.detail_id) AS detail_count FROM primary_entity p INNER JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code
```

## Validation Status: FAIL
## Discrepancy Found
- **Category**: UNKNOWN
- **Source Exp**: 3200.0
- **Target Exp**: 4000.0

## AI Diagnosis
- **Status**: DIAGNOSED
- **Observed Change**: Mock deterministic change.

## Repair Proposal
- **Status**: PROPOSED
- **Proposed SQL**:
```sql
SELECT p.ref_code, COUNT(s.detail_id) AS detail_count FROM primary_entity p LEFT JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code
```
- **Rationale**: Deterministic regression mock
- **Constraints Checked**: ['target_dialect_syntax_preserved', 'read_only_policy_enforced', 'target_contract_preserved', 'join_clause_unchanged', 'groupby_clause_unchanged', 'where_clause_unchanged', 'unrelated_projection_expressions_unchanged']

## Verification Result
- **Status**: VERIFIED
- **Remaining Discrepancies**: 0
