import React from 'react';
import { AlertOctagon } from 'lucide-react';
import type { MigrationAssuranceReport } from '../types/migration';

interface WhyBlockedCardProps {
  report: MigrationAssuranceReport;
}

export const WhyBlockedCard: React.FC<WhyBlockedCardProps> = ({ report }) => {
  if (report.final_status !== 'BLOCKED') {
    return null;
  }

  const failedGates = report.gate_evaluation.gates.filter((g) => g.outcome === 'FAIL');
  const affectedCount = report.discrepancy_summary?.total_affected_rows || 0;
  const discrepancyCount = report.discrepancy_summary?.discrepancy_count || 1;

  return (
    <div
      style={{
        backgroundColor: '#FEF2F2',
        border: '2px solid #FCA5A5',
        borderRadius: '8px',
        padding: '24px',
        marginBottom: '24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#B91C1C', marginBottom: '12px' }}>
        <AlertOctagon size={24} />
        <h3 style={{ fontSize: '18px', fontWeight: 700 }}>FINAL STATUS: BLOCKED</h3>
      </div>

      <div style={{ fontSize: '14px', color: '#7F1D1D', fontWeight: 600, marginBottom: '8px' }}>
        Why? {discrepancyCount} unresolved semantic discrepancy detected.
      </div>

      <div style={{ fontSize: '13px', color: '#991B1B', marginBottom: '12px' }}>
        Impact: {affectedCount.toLocaleString()} affected records require remediation before migration can be verified.
      </div>

      {failedGates.length > 0 && (
        <div style={{ backgroundColor: '#FFFFFF', padding: '12px 16px', borderRadius: '6px', border: '1px solid #FECACA' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#991B1B', marginBottom: '4px' }}>
            Failed Hard Gate:
          </div>
          {failedGates.map((g) => (
            <div key={g.gate_id} style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', color: '#7F1D1D' }}>
              {g.gate_id}: {g.gate_name} — {g.reason}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
