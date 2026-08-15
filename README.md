# Migra-Q: Automated SQL & Database Migration Assurance Platform

![Migra-Q Architecture](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![DuckDB](https://img.shields.io/badge/DuckDB-1.0%2B-yellow) ![License](https://img.shields.io/badge/License-MIT-green)

**Migra-Q** is an end-to-end automated platform for SQL dialect translation, multi-stage semantic equivalence validation, mismatch diagnosis, automated patch repair, and assurance scoring. It ensures zero data loss, zero semantic drift, and high-confidence migration across heterogeneous database engines (Oracle, PostgreSQL, Snowflake, BigQuery, MySQL, SQLite, DuckDB).

---

## Key Features

- 🖥️ **Phase 10 Enterprise Product UI**: Incedo-inspired light enterprise visual design language (`LOGIC → BEHAVIOR → EVIDENCE → REPAIR → ASSURANCE`) powered 100% by backend REST APIs.
- 🔄 **Multi-Dialect SQL Translation**: Automated transformation between SQL dialects (e.g. Teradata / Oracle PL/SQL to BigQuery / Snowflake) using dialect-aware LLM translation.
- 🎯 **5-Stage Equivalence Validation Engine**: Multi-layer deterministic sandbox execution comparing output schemas, row sets, aggregates, business rules, and edge cases.
- 🩺 **AI Discrepancy Diagnosis & Repair**: Agentic classification of semantic discrepancies (e.g. boundary condition operators) and automated AST patch synthesis.
- 📊 **Assurance Scoring & Quality Gates**: Quantitative 0-100 score renormalized over applicable components and 11 deterministic hard quality gates.
- 🏎️ **In-Memory High-Speed Execution**: Powered by embedded **DuckDB** sandbox for rapid local validation without touching production databases.
- 📈 **Benchmark Suite**: Standardized test cases and metrics for evaluating translation accuracy, latency, and drift.

---

## Directory Structure

```
migra-q/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
│
├── backend/                  # FastAPI backend server
│   ├── main.py               # API Application Entrypoint
│   ├── api/                  # REST Endpoint Handlers (migrations, validation, repairs, reports)
│   ├── core/                 # App Settings, Logging, Pydantic Models, Exceptions
│   ├── analyzer/             # SQLGlot Parser, AST Normalizer, AST Diff Engine, Rule Extractor
│   ├── translator/           # SQL Dialect Translator, Prompt Templates, Schemas
│   ├── execution/            # DuckDB Sandbox Execution Engine & Database Adapters
│   ├── validation/           # 5-Stage Validation Orchestrator (Schema, Rows, Aggregates, Rules, Edge Cases)
│   ├── diagnosis/            # Mismatch Classifier & Root Cause Analyzer
│   ├── repair/               # Automated SQL Repair Agent & AST Patcher
│   ├── assurance/            # Assurance Scoring Engine, Quality Gates & Reports
│   ├── benchmark/            # Benchmark Runner, Metrics & Case Studies
│   └── storage/              # SQLite Database Session & Repository Layer
│
├── frontend/                 # React + TypeScript Frontend UI
│   ├── src/
│   │   ├── components/       # Reusable UI Components (SQL Diff Viewer, Scorecard, Repair Studio)
│   │   ├── pages/            # Dashboard, Migration Setup, Validation Details, Benchmarks
│   │   ├── api/              # Axios API Client
│   │   ├── types/            # TypeScript Interfaces
│   │   └── hooks/            # Custom React Hooks
│   └── package.json
│
├── datasets/                 # Test Data, Schemas, Synthetic Generators & Fixtures
├── docs/                     # Technical Docs (Architecture, Methodology, Security, Benchmarks)
└── tests/                    # Unit, Integration & Benchmark Test Suites
```

---

## Quickstart

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ (for frontend)
- Docker & Docker Compose (optional)

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
FastAPI Interactive API Docs will be available at `http://localhost:8000/docs`.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend UI will be running at `http://localhost:5173`.

### 4. Running with Docker Compose
```bash
docker-compose up --build
```

---

## Testing

Run unit & integration tests:
```bash
pytest tests/unit tests/integration -v
```

Run benchmark evaluation:
```bash
python -m backend.benchmark.runner
```

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
