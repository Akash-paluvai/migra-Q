# Repair Report: conditional_aggregation

## Source SQL
```sql
SELECT department, SUM(CASE WHEN gate_status = 'PASS' THEN score ELSE 0 END) AS passing_score FROM enterprise_metrics GROUP BY department
```

## Target SQL
```sql
SELECT department, SUM(score) AS passing_score FROM enterprise_metrics GROUP BY department
```

## Validation Status: FAIL
## Discrepancy Found
- **Category**: UNKNOWN
- **Source Exp**: 0.0
- **Target Exp**: 19554687.5

## AI Diagnosis
- **Status**: DIAGNOSED
- **Observed Change**: Mock deterministic change.

## Repair Proposal
- **Status**: PROPOSED
- **Proposed SQL**:
```sql
SELECT department, SUM(CASE WHEN gate_status = 'PASS' THEN score ELSE 0 END) AS passing_score FROM enterprise_metrics GROUP BY department
```
- **Rationale**: Deterministic regression mock
- **Constraints Checked**: ['target_dialect_syntax_preserved', 'read_only_policy_enforced', 'target_contract_preserved', 'join_clause_unchanged', 'groupby_clause_unchanged', 'where_clause_unchanged', 'unrelated_projection_expressions_unchanged']

## Verification Result
- **Status**: VERIFIED
- **Remaining Discrepancies**: 0
