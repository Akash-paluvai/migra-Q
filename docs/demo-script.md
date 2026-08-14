# Migra-Q Interactive Demo Script

1. **Start Backend Server**:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```
2. **Start Frontend App**:
   ```bash
   cd frontend && npm run dev
   ```
3. **Open Browser** at `http://localhost:5173`.
4. **Step 1: Translate Query**: Select Oracle as Source, PostgreSQL as Target. Input `SELECT id, NVL(amount, 0) FROM transactions`. Click "Translate SQL".
5. **Step 2: Validate**: Click "Run 5-Stage Validation Pipeline". Observe the Assurance Scorecard (100/100).
6. **Step 3: Trigger Repair**: Input a query with deliberate column missing and observe automatic repair patch generation.
