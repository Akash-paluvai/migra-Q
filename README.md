# Migra-Q: Automated SQL & Database Migration Assurance Platform

![Migra-Q Architecture](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![React](https://img.shields.io/badge/React-18%2B-blue) ![DuckDB](https://img.shields.io/badge/DuckDB-1.0%2B-yellow) ![License](https://img.shields.io/badge/License-MIT-green)

**Migra-Q — AI-Assisted, Deterministically Verified SQL Migration**

Migra-Q translates SQL across database dialects, applies proven dialect compatibility adapters, executes the candidate in an isolated DuckDB sandbox, compares source and target behavior, diagnoses semantic discrepancies, proposes repairs, and produces an auditable assurance decision.

**AI proposes. Deterministic execution and capability assurance decide.**

---

## What Happens When Something Goes Wrong?

Migra-Q is built to handle the complexities of real-world migrations gracefully. 

| Situation | Result |
| :--- | :--- |
| Query references missing dataset column | **BLOCKED** — `INPUT_SCHEMA_MISMATCH` |
| Sandbox cannot execute specific proprietary function | **BLOCKED** — `UNSUPPORTED_CAPABILITY` |
| Target execution fails syntactically | **FAILED** |
| Validation detects semantic mismatch | AI diagnosis/repair may run |
| Repair verification fails | **BLOCKED** |
| Provider quota exhausted | **BLOCKED_PROVIDER_LIMIT** |
| Execution succeeds, but relied on AST approximations | **INCONCLUSIVE** |
| Source/target behavior matches strictly | **VERIFIED** |

---

## Key Features

- 🖥️ **Enterprise Product UI**: Incedo-inspired light enterprise visual design language (`LOGIC → BEHAVIOR → EVIDENCE → REPAIR → ASSURANCE`) powered 100% by backend REST APIs.
- 🔄 **Multi-Dialect SQL Translation**: Automated transformation between SQL dialects (e.g. Teradata / Oracle PL/SQL to BigQuery / Snowflake) using dialect-aware LLM translation.
- 🧩 **Dialect Compatibility Adapters**: Bridging proven semantic gaps (e.g. `ZEROIFNULL` to `COALESCE`) dynamically before execution to ensure the DuckDB Sandbox evaluates valid logic, rather than blindly throwing syntax errors.
- 🎯 **5-Stage Validation Engine**: Multi-layer deterministic sandbox execution comparing output schemas, row sets, aggregates, business rules, and edge cases.
- 🛡️ **Semantic Assurance Gating**: Hard gating that coerces speculative AI transformations (`APPROXIMATION` or `UNKNOWN`) to an `INCONCLUSIVE` status, refusing to falsely `VERIFY` unsafe translations.
- 🩺 **AI Discrepancy Diagnosis & Repair**: Agentic classification of semantic discrepancies and automated AST patch synthesis.
- 🏎️ **In-Memory High-Speed Execution**: Powered by an embedded **DuckDB** sandbox for rapid local validation without touching production databases.

---

## Documentation

The platform's methodology and technical design are documented comprehensively in the `docs/` directory:

1. [**Architecture**](docs/ARCHITECTURE.md): The 9-phase orchestration pipeline, Dialect Adapters, and the Semantic Confidence state machine.
2. [**Approach**](docs/APPROACH.md): The philosophy of deterministic verification and sandbox boundaries over purely generative LLM translations.
3. [**Terminology**](docs/TERMINOLOGY.md): Glossary for domain concepts like *Schema Preflight*, *Capability Check*, and *Assurance Score*.
4. [**Development**](docs/DEVELOPMENT.md): Guide for setting up the environment, running tests, and debugging migration failures with strict capability checks.
5. [**Validation**](docs/VALIDATION.md): Deep dive into the 5-stage validators and Assurance Gating rules.

---

## Quickstart

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)

### 2. Backend Setup
```bash
# Clone the repository
git clone https://github.com/Akash-paluvai/migra-Q.git
cd migra-Q

# Install Python dependencies
pip install -e .

# Copy environment template
cp .env.example .env

# Run FastAPI backend server
uvicorn backend.main:app --reload --port 8000
```
*FastAPI Interactive API Docs will be available at `http://localhost:8000/docs`.*

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Frontend UI will be running at `http://localhost:5173`.*

---

## Testing

The automated backend suite currently passes.

Run unit & integration tests:
```bash
pytest tests/
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
