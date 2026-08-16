import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { StatusBadge } from '../components/StatusBadge';

interface ValidationViewProps {
  report: MigrationAssuranceReport;
}

export const ValidationView: React.FC<ValidationViewProps> = ({ report }) => {
  const summary = report.validation_summary;
  const affectedCount = report.discrepancy_summary?.total_affected_rows || 0;

  if (!summary) {
    return (
      <div className="card-panel" style={{ padding: '32px', textAlign: 'center' }}>
        <h3 style={{ color: '#64748B', marginBottom: '8px' }}>Validation Not Run</h3>
        <p style={{ color: '#94A3B8', fontSize: '14px', maxWidth: '500px', margin: '0 auto' }}>
          Phase 4 Multi-Layer Semantic Validation was NOT RUN because upstream translation or execution did not complete successfully.
        </p>
      </div>
    );
  }

  return (
    <div>
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
          <div>
            <h3>MULTI-LAYER SEMANTIC VALIDATION</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Validation ID: {summary.validation_id || 'N/A'}
            </p>
          </div>
          <StatusBadge status={summary.overall_status || 'UNKNOWN'} />
        </div>

        {/* Validation Checklist */}
        <div className="enterprise-table-container">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Validator Check</th>
                <th>Status</th>
                <th>Mismatches</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {summary.checks.map((check) => (
                <tr key={check.check_name}>
                  <td style={{ fontWeight: 600 }}>{check.check_name}</td>
                  <td>
                    <StatusBadge status={check.status} />
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {check.mismatch_count > 0 ? check.mismatch_count.toLocaleString() : '0'}
                  </td>
                  <td>{(check.score * 100).toFixed(0)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Affected Record Impact Metric */}
      {affectedCount > 0 && (
        <div
          style={{
            backgroundColor: '#FFFBEB',
            border: '1px solid #FDE68A',
            borderRadius: '8px',
            padding: '24px',
          }}
        >
          <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#B45309', marginBottom: '4px' }}>
            BEHAVIORAL DRIFT IMPACT
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#92400E' }}>
            {affectedCount.toLocaleString()} Records Affected
          </div>
          <div style={{ fontSize: '14px', color: '#B45309', marginTop: '4px' }}>
            Row-level semantic mismatch detected between source and target outputs.
          </div>
        </div>
      )}
    </div>
  );
};
