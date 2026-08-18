# Repair Report: unauthorized_join_change

## Source SQL
```sql
SELECT p.ref_code, SUM(p.base_val) AS total_base FROM primary_entity p LEFT JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code
```

## Target SQL
```sql
SELECT p.ref_code, SUM(p.base_val) AS total_base FROM primary_entity p INNER JOIN secondary_entity s ON p.ref_code = s.ref_code GROUP BY p.ref_code
```

## Validation Status: FAIL
## Discrepancy Found
- **Category**: UNKNOWN
- **Source Exp**: 50
- **Target Exp**: 40

## AI Diagnosis
- **Status**: DIAGNOSED
- **Observed Change**: Mock deterministic change.

## Repair Proposal
- **Status**: FAILED
- **Proposed SQL**:
```sql

```
- **Rationale**: Deterministic regression mock
- **Constraints Checked**: ['target_dialect_syntax_preserved', 'read_only_policy_enforced', 'target_contract_preserved']

