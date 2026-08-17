# Repair Report: window_function

## Source SQL
```sql
SELECT account_id, RANK() OVER(PARTITION BY customer_id ORDER BY balance DESC) AS rnk FROM accounts
```

## Target SQL
```sql
SELECT account_id, ROW_NUMBER() OVER(PARTITION BY customer_id ORDER BY balance DESC) AS rnk FROM accounts
```

## Validation Status: FAIL
## Discrepancy Found
- **Category**: UNKNOWN
- **Source Exp**: 1.0
- **Target Exp**: 2.0

## AI Diagnosis
- **Status**: DIAGNOSED
- **Observed Change**: Mock deterministic change.

## Repair Proposal
- **Status**: PROPOSED
- **Proposed SQL**:
```sql
SELECT account_id, RANK() OVER(PARTITION BY customer_id ORDER BY balance DESC) AS rnk FROM accounts
```
- **Rationale**: Deterministic regression mock
- **Constraints Checked**: ['target_dialect_syntax_preserved', 'read_only_policy_enforced', 'target_contract_preserved', 'join_clause_unchanged', 'groupby_clause_unchanged', 'where_clause_unchanged', 'unrelated_projection_expressions_unchanged']

## Verification Result
- **Status**: VERIFIED
- **Remaining Discrepancies**: 0
