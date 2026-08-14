import React, { useState, useEffect } from 'react';
import AssuranceGauge from '../components/AssuranceGauge';
import { runValidation, getScorecard, triggerRepair } from '../api/client';

export default function ValidationPage({ migrationId }) {
  const [loading, setLoading] = useState(false);
  const [valResult, setValResult] = useState(null);
  const [scorecard, setScorecard] = useState(null);
  const [repairedSQL, setRepairedSQL] = useState('');

  const execute = async () => {
    if (!migrationId) return;
    setLoading(true);
    try {
      const res = await runValidation(migrationId);
      setValResult(res);
      const sc = await getScorecard(migrationId);
      setScorecard(sc);
    } catch (err) {
      alert('Validation error: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRepair = async () => {
    try {
      const patch = await triggerRepair(migrationId);
      setRepairedSQL(patch.repaired_target_sql);
      execute();
    } catch (err) {
      alert('Repair failed: ' + err.message);
    }
  };

  useEffect(() => {
    if (migrationId) execute();
  }, [migrationId]);

  return (
    <div className="container">
      <h1 style={{ fontSize: '1.75rem', marginBottom: '1.5rem' }}>Equivalence Validation & Assurance</h1>
      {!migrationId && <p style={{ color: '#9ca3af' }}>Please submit a migration query on the Dashboard first.</p>}

      {loading && <p>Running 5-stage validation pipeline on DuckDB sandbox...</p>}

      {scorecard && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '1.5rem' }}>
          <AssuranceGauge score={scorecard.assurance_score} passed={scorecard.gate_passed} />
          <div className="card">
            <h3>Pipeline Stages</h3>
            <ul style={{ listStyle: 'none', marginTop: '1rem', lineHeight: '2' }}>
              <li>🔹 Schema Check: <strong>{valResult?.schema_check?.passed ? 'Passed' : 'Failed'}</strong></li>
              <li>🔹 Row-Level Equivalence: <strong>{valResult?.row_check?.passed ? 'Passed' : 'Failed'}</strong> ({valResult?.row_check?.matched_row_count} rows matched)</li>
              <li>🔹 Aggregate Invariants: <strong>{valResult?.aggregate_check?.passed ? 'Passed' : 'Failed'}</strong></li>
              <li>🔹 Edge Cases (Null/Precision): <strong>{valResult?.edge_cases_check?.null_handling_passed ? 'Passed' : 'Failed'}</strong></li>
            </ul>

            {!scorecard.gate_passed && (
              <button onClick={handleRepair} className="btn" style={{ marginTop: '1.5rem', background: '#f59e0b' }}>
                Synthesize AI Repair Patch
              </button>
            )}

            {repairedSQL && (
              <div style={{ marginTop: '1rem', background: '#0b0f19', padding: '1rem', borderRadius: '6px' }}>
                <div style={{ color: '#10b981', fontWeight: 'bold' }}>Repaired SQL Patch:</div>
                <pre>{repairedSQL}</pre>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
