# Phase 2 — Synthetic Migration Laboratory

## 1. Why Synthetic Data is Used

In legacy database migration verification (e.g. Teradata to PostgreSQL/Snowflake), evaluating AI translation and verification engines against arbitrary production data introduces privacy risks, non-reproducible edge conditions, and missing ground-truth evaluation bounds. 

MIGRA-Q solves this by constructing a **deterministic, synthetic enterprise truth environment**. The synthetic laboratory produces realistic relational datasets alongside isolated adversarial scenarios containing explicit semantic edge cases (boundary values, NULL logic, orphan keys, date anomalies, and multi-row aggregations).

---

## 2. Domain Model

The laboratory models a realistic financial customer transaction & risk domain across four relational entities:

- **Customers**: Primary demographic, income, credit rating, risk tier, and status records.
- **Accounts**: Customer bank accounts (Checking, Savings, Credit, Investment) with balances and limits.
- **Transactions**: High-volume financial activity logs (Purchases, Refunds, Transfers, Fees) tied directly to account and customer IDs.
- **Support Cases**: Customer support interaction logs tracking priority, status, and resolution timelines.

---

## 3. Table Relationships

```
                     ┌──────────────────┐
                     │    customers     │
                     │  (customer_id)   │
                     └────────┬─────────┘
                              │
               ┌──────────────┴──────────────┐
               │ 1:N                         │ 1:N
               ▼                             ▼
     ┌──────────────────┐          ┌──────────────────┐
     │     accounts     │          │  support_cases   │
     │   (account_id)   │          │    (case_id)     │
     └────────┬─────────┘          └──────────────────┘
              │ 1:N
              ▼
     ┌──────────────────┐
     │   transactions   │
     │ (transaction_id) │
     └──────────────────┘
```

For all **normal** datasets, strict referential integrity is guaranteed:
- `accounts.customer_id → customers.customer_id`
- `transactions.account_id → accounts.account_id`
- `transactions.customer_id == accounts.customer_id`
- `support_cases.customer_id → customers.customer_id`

---

## 4. Data Profiles

Scale profiles are fully configurable:

| Profile | Customers | Accounts | Transactions | Support Cases |
|---------|-----------|----------|--------------|---------------|
| `dev`   | 10,000    | 40,000   | 200,000      | 20,000        |
| `demo`  | 50,000    | 200,000  | 1,000,000    | 100,000       |

---

## 5. Randomness & Deterministic Seeding

Generation is 100% deterministic. Passing the same `--seed` and `--profile` guarantees bit-for-bit identical datasets and SHA-256 checksums. Randomness is managed via explicit, isolated `numpy.random.RandomState` instances and seeded `Faker` instances, avoiding global state pollution.

---

## 6. Adversarial Scenarios

Adversarial scenario datasets isolate difficult SQL edge conditions to test future migration validators:

1. **Boundary**: Values placed exactly on thresholds (e.g. refund amounts at 499.99, 500.00, 500.01; credit scores at 599, 600, 601).
2. **NULL Logic**: Controlled NULLs in expressions (e.g. NULL refund amounts, NULL closed dates).
3. **Zero / Negative**: Zero transaction amounts, negative account balances.
4. **Duplicate Keys**: Intentional duplicate business keys in dimension tables.
5. **Missing References**: Orphan transactions referencing non-existent account IDs.
6. **NULL Join Keys**: Accounts with NULL `customer_id` join keys.
7. **Date Edge Cases**: Timestamps on month ends, midnight, and leap days.
8. **Multi-Row Aggregation**: Duplicate refund records to test `COUNT` vs `COUNT DISTINCT` vs `SUM`.

---

## 7. Benchmark Philosophy

The benchmark library contains **20 registered scenario specifications** (15 adversarial edge cases, 5 normal pass cases). These specifications define the input evaluation data and expected semantic concerns without hardcoding or biasing future validation algorithms.

---

## 8. Dataset Format

Datasets are exported canonically in **Apache Parquet** format for columnar storage, high compression, and instant inspection with DuckDB or pandas. Optional CSV exports are also supported.

---

## 9. Manifest Format

Every generated dataset produces a `manifest.json` metadata file:

```json
{
  "dataset_id": "dev_42",
  "generator_version": "0.1.0",
  "schema_version": "0.1.0",
  "seed": 42,
  "profile": "dev",
  "generation_timestamp": "2026-08-15T02:30:00+00:00",
  "row_counts": {
    "customers": 10000,
    "accounts": 40000,
    "transactions": 200000,
    "support_cases": 20000
  },
  "file_names": {
    "customers": "customers.parquet",
    "accounts": "accounts.parquet",
    "transactions": "transactions.parquet",
    "support_cases": "support_cases.parquet"
  },
  "checksums": {
    "customers": "...",
    "accounts": "...",
    "transactions": "...",
    "support_cases": "..."
  }
}
```

---

## 10. Known Limitations

- **Synthesized Realism**: Statistical distributions mirror general enterprise patterns but are not derived from real bank data.
- **Offline Local Scope**: Generation takes place strictly in local Python without external API dependencies.
