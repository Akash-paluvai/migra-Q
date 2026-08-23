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
        <p style={{ color: '#94A3B8', fontSize: '14px', maxWidth: '500px', margin: '0 auto', marginBottom: '24px' }}>
          Phase 4 Multi-Layer Semantic Validation was NOT RUN because upstream translation or execution did not complete successfully.
        </p>

        {report.execution_summary && (
          <div style={{ textAlign: 'left', backgroundColor: '#FEF2F2', padding: '16px', borderRadius: '8px', border: '1px solid #FECACA' }}>
            <h4 style={{ color: '#991B1B', margin: '0 0 12px 0' }}>Execution Status</h4>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '12px' }}>
              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: report.execution_summary.source_status === 'SUCCESS' ? '#065F46' : '#7F1D1D', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Source ({report.source_dialect || 'Source'}) Execution
                </div>
                <div style={{ fontSize: '13px', color: report.execution_summary.source_status === 'SUCCESS' ? '#047857' : '#991B1B', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {report.execution_summary.source_status === 'SUCCESS' ? (
                    <><span>✅</span> SUCCESS</>
                  ) : (
                    <><span>❌</span> FAILED</>
                  )}
                </div>
                {report.execution_summary.source_status !== 'SUCCESS' && (
                   <div style={{ fontSize: '11px', color: '#991B1B', fontFamily: 'monospace', whiteSpace: 'pre-wrap', marginTop: '6px', background: '#f8717122', padding: '4px', borderRadius: '4px' }}>
                     {report.execution_summary.source_status}
                   </div>
                )}
              </div>

              <div>
                <div style={{ fontSize: '12px', fontWeight: 700, color: report.execution_summary.target_status === 'SUCCESS' ? '#065F46' : '#7F1D1D', textTransform: 'uppercase', marginBottom: '4px' }}>
                  Target ({report.target_dialect || 'Target'}) Execution
                </div>
                <div style={{ fontSize: '13px', color: report.execution_summary.target_status === 'SUCCESS' ? '#047857' : '#991B1B', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {report.execution_summary.target_status === 'SUCCESS' ? (
                    <><span>✅</span> SUCCESS</>
                  ) : (
                    <><span>❌</span> FAILED</>
                  )}
                </div>
                {report.execution_summary.target_status !== 'SUCCESS' && (
                   <div style={{ fontSize: '11px', color: '#991B1B', fontFamily: 'monospace', whiteSpace: 'pre-wrap', marginTop: '6px', background: '#f8717122', padding: '4px', borderRadius: '4px' }}>
                     {report.execution_summary.target_status}
                   </div>
                )}
              </div>
            </div>
            
            {(report.execution_summary.source_status !== 'SUCCESS' || report.execution_summary.target_status !== 'SUCCESS') && (
              <div style={{ fontSize: '13px', color: '#991B1B', marginTop: '8px', borderTop: '1px solid #FECACA', paddingTop: '12px' }}>
                <strong>Semantic Validation ⏭ NOT RUN.</strong> There is no comparable output pair due to execution failure.
              </div>
            )}
          </div>
        )}
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
