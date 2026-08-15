import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, FileText } from 'lucide-react';
import { runMigration } from '../api/migrations';

const FLAGSHIP_SQL = `
SELECT
    c.customer_id,
    c.customer_segment,
    SUM(t.amount) AS total_amount,
    CASE
        WHEN t.amount > 500
        THEN 'HIGH_RISK'
        ELSE 'NORMAL'
    END AS risk_class
FROM transactions AS t
INNER JOIN customers AS c
    ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;
`.trim();

export const NewMigrationPage: React.FC = () => {
  const navigate = useNavigate();
  const [sourceDialect, setSourceDialect] = useState('teradata');
  const [targetDialect, setTargetDialect] = useState('bigquery');
  const [datasetId, setDatasetId] = useState('customer_risk');
  const [sql, setSql] = useState(FLAGSHIP_SQL);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLoadFlagship = () => {
    setSourceDialect('teradata');
    setTargetDialect('bigquery');
    setDatasetId('customer_risk');
    setSql(FLAGSHIP_SQL);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sql.trim()) {
      setError('Please provide source SQL logic.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const record = await runMigration({
        source_sql: sql,
        source_dialect: sourceDialect,
        target_dialect: targetDialect,
        dataset_id: datasetId,
      });
      navigate(`/migrations/${record.migration_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to execute migration workflow.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 className="page-title">NEW MIGRATION WORKSPACE</h1>
        <p className="page-subtitle">
          Configure source/target dialects, load dataset schema, and execute automated migration pipeline.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Source Configuration Panel */}
        <div className="card-panel">
          <div className="card-header">
            <h3>SOURCE & TARGET CONFIGURATION</h3>
            <button
              type="button"
              onClick={handleLoadFlagship}
              className="btn-secondary"
              style={{ fontSize: '13px', padding: '6px 12px' }}
            >
              <FileText size={14} color="#2563EB" /> Load Flagship Example
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px' }}>
            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, color: '#334155', display: 'block', marginBottom: '6px' }}>
                Source Dialect:
              </label>
              <select
                value={sourceDialect}
                onChange={(e) => setSourceDialect(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '14px' }}
              >
                <option value="teradata">Teradata Baseline</option>
                <option value="oracle">Oracle PL/SQL</option>
                <option value="netezza">Netezza SQL</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, color: '#334155', display: 'block', marginBottom: '6px' }}>
                Target Dialect:
              </label>
              <select
                value={targetDialect}
                onChange={(e) => setTargetDialect(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '14px' }}
              >
                <option value="bigquery">Google BigQuery</option>
                <option value="snowflake">Snowflake</option>
              </select>
            </div>

            <div>
              <label style={{ fontSize: '13px', fontWeight: 600, color: '#334155', display: 'block', marginBottom: '6px' }}>
                Dataset Profile:
              </label>
              <select
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
                style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '14px' }}
              >
                <option value="customer_risk">customer_risk (Benchmark)</option>
              </select>
            </div>
          </div>
        </div>

        {/* SQL Editor Panel */}
        <div className="card-panel">
          <div className="card-header">
            <h3>LEGACY SOURCE SQL LOGIC</h3>
          </div>

          <textarea
            value={sql}
            onChange={(e) => setSql(e.target.value)}
            rows={10}
            style={{
              width: '100%',
              backgroundColor: '#0F172A',
              color: '#F8FAFC',
              fontFamily: 'var(--font-mono)',
              fontSize: '14px',
              padding: '16px',
              borderRadius: '8px',
              border: '1px solid #334155',
              outline: 'none',
              lineHeight: 1.5,
              resize: 'vertical',
            }}
            placeholder="Paste Teradata SQL source query..."
          />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '20px' }}>
            <div style={{ fontSize: '13px', color: '#64748B' }}>
              Submitting triggers Phase 1 Analysis → Phase 6 Translation → Phase 3 Execution → Phase 4–9 Re-Validation.
            </div>

            <button type="submit" disabled={submitting} className="btn-primary" style={{ padding: '12px 24px', fontSize: '15px' }}>
              <Sparkles size={18} />
              {submitting ? 'Executing Workflow...' : 'Analyze & Translate'}
            </button>
          </div>

          {error && (
            <div style={{ marginTop: '16px', color: '#DC2626', fontSize: '14px', fontWeight: 500 }}>
              ⚠ {error}
            </div>
          )}
        </div>
      </form>
    </div>
  );
};
