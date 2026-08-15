import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { SqlDiffViewer } from '../components/SqlDiffViewer';
import { CheckCircle2, ShieldCheck } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';

interface RepairViewProps {
  report: MigrationAssuranceReport;
}

export const RepairView: React.FC<RepairViewProps> = ({ report }) => {
  const summary = report.repair_summary;
  const verSummary = report.verification_summary;
  const isVerified = verSummary?.status === 'VERIFIED';

  const origSql = `SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount >= 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;`;

  const repSql = `SELECT
  c.customer_id,
  c.customer_segment,
  SUM(t.amount) AS total_amount,
  CASE WHEN t.amount > 500.00 THEN 'HIGH_RISK' ELSE 'NORMAL' END AS risk_class
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.status = 'COMPLETED'
GROUP BY c.customer_id, c.customer_segment, t.amount;`;

  return (
    <div>
      {/* Header & Verification Badge */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>AI-GROUNDED REPAIR PROPOSAL</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Repair ID: {summary?.repair_id || 'rep-001'} | Target Discrepancy: D-001
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <StatusBadge status={summary?.status || 'PROPOSED'} />

            {isVerified && (
              <div style={{ backgroundColor: '#F0FDF4', color: '#15803D', padding: '6px 14px', borderRadius: '6px', fontSize: '13px', fontWeight: 700, border: '1px solid #BBF7D0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={16} />
                ✓ INDEPENDENTLY VERIFIED
              </div>
            )}
          </div>
        </div>
      </div>

      {/* SQL Diff Panel */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '16px' }}>PROPOSED REPAIR SQL DIFF</h3>
        <SqlDiffViewer
          originalSql={origSql}
          repairedSql={repSql}
          diffHighlight={{
            originalExpression: 't.amount >= 500.00',
            repairedExpression: 't.amount > 500.00',
          }}
        />
      </div>

      {/* Repair Constraints & Safety Checklist */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '16px' }}>SAFETY & CONSTRAINT VALIDATION</h3>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          {[
            { label: 'Target Dialect Preserved', desc: 'Valid BigQuery syntax', status: true },
            { label: 'Read-Only Safety', desc: 'No DDL / DML mutations', status: true },
            { label: 'Output Schema Contract', desc: 'Columns & types intact', status: true },
            { label: 'Scope Restricted', desc: 'Only risk_class modified', status: true },
          ].map((item) => (
            <div key={item.label} style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#15803D', fontSize: '13px', fontWeight: 600 }}>
                <CheckCircle2 size={16} />
                {item.label}
              </div>
              <div style={{ fontSize: '12px', color: '#64748B', marginTop: '4px' }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
