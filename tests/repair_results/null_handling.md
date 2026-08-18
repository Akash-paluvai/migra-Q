# Repair Report: null_handling

## Source SQL
```sql
SELECT product_id, COALESCE(list_price, 0.0) AS price FROM product_catalog
```

## Target SQL
```sql
SELECT product_id, list_price AS price FROM product_catalog
```

## Validation Status: FAIL
## Discrepancy Found
- **Category**: UNKNOWN
- **Source Exp**: 0.0
- **Target Exp**: nan

## AI Diagnosis
- **Status**: DIAGNOSED
- **Observed Change**: Mock deterministic change.

## Repair Proposal
- **Status**: PROPOSED
- **Proposed SQL**:
```sql
SELECT product_id, COALESCE(list_price, 0.0) AS price FROM product_catalog
```
- **Rationale**: Deterministic regression mock
- **Constraints Checked**: ['target_dialect_syntax_preserved', 'read_only_policy_enforced', 'target_contract_preserved', 'join_clause_unchanged', 'groupby_clause_unchanged', 'where_clause_unchanged', 'unrelated_projection_expressions_unchanged']

## Verification Result
- **Status**: VERIFIED
- **Remaining Discrepancies**: 0
