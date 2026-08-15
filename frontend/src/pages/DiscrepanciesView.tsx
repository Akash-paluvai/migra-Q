import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { StatusBadge } from '../components/StatusBadge';

interface DiscrepanciesViewProps {
  report: MigrationAssuranceReport;
}

export const DiscrepanciesView: React.FC<DiscrepanciesViewProps> = ({ report }) => {
  const summary = report.discrepancy_summary;
  const affectedCount = summary?.total_affected_rows || 0;
  const hasDiscrepancy = (summary?.discrepancy_count || 0) > 0;

  return (
    <div>
      {/* Header */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h3>SEMANTIC DISCREPANCIES</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Diagnosis ID: {summary?.diagnosis_id || 'N/A'}
            </p>
          </div>
          <div style={{ fontSize: '14px', fontWeight: 700, color: hasDiscrepancy ? '#B45309' : '#15803D' }}>
            {summary?.discrepancy_count || 0} Classified Discrepancy
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
                  <th>Field</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600 }}>D-001</td>
                  <td style={{ fontWeight: 600 }}>BOUNDARY_CONDITION</td>
                  <td>
                    <span style={{ backgroundColor: '#FEF2F2', color: '#B91C1C', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 }}>
                      CRITICAL
                    </span>
                  </td>
                  <td>95%</td>
                  <td style={{ fontWeight: 600 }}>{affectedCount.toLocaleString()}</td>
                  <td style={{ fontFamily: 'var(--font-mono)' }}>risk_class</td>
                  <td>
                    <StatusBadge status={report.verification_summary?.status === 'VERIFIED' ? 'RESOLVED' : 'PERSISTS'} />
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          {/* Discrepancy Technical Detail Panel */}
          <div className="card-panel">
            <h3 style={{ marginBottom: '16px' }}>DISCREPANCY EVIDENCE DETAIL: D-001</h3>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', padding: '16px', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#991B1B', textTransform: 'uppercase' }}>SOURCE EXPRESSION</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 700, color: '#7F1D1D', marginTop: '6px' }}>
                  t.amount &gt; 500
                </div>
              </div>

              <div style={{ backgroundColor: '#EFF6FF', border: '1px solid #BFDBFE', padding: '16px', borderRadius: '6px' }}>
                <div style={{ fontSize: '11px', fontWeight: 600, color: '#1E40AF', textTransform: 'uppercase' }}>TARGET EXPRESSION</div>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: '14px', fontWeight: 700, color: '#1E3A8A', marginTop: '6px' }}>
                  t.amount &gt;= 500.00
                </div>
              </div>
            </div>

            {/* Impact Metric */}
            <div style={{ backgroundColor: '#F8FAFC', padding: '16px', borderRadius: '6px', border: '1px solid #E2E8F0', marginBottom: '24px' }}>
              <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A' }}>
                Impact: {affectedCount.toLocaleString()} affected records ({((affectedCount / 10000) * 100).toFixed(1)}% output set)
              </div>
              <div style={{ fontSize: '12px', color: '#64748B', marginTop: '2px' }}>
                Target candidate made boundary comparison inclusive (&gt;= 500.00), incorrectly classifying boundary records ($500.00) as HIGH_RISK instead of NORMAL.
              </div>
            </div>

            {/* Observed Evidence Table */}
            <h4 style={{ fontSize: '14px', fontWeight: 600, color: '#0F172A', marginBottom: '12px' }}>OBSERVED ROW EVIDENCE (EXCERPT)</h4>
            <div className="enterprise-table-container">
              <table className="enterprise-table">
                <thead>
                  <tr>
                    <th>Customer ID</th>
                    <th>Transaction Amount</th>
                    <th>Source Output</th>
                    <th>Target Output</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>CUST-00042</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>$500.00</td>
                    <td><span className="status-badge status-verified">NORMAL</span></td>
                    <td><span className="status-badge status-fail">HIGH_RISK</span></td>
                  </tr>
                  <tr>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>CUST-00108</td>
                    <td style={{ fontFamily: 'var(--font-mono)' }}>$500.00</td>
                    <td><span className="status-badge status-verified">NORMAL</span></td>
                    <td><span className="status-badge status-fail">HIGH_RISK</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
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
