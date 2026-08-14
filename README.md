# Migra-Q: Automated SQL & Database Migration Assurance Platform

![Migra-Q Architecture](https://img.shields.io/badge/Status-Active-brightgreen) ![Python](https://img.shields.io/badge/Python-3.11%2B-blue) ![DuckDB](https://img.shields.io/badge/DuckDB-1.0%2B-yellow) ![License](https://img.shields.io/badge/License-MIT-green)

**Migra-Q** is an end-to-end automated platform for SQL dialect translation, multi-stage semantic equivalence validation, mismatch diagnosis, automated patch repair, and assurance scoring. It ensures zero data loss, zero semantic drift, and high-confidence migration across heterogeneous database engines (Oracle, PostgreSQL, Snowflake, BigQuery, MySQL, SQLite, DuckDB).

---

## Key Features

- 🔄 **Multi-Dialect SQL Translation**: Automated transformation between SQL dialects (e.g. Oracle PL/SQL to PostgreSQL, Snowflake to BigQuery) using AST parsing (`sqlglot`) and LLM-assisted fallback translation.
- 🎯 **5-Stage Equivalence Validation Engine**:
  1. **Schema Integrity**: Structural verification of tables, column types, nullability, primary/foreign key constraints.
  2. **Row-Level Equivalence**: Cryptographic row-hashing and record matching.
  3. **Aggregate Invariants**: Multi-dimensional verification of SUM, COUNT, AVG, MIN, MAX, and GROUP BY grouping sets.
  4. **Business Rule Verification**: Custom constraint assertions across source and target queries.
  5. **Edge-Case Stress Testing**: Null semantics, collation, floating-point precision, and timezone timestamp validation.
- 🩺 **Diagnostic & Root Cause Engine**: Automated classification of mismatch causes (Type Mismatch, Collation/Ordering, Null Propagation, Window Function behavior, Join semantics).
- 🛠️ **Automated Repair Agent**: Agentic SQL repair engine synthesizing AST patches and optimized SQL replacements.
- 📊 **Assurance Scoring & Quality Gates**: Quantitative 0-100 confidence scorecard for CI/CD deployment approval gates.
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
