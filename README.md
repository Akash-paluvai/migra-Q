# Migra-Q: Automated SQL & Database Migration Assurance Platform

![Migra-Q Architecture](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![React](https://img.shields.io/badge/React-18%2B-blue) ![DuckDB](https://img.shields.io/badge/DuckDB-1.0%2B-yellow) ![License](https://img.shields.io/badge/License-MIT-green)

**Migra-Q — AI-Assisted, Deterministically Verified SQL Migration**

Migra-Q translates SQL across database dialects, executes the candidate in an isolated DuckDB sandbox, compares source and target behavior, diagnoses semantic discrepancies, proposes repairs, and produces an auditable assurance decision.

**AI proposes. Deterministic execution and validation decide.**

---

## What Happens When Something Goes Wrong?

Migra-Q is built to handle the complexities of real-world migrations gracefully. 

| Situation | Result |
| :--- | :--- |
| Query references missing dataset column | **BLOCKED** — `INPUT_SCHEMA_MISMATCH` |
| Target execution fails | **FAILED** |
| Semantic mismatch detected | AI diagnosis/repair may run |
| Repair verification fails | **BLOCKED** |
| Provider quota exhausted | **BLOCKED_PROVIDER_LIMIT** |
| Source/target behavior matches | **VERIFIED** |

---

## Key Features

- 🖥️ **Enterprise Product UI**: Incedo-inspired light enterprise visual design language (`LOGIC → BEHAVIOR → EVIDENCE → REPAIR → ASSURANCE`) powered 100% by backend REST APIs.
- 🔄 **Multi-Dialect SQL Translation**: Automated transformation between SQL dialects (e.g. Teradata / Oracle PL/SQL to BigQuery / Snowflake) using dialect-aware LLM translation.
- 🎯 **5-Stage Validation Engine**: Multi-layer deterministic sandbox execution comparing output schemas, row sets, aggregates, business rules, and edge cases.
- 🩺 **AI Discrepancy Diagnosis & Repair**: Agentic classification of semantic discrepancies (e.g. boundary condition operators) and automated AST patch synthesis.
- 📊 **Assurance Scoring & Quality Gates**: Quantitative 0-100 score renormalized over applicable components and strict deterministic hard quality gates.
- 🏎️ **In-Memory High-Speed Execution**: Powered by an embedded **DuckDB** sandbox for rapid local validation without touching production databases.

---

## Documentation

The platform's methodology and technical design are documented comprehensively in the `docs/` directory:

1. [**Architecture**](docs/ARCHITECTURE.md): The 9-phase orchestration pipeline, execution boundaries, and state machine.
2. [**Approach**](docs/APPROACH.md): The philosophy of deterministic verification over purely generative LLM translations.
3. [**Terminology**](docs/TERMINOLOGY.md): Glossary for domain concepts like *Schema Preflight*, *Hard Gates*, and *Assurance Score*.
4. [**Development**](docs/DEVELOPMENT.md): Guide for setting up the environment, running tests, and debugging migration failures.
5. [**Validation**](docs/VALIDATION.md): Deep dive into the Schema, Row, Aggregate, Business Rule, and Edge Case validators.

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
