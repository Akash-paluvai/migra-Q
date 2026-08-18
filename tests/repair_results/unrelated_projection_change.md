# Repair Report: unrelated_projection_change

## Source SQL
```sql
SELECT product_id, list_price, status FROM product_catalog
```

## Target SQL
```sql
SELECT product_id, list_price * 10 AS list_price, status FROM product_catalog
```

## Validation Status: FAIL
## Discrepancy Found
- **Category**: UNKNOWN
- **Source Exp**: 10430.0
- **Target Exp**: 104300.0

## AI Diagnosis
- **Status**: DIAGNOSED
- **Observed Change**: Mock deterministic change.

## Repair Proposal
- **Status**: FAILED
- **Proposed SQL**:
```sql

```
- **Rationale**: Deterministic regression mock
- **Constraints Checked**: ['target_dialect_syntax_preserved', 'read_only_policy_enforced', 'target_contract_preserved', 'join_clause_unchanged', 'groupby_clause_unchanged', 'where_clause_unchanged']

