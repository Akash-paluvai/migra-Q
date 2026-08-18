import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Sparkles,
  FileText,
  Database,
  Search,
  Upload,
  Layers,
  CheckCircle2,
  AlertCircle,
  Table,
  Loader2,
} from 'lucide-react';
import { listDatasets, getDatasetSchema } from '../api/datasets';
import { runMigration } from '../api/migrations';
import { DatasetSummary, DatasetTableSummary } from '../types/dataset';
import { DatasetExplorer } from '../components/DatasetExplorer';
import { UploadDatasetDialog } from '../components/UploadDatasetDialog';

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
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDatasetId, setSelectedDatasetId] = useState('');
  const [selectedSchema, setSelectedSchema] = useState<DatasetTableSummary[]>([]);
  
  const [sourceDialect, setSourceDialect] = useState('teradata');
  const [targetDialect, setTargetDialect] = useState('bigquery');
  const [sql, setSql] = useState('');
  
  const [explorerOpen, setExplorerOpen] = useState(false);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load datasets on mount
  useEffect(() => {
    fetchDatasets();
  }, []);

  // Fetch table schemas whenever selected dataset changes
  useEffect(() => {
    if (!selectedDatasetId) return;
    getDatasetSchema(selectedDatasetId)
      .then((schema) => setSelectedSchema(schema))
      .catch(() => setSelectedSchema([]));
  }, [selectedDatasetId]);

  const fetchDatasets = async () => {
    try {
      const data = await listDatasets();
      setDatasets(data);
    } catch {
      // Fallback
    }
  };

  const filteredDatasets = datasets.filter(
    (d) =>
      d.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.dataset_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      d.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const selectedDataset = datasets.find((d) => d.dataset_id === selectedDatasetId);

  const handleLoadFlagship = () => {
    setSourceDialect('teradata');
    setTargetDialect('bigquery');
    setSelectedDatasetId('customer_risk');
    setSql(FLAGSHIP_SQL);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sql.trim()) {
      setError('Please provide source SQL logic.');
      return;
    }
    if (!selectedDatasetId) {
      setError('Please select a dataset.');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      const record = await runMigration({
        source_sql: sql,
        source_dialect: sourceDialect,
        target_dialect: targetDialect,
        dataset_id: selectedDatasetId,
      });
      navigate(`/migrations/${record.migration_id}`);
    } catch (err: any) {
      const detail = err.response?.data?.detail || err.message || 'Failed to execute migration workflow.';
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '1100px', margin: '0 auto' }}>
      <div style={{ marginBottom: '24px' }}>
        <h1 className="page-title">NEW MIGRATION WORKSPACE</h1>
        <p className="page-subtitle">
          Select target dataset, inspect schema tables, choose dialects, and run end-to-end migration pipeline.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Section 1: Dynamic Dataset Workbench */}
        <div className="card-panel" style={{ marginBottom: '24px' }}>
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Database size={18} color="#10B981" /> 1. SELECT DATA ENVIRONMENT
            </h3>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button
                type="button"
                onClick={() => setUploadDialogOpen(true)}
                className="btn-secondary"
                style={{ fontSize: '13px', padding: '6px 12px' }}
              >
                <Upload size={14} color="#10B981" /> + Upload Dataset
              </button>
              {selectedDatasetId && (
                <button
                  type="button"
                  onClick={() => setExplorerOpen(true)}
                  className="btn-secondary"
                  style={{ fontSize: '13px', padding: '6px 12px' }}
                >
                  <Layers size={14} color="#3B82F6" /> Explore Data & Schema
                </button>
              )}
            </div>
          </div>

          {/* Search bar */}
          <div style={{ position: 'relative', marginBottom: '16px' }}>
            <Search
              size={16}
              color="#64748B"
              style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }}
            />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search datasets by name, ID, or tag..."
              style={{
                width: '100%',
                padding: '10px 12px 10px 36px',
                borderRadius: '8px',
                border: '1px solid #CBD5E1',
                fontSize: '14px',
              }}
            />
          </div>

          {/* Dataset Cards Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: '12px',
              maxHeight: '260px',
              overflowY: 'auto',
              padding: '4px',
            }}
          >
            {filteredDatasets.map((d) => {
              const isSelected = d.dataset_id === selectedDatasetId;
              return (
                <div
                  key={d.dataset_id}
                  onClick={() => setSelectedDatasetId(d.dataset_id)}
                  style={{
                    padding: '14px',
                    borderRadius: '10px',
                    border: isSelected ? '2px solid #10B981' : '1px solid #E2E8F0',
                    backgroundColor: isSelected ? '#F0FDF4' : '#FFFFFF',
                    cursor: 'pointer',
                    transition: 'all 0.15s ease',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontWeight: 600, fontSize: '14px', color: '#0F172A' }}>{d.display_name}</span>
                    {isSelected && <CheckCircle2 size={16} color="#10B981" />}
                  </div>
                  <p style={{ fontSize: '12px', color: '#64748B', margin: '4px 0 8px 0', lineHeight: 1.3 }}>{d.description}</p>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '11px', fontFamily: 'var(--font-mono)', color: '#475569' }}>
                    <span>{d.row_count_total.toLocaleString()} rows</span>
                    <span>•</span>
                    <span>{d.table_count} tables</span>
                    <span>•</span>
                    <span style={{ color: '#059669' }}>{d.dataset_hash.slice(0, 8)}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {selectedDataset && (
            <div
              style={{
                marginTop: '16px',
                padding: '12px',
                backgroundColor: '#F8FAFC',
                borderRadius: '8px',
                border: '1px solid #E2E8F0',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                fontSize: '13px',
              }}
            >
              <div>
                <span style={{ fontWeight: 600, color: '#0F172A' }}>Selected Environment: </span>
                <span style={{ fontFamily: 'var(--font-mono)', color: '#059669' }}>{selectedDataset.display_name}</span>
                <span style={{ color: '#64748B', marginLeft: '8px' }}>({selectedDataset.dataset_id})</span>
              </div>
              <button
                type="button"
                onClick={() => setExplorerOpen(true)}
                style={{ background: 'none', border: 'none', color: 'var(--accent-primary)', fontWeight: 600, cursor: 'pointer', fontSize: '13px' }}
              >
                Inspect Schema & Preview Data →
              </button>
            </div>
          )}
        </div>

        {/* Section 2: Dialect Configuration */}
        <div className="card-panel" style={{ marginBottom: '24px' }}>
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3>2. DIALECT SPECIFICATION</h3>
            <button
              type="button"
              onClick={handleLoadFlagship}
              className="btn-secondary"
              style={{ fontSize: '13px', padding: '6px 12px' }}
            >
              <FileText size={14} color="var(--accent-primary)" /> Load Flagship Benchmark Example
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
                <option value="teradata">Teradata SQL</option>
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
                <option value="snowflake">Snowflake SQL</option>
              </select>
            </div>
          </div>
        </div>

        {/* Section 3: SQL Editor & Tables Helper */}
        <div className="card-panel">
          <div className="card-header" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <h3>3. SOURCE SQL QUERY LOGIC</h3>
            {selectedSchema.length > 0 && (
              <div style={{ fontSize: '12px', color: '#64748B', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Table size={14} color="#059669" />
                <span>Available Tables: </span>
                <span style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#0F172A' }}>
                  {selectedSchema.map((t) => t.table_name).join(', ')}
                </span>
              </div>
            )}
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
            placeholder="Paste or enter source SQL...\n\nOr click 'Load Flagship Benchmark Example' above to try the built-in demo."
          />

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: '20px' }}>
            <div style={{ fontSize: '13px', color: '#64748B' }}>
              Triggers Phase 1 Analyzer → Phase 6 Translator → Phase 3 Execution → Phase 4–9 Quality Gates.
            </div>

            <button type="submit" disabled={submitting} className="btn-primary" style={{ padding: '12px 24px', fontSize: '15px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              {submitting ? (
                <Loader2 size={18} className="animate-spin" />
              ) : (
                <Sparkles size={18} />
              )}
              {submitting ? 'Executing Pipeline...' : 'Analyze & Migrate Logic'}
            </button>
          </div>

          {error && (
            <div
              style={{
                marginTop: '16px',
                padding: '12px',
                backgroundColor: '#FEF2F2',
                border: '1px solid #FCA5A5',
                borderRadius: '8px',
                color: '#991B1B',
                fontSize: '13px',
                fontFamily: 'var(--font-mono)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <AlertCircle size={16} />
              <span>{error}</span>
            </div>
          )}
        </div>
      </form>

      {/* Dataset Explorer Drawer */}
      <DatasetExplorer
        datasetId={selectedDatasetId}
        isOpen={explorerOpen}
        onClose={() => setExplorerOpen(false)}
        onSelectDataset={(id) => setSelectedDatasetId(id)}
      />

      {/* Upload Dataset Dialog */}
      <UploadDatasetDialog
        isOpen={uploadDialogOpen}
        onClose={() => setUploadDialogOpen(false)}
        onSuccess={(detail) => {
          fetchDatasets();
          setSelectedDatasetId(detail.dataset_id);
        }}
      />
    </div>
  );
};
