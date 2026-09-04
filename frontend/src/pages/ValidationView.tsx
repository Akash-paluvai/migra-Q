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
              {/* SOURCE SIDE */}
              <div style={{ padding: '12px', backgroundColor: report.execution_summary.source_status === 'SUCCESS' ? '#F0FDF4' : '#FEF2F2', borderRadius: '6px', border: `1px solid ${report.execution_summary.source_status === 'SUCCESS' ? '#BBF7D0' : '#FECACA'}` }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '2px' }}>
                  SOURCE
                </div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#1E293B', marginBottom: '6px' }}>
                  {(report.execution_summary.source_dialect || report.translation_summary?.source_dialect || 'Source').toUpperCase()}
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', color: report.execution_summary.source_status === 'SUCCESS' ? '#047857' : '#991B1B' }}>
                  {report.execution_summary.source_status === 'SUCCESS' ? (
                    <><span>✅</span> SUCCESS</>
                  ) : report.execution_summary.source_status === 'SANDBOX_LIMITATION' ? (
                    <><span>⚠️</span> Sandbox: LIMITED</>
                  ) : (
                    <><span>❌</span> FAILED</>
                  )}
                </div>
                {report.execution_summary.source_status === 'SANDBOX_LIMITATION' && (
                  <div style={{ fontSize: '11px', color: '#92400E', fontFamily: 'monospace', marginTop: '6px', background: '#FEF3C7', padding: '6px 8px', borderRadius: '4px', lineHeight: 1.4 }}>
                    DuckDB cannot execute this {(report.execution_summary.source_dialect || 'source').toLowerCase()} query
                  </div>
                )}
                {report.execution_summary.source_status !== 'SUCCESS' && report.execution_summary.source_status !== 'SANDBOX_LIMITATION' && (
                  <div style={{ fontSize: '11px', color: '#991B1B', fontFamily: 'monospace', whiteSpace: 'pre-wrap', marginTop: '6px', background: '#f8717122', padding: '4px', borderRadius: '4px' }}>
                    {report.execution_summary.source_status}
                  </div>
                )}
              </div>

              {/* TARGET SIDE */}
              <div style={{ padding: '12px', backgroundColor: report.execution_summary.target_status === 'SUCCESS' ? '#F0FDF4' : '#FEF2F2', borderRadius: '6px', border: `1px solid ${report.execution_summary.target_status === 'SUCCESS' ? '#BBF7D0' : '#FECACA'}` }}>
                <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748B', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '2px' }}>
                  TARGET
                </div>
                <div style={{ fontSize: '14px', fontWeight: 700, color: '#1E293B', marginBottom: '6px' }}>
                  {(report.execution_summary.target_dialect || report.translation_summary?.target_dialect || 'Target').toUpperCase()}
                </div>
                <div style={{ fontSize: '13px', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', color: report.execution_summary.target_status === 'SUCCESS' ? '#047857' : '#991B1B' }}>
                  {report.execution_summary.target_status === 'SUCCESS' ? (
                    <><span>✅</span> SUCCESS</>
                  ) : report.execution_summary.target_status === 'SANDBOX_LIMITATION' ? (
                    <><span>⚠️</span> Sandbox: LIMITED</>
                  ) : (
                    <><span>❌</span> FAILED</>
                  )}
                </div>
                {report.execution_summary.target_status === 'SANDBOX_LIMITATION' && (
                  <div style={{ fontSize: '11px', color: '#92400E', fontFamily: 'monospace', marginTop: '6px', background: '#FEF3C7', padding: '6px 8px', borderRadius: '4px', lineHeight: 1.4 }}>
                    DuckDB cannot execute this {(report.execution_summary.target_dialect || 'target').toLowerCase()} query
                  </div>
                )}
                {report.execution_summary.target_status !== 'SUCCESS' && report.execution_summary.target_status !== 'SANDBOX_LIMITATION' && (
                  <div style={{ fontSize: '11px', color: '#991B1B', fontFamily: 'monospace', whiteSpace: 'pre-wrap', marginTop: '6px', background: '#f8717122', padding: '4px', borderRadius: '4px' }}>
                    {report.execution_summary.target_status}
                  </div>
                )}
              </div>
            </div>
            
            {(report.execution_summary.source_status !== 'SUCCESS' || report.execution_summary.target_status !== 'SUCCESS') && (
              <div style={{ fontSize: '13px', color: report.execution_summary.source_status === 'SANDBOX_LIMITATION' || report.execution_summary.target_status === 'SANDBOX_LIMITATION' ? '#92400E' : '#991B1B', marginTop: '8px', borderTop: '1px solid #FECACA', paddingTop: '12px' }}>
                {(report.execution_summary.source_status === 'SANDBOX_LIMITATION' || report.execution_summary.target_status === 'SANDBOX_LIMITATION') ? (
                  <><strong>Semantic Validation ⏭ NOT RUN.</strong> Semantic equivalence could not be proven in the sandbox.</>
                ) : (
                  <><strong>Semantic Validation ⏭ NOT RUN.</strong> There is no comparable output pair due to execution failure.</>
                )}
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
