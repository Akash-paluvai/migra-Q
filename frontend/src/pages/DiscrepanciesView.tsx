import React, { useEffect, useState } from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { StatusBadge } from '../components/StatusBadge';
import { fetchApi } from '../api/client';

interface DiscrepanciesViewProps {
  report: MigrationAssuranceReport;
}

interface CanonicalDiscrepancy {
  discrepancy_id: string;
  validation_id: string;
  category: string;
  severity: string;
  classification_confidence: number;
  classification_reason: string;
  source_expression: string | null;
  target_expression: string | null;
  affected_output_columns: string[];
  affected_row_count: number;
  total_output_rows: number;
  affected_percentage: number;
  status: string;
  evidence: Array<{
    type: string;
    column: string | null;
    source_result: unknown;
    target_result: unknown;
    row_key: Record<string, unknown> | null;
    detail: string;
  }>;
}

interface CanonicalDiscrepancyData {
  migration_id: string;
  diagnosis_id: string | null;
  discrepancy_count: number;
  discrepancies: CanonicalDiscrepancy[];
  status: string;
}

export const DiscrepanciesView: React.FC<DiscrepanciesViewProps> = ({ report }) => {
  const [discData, setDiscData] = useState<CanonicalDiscrepancyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadCanonicalDiscrepancies() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchApi<CanonicalDiscrepancyData>(
          `/api/v1/migrations/${report.migration_id}/discrepancies`
        );
        if (isMounted) {
          setDiscData(data);
          setLoading(false);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err?.message || 'Failed to fetch discrepancy data.');
          setLoading(false);
        }
      }
    }
    loadCanonicalDiscrepancies();
    return () => { isMounted = false; };
  }, [report.migration_id]);

  if (loading) {
    return (
      <div className="card-panel" style={{ padding: '32px', textAlign: 'center', color: '#64748B' }}>
        Loading canonical Phase 5 discrepancy data...
      </div>
    );
  }

  if (error) {
    return (
      <div className="card-panel" style={{ backgroundColor: '#FEF2F2', border: '1px solid #FECACA', padding: '24px' }}>
        <h3 style={{ color: '#991B1B', marginBottom: '8px' }}>Discrepancy Data Error</h3>
        <p style={{ color: '#B91C1C', fontSize: '13px' }}>{error}</p>
      </div>
    );
  }

  const hasDiscrepancy = (discData?.discrepancy_count || 0) > 0;

  return (
    <div>
      {/* Header */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3>SEMANTIC DISCREPANCIES</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Diagnosis ID: {discData?.diagnosis_id || 'N/A'}
            </p>
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: hasDiscrepancy ? '#B45309' : '#15803D' }}>
            {discData?.discrepancy_count || 0} Classified Discrepanc{discData?.discrepancy_count === 1 ? 'y' : 'ies'}
          </div>
        </div>
      </div>

      {hasDiscrepancy ? (
        <>
          {/* Discrepancies Table */}
          <div className="enterprise-table-container" style={{ marginBottom: '24px' }}>
            <table className="enterprise-table">
              <thead>
                <tr>
                  <th>Discrepancy ID</th>
                  <th>Category</th>
                  <th>Severity</th>
                  <th>Confidence</th>
                  <th>Affected Records</th>
                  <th>Affected Columns</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {discData!.discrepancies.map((disc) => (
                  <tr key={disc.discrepancy_id}>
                    <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>{disc.discrepancy_id}</td>
                    <td style={{ fontWeight: 600 }}>{disc.category}</td>
                    <td>
                      <span
                        style={{
                          backgroundColor: disc.severity === 'CRITICAL' ? '#FEF2F2' : disc.severity === 'HIGH' ? '#FFF7ED' : '#F0FDF4',
                          color: disc.severity === 'CRITICAL' ? '#B91C1C' : disc.severity === 'HIGH' ? '#C2410C' : '#15803D',
                          padding: '2px 8px',
                          borderRadius: '4px',
                          fontSize: '12px',
                          fontWeight: 600,
                        }}
                      >
                        {disc.severity}
                      </span>
                    </td>
                    <td>{(disc.classification_confidence * 100).toFixed(0)}%</td>
                    <td style={{ fontWeight: 600 }}>{disc.affected_row_count.toLocaleString()}</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>
                      {disc.affected_output_columns.length > 0 ? disc.affected_output_columns.join(', ') : 'N/A'}
                    </td>
                    <td>
                      <StatusBadge
                        status={
                          report.verification_summary?.status === 'VERIFIED' ? 'RESOLVED' : disc.status || 'OPEN'
                        }
                      />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Per-Discrepancy Detail Panels */}
          {discData!.discrepancies.map((disc) => (
            <div className="card-panel" key={`detail-${disc.discrepancy_id}`} style={{ marginBottom: '16px' }}>
              <h3 style={{ marginBottom: '16px' }}>
                DISCREPANCY EVIDENCE DETAIL: {disc.discrepancy_id}
              </h3>

              {/* Expression Comparison (only if expressions exist) */}
              {(disc.source_expression || disc.target_expression) && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
                  <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', padding: '16px', borderRadius: '6px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#991B1B', textTransform: 'uppercase' }}>
                      SOURCE EXPRESSION
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 700, color: '#7F1D1D', marginTop: '6px' }}>
                      {disc.source_expression || '—'}
                    </div>
                  </div>

                  <div style={{ backgroundColor: '#EFF6FF', border: '1px solid #BFDBFE', padding: '16px', borderRadius: '6px' }}>
                    <div style={{ fontSize: '11px', fontWeight: 600, color: '#1E40AF', textTransform: 'uppercase' }}>
                      TARGET EXPRESSION
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 700, color: '#1E3A8A', marginTop: '6px' }}>
                      {disc.target_expression || '—'}
                    </div>
                  </div>
                </div>
              )}

              {/* Impact Metric */}
              <div style={{ backgroundColor: '#F8FAFC', padding: '16px', borderRadius: '6px', border: '1px solid #E2E8F0', marginBottom: '24px' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A' }}>
                  Impact: {disc.affected_row_count.toLocaleString()} affected records
                  ({disc.affected_percentage.toFixed(1)}% of output set)
                </div>
                <div style={{ fontSize: '12px', color: '#64748B', marginTop: '2px' }}>
                  {disc.classification_reason}
                </div>
              </div>

              {/* Evidence Items (from canonical Phase 5 data) */}
              {disc.evidence.length > 0 && (
                <>
                  <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#0F172A', marginBottom: '12px' }}>
                    OBSERVED ROW EVIDENCE ({disc.evidence.length} items)
                  </h4>
                  <div className="enterprise-table-container">
                    <table className="enterprise-table">
                      <thead>
                        <tr>
                          <th>Type</th>
                          <th>Column</th>
                          <th>Source Value</th>
                          <th>Target Value</th>
                          <th>Detail</th>
                        </tr>
                      </thead>
                      <tbody>
                        {disc.evidence.slice(0, 10).map((ev, idx) => (
                          <tr key={idx}>
                            <td style={{ fontSize: '12px', fontWeight: 600 }}>{ev.type}</td>
                            <td style={{ fontFamily: 'var(--font-mono)' }}>{ev.column || '—'}</td>
                            <td style={{ fontFamily: 'var(--font-mono)' }}>
                              {ev.source_result != null ? String(ev.source_result) : '—'}
                            </td>
                            <td style={{ fontFamily: 'var(--font-mono)' }}>
                              {ev.target_result != null ? String(ev.target_result) : '—'}
                            </td>
                            <td style={{ fontSize: '12px', color: '#64748B' }}>{ev.detail || '—'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}
            </div>
          ))}
        </>
      ) : (
        <div className="card-panel" style={{ textAlign: 'center', padding: '40px' }}>
          <h3 style={{ color: '#15803D' }}>✓ Zero Semantic Discrepancies Detected</h3>
          <p style={{ fontSize: '14px', color: '#64748B', marginTop: '4px' }}>
            Source and target executions produced 100% equivalent semantic output.
          </p>
        </div>
      )}
    </div>
  );
};
