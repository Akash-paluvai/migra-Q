import React, { useState } from 'react';
import SQLDiffViewer from '../components/SQLDiffViewer';
import { submitMigration, runValidation } from '../api/client';

export default function Dashboard({ onRunValidation }) {
  const [sourceDialect, setSourceDialect] = useState('oracle');
  const [targetDialect, setTargetDialect] = useState('postgres');
  const [sourceSQL, setSourceSQL] = useState('SELECT id, NVL(amount, 0) AS amount FROM transactions');
  const [targetSQL, setTargetSQL] = useState('');
  const [loading, setLoading] = useState(false);
  const [migrationId, setMigrationId] = useState('');

  const handleTranslate = async () => {
    setLoading(true);
    try {
      const res = await submitMigration({
        source_dialect: sourceDialect,
        target_dialect: targetDialect,
        source_sql: sourceSQL,
      });
      setTargetSQL(res.target_sql);
      setMigrationId(res.migration_id);
    } catch (err) {
      alert('Translation failed: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h1 style={{ fontSize: '1.75rem', marginBottom: '1.5rem' }}>SQL Migration Setup</h1>
      <div className="card">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#9ca3af' }}>Source Dialect</label>
            <select value={sourceDialect} onChange={(e) => setSourceDialect(e.target.value)} style={{ width: '100%', padding: '0.5rem', background: '#0b0f19', border: '1px solid #374151', color: '#fff', borderRadius: '6px' }}>
              <option value="oracle">Oracle PL/SQL</option>
              <option value="postgres">PostgreSQL</option>
              <option value="snowflake">Snowflake</option>
              <option value="bigquery">Google BigQuery</option>
              <option value="mysql">MySQL</option>
              <option value="sqlite">SQLite</option>
            </select>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#9ca3af' }}>Target Dialect</label>
            <select value={targetDialect} onChange={(e) => setTargetDialect(e.target.value)} style={{ width: '100%', padding: '0.5rem', background: '#0b0f19', border: '1px solid #374151', color: '#fff', borderRadius: '6px' }}>
              <option value="postgres">PostgreSQL</option>
              <option value="bigquery">Google BigQuery</option>
              <option value="snowflake">Snowflake</option>
              <option value="oracle">Oracle PL/SQL</option>
              <option value="duckdb">DuckDB</option>
            </select>
          </div>
        </div>

        <button onClick={handleTranslate} className="btn" disabled={loading}>
          {loading ? 'Translating AST...' : 'Translate SQL'}
        </button>

        {targetSQL && (
          <div style={{ marginTop: '1.5rem' }}>
            <SQLDiffViewer sourceSQL={sourceSQL} targetSQL={targetSQL} sourceDialect={sourceDialect} targetDialect={targetDialect} />
            <button
              onClick={() => onRunValidation(migrationId)}
              className="btn"
              style={{ marginTop: '1rem', background: '#10b981' }}
            >
              Run 5-Stage Validation Pipeline
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
