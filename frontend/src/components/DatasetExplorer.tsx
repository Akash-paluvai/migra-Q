import React, { useEffect, useState } from 'react';
import { Database, FileSpreadsheet, Hash, Layers, Table, X } from 'lucide-react';
import { getDataset, getDatasetPreview } from '../api/datasets';
import { DatasetDetail, DatasetPreviewResponse } from '../types/dataset';
import { LoadingState } from './LoadingState';
import { ErrorState } from './ErrorState';

interface DatasetExplorerProps {
  datasetId: string;
  isOpen: boolean;
  onClose: () => void;
  onSelectDataset?: (datasetId: string) => void;
}

export const DatasetExplorer: React.FC<DatasetExplorerProps> = ({
  datasetId,
  isOpen,
  onClose,
  onSelectDataset,
}) => {
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [preview, setPreview] = useState<DatasetPreviewResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [previewLoading, setPreviewLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isOpen || !datasetId) return;

    let isMounted = true;
    setLoading(true);
    setError(null);

    getDataset(datasetId)
      .then((data) => {
        if (isMounted) {
          setDetail(data);
          const defaultTable = data.table_summaries[0]?.table_name || '';
          setSelectedTable(defaultTable);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (isMounted) {
          setError(err.message || 'Failed to load dataset details');
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [datasetId, isOpen]);

  useEffect(() => {
    if (!isOpen || !datasetId || !selectedTable) return;

    let isMounted = true;
    setPreviewLoading(true);

    getDatasetPreview(datasetId, selectedTable, 100)
      .then((data) => {
        if (isMounted) {
          setPreview(data);
          setPreviewLoading(false);
        }
      })
      .catch(() => {
        if (isMounted) {
          setPreviewLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [datasetId, selectedTable, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="drawer-overlay">
      <div className="drawer-content">
        {/* Drawer Header */}
        <div className="drawer-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div className="icon-box">
              <Database size={20} />
            </div>
            <div>
              <h2 style={{ fontSize: '20px', fontWeight: 600, margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                {detail?.display_name || datasetId}
                {detail?.is_builtin && (
                  <span className="status-badge status-pass">BUILT-IN</span>
                )}
                {detail?.is_upload && (
                  <span className="status-badge status-info">UPLOADED</span>
                )}
              </h2>
              <p style={{ fontSize: '13px', color: 'var(--text-secondary)', margin: '4px 0 0 0' }}>
                {detail?.description}
              </p>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            {onSelectDataset && (
              <button
                onClick={() => {
                  onSelectDataset(datasetId);
                  onClose();
                }}
                className="btn-primary"
              >
                Use This Dataset
              </button>
            )}
            <button onClick={onClose} className="btn-icon-only">
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="drawer-body">
          {loading ? (
            <LoadingState message="Loading dataset metadata and schema..." />
          ) : error ? (
            <ErrorState title="Error Loading Dataset" message={error} />
          ) : detail ? (
            <>
              {/* Quick Stats Bar */}
              <div className="stats-grid">
                <div className="stat-item">
                  <span className="stat-label">
                    <Layers size={14} /> Total Rows
                  </span>
                  <span className="stat-value">{detail.row_count_total.toLocaleString()}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">
                    <Table size={14} /> Tables
                  </span>
                  <span className="stat-value">{detail.table_count}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">
                    <Hash size={14} /> Content Hash
                  </span>
                  <span className="stat-value" style={{ fontSize: '14px', color: 'var(--accent-primary)', marginTop: '8px' }}>
                    {detail.dataset_hash}
                  </span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">
                    <FileSpreadsheet size={14} /> Profile
                  </span>
                  <span className="stat-value" style={{ fontSize: '14px', textTransform: 'uppercase', marginTop: '8px' }}>
                    {detail.profile}
                  </span>
                </div>
              </div>

              {/* Table Selector Tabs */}
              <div style={{ marginBottom: '24px' }}>
                <div className="section-title">Dataset Tables</div>
                <div className="table-tabs">
                  {detail.table_summaries.map((t) => {
                    const active = t.table_name === selectedTable;
                    return (
                      <button
                        key={t.table_name}
                        onClick={() => setSelectedTable(t.table_name)}
                        className={`table-tab ${active ? 'active' : ''}`}
                      >
                        <Table size={16} />
                        <span>{t.table_name}</span>
                        <span className="table-tab-badge">
                          {t.row_count.toLocaleString()} rows
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Table Schema Specification */}
              {selectedTable && (
                <div style={{ marginBottom: '32px' }}>
                  <div className="section-title">
                    Schema Specification: <span style={{ color: 'var(--accent-primary)', textTransform: 'none', marginLeft: '8px', fontFamily: 'var(--font-mono)' }}>{selectedTable}</span>
                  </div>
                  <div className="enterprise-table-container">
                    <table className="enterprise-table">
                      <thead>
                        <tr>
                          <th style={{ width: '60px' }}>#</th>
                          <th>Column Name</th>
                          <th>Data Type</th>
                          <th>Nullable</th>
                        </tr>
                      </thead>
                      <tbody>
                        {detail.table_summaries
                          .find((t) => t.table_name === selectedTable)
                          ?.columns.map((col) => (
                            <tr key={col.name}>
                              <td style={{ color: 'var(--text-muted)' }}>{col.ordinal_position}</td>
                              <td style={{ fontWeight: 500 }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                  {col.name}
                                  {col.primary_key && (
                                    <span className="table-tab-badge" style={{ backgroundColor: 'var(--status-warn-bg)', color: 'var(--status-warn-text)' }}>PK</span>
                                  )}
                                </div>
                              </td>
                              <td style={{ color: 'var(--accent-primary)', fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
                                {col.data_type}
                              </td>
                              <td style={{ color: 'var(--text-secondary)' }}>
                                {col.nullable ? 'YES' : 'NO'}
                              </td>
                            </tr>
                          ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Live Sample Row Preview */}
              <div>
                <div className="section-title">
                  <span>Sample Rows Preview (Max 100)</span>
                  {preview && (
                    <span style={{ fontSize: '12px', textTransform: 'none', fontWeight: 500 }}>
                      Showing {preview.returned_rows} of {preview.total_rows.toLocaleString()} rows
                    </span>
                  )}
                </div>

                {previewLoading ? (
                  <div style={{ padding: '40px 0' }}>
                    <LoadingState message="Fetching live sample rows..." />
                  </div>
                ) : preview && preview.rows.length > 0 ? (
                  <div className="enterprise-table-container" style={{ maxHeight: '400px', overflowY: 'auto' }}>
                    <table className="enterprise-table" style={{ whiteSpace: 'nowrap' }}>
                      <thead style={{ position: 'sticky', top: 0, zIndex: 10 }}>
                        <tr>
                          {preview.columns.map((col) => (
                            <th key={col.name}>{col.name}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {preview.rows.map((row, rIdx) => (
                          <tr key={rIdx}>
                            {preview.columns.map((col) => {
                              const val = row[col.name];
                              return (
                                <td key={col.name} style={{ fontFamily: 'var(--font-mono)', fontSize: '13px' }}>
                                  {val === null ? (
                                    <span style={{ color: 'var(--text-muted)', fontStyle: 'italic' }}>null</span>
                                  ) : typeof val === 'object' ? (
                                    JSON.stringify(val)
                                  ) : (
                                    String(val)
                                  )}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div className="card-panel" style={{ textAlign: 'center', padding: '32px' }}>
                    <span style={{ color: 'var(--text-muted)' }}>No sample rows available for this table.</span>
                  </div>
                )}
              </div>
            </>
          ) : null}
        </div>
      </div>
    </div>
  );
};
