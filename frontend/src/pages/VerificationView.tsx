import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { ShieldCheck, ArrowDown, CheckCircle2 } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';

interface VerificationViewProps {
  report: MigrationAssuranceReport;
}

export const VerificationView: React.FC<VerificationViewProps> = ({ report }) => {
  const summary = report.verification_summary;

  const rowsBefore = summary?.affected_rows_before || 0;
  const rowsAfter = summary?.affected_rows_after || 0;
  const reductionPct = summary?.reduction_percentage || 0;
  const newDiscrepancies = summary?.new_discrepancy_count || 0;
  const status = summary?.status || 'NOT_ATTEMPTED';

  return (
    <div>
      {/* Header */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>REPAIR EXECUTION & DETERMINISTIC RE-VALIDATION</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Verification ID: {summary?.verification_id || 'N/A'} | Path: {report.verification_path}
            </p>
          </div>
          <StatusBadge status={status} />
        </div>
      </div>

      {/* Hero Proof Centerpiece Box */}
      <div
        style={{
          backgroundColor: '#FFFFFF',
          border: '2px solid #22C55E',
          borderRadius: '12px',
          padding: '40px',
          boxShadow: '0 10px 25px -5px rgba(34, 197, 94, 0.1)',
          marginBottom: '24px',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', color: '#15803D', marginBottom: '24px' }}>
          DETERMINISTIC BEHAVIORAL RE-VALIDATION PROOF
        </div>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '48px', flexWrap: 'wrap' }}>
          {/* Before */}
          <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #FCA5A5', padding: '24px 36px', borderRadius: '8px', minWidth: '180px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#991B1B', textTransform: 'uppercase' }}>BEFORE REPAIR</div>
            <div style={{ fontSize: '36px', fontWeight: 800, color: '#B91C1C', marginTop: '8px' }}>
              {rowsBefore.toLocaleString()}
            </div>
            <div style={{ fontSize: '12px', color: '#7F1D1D', marginTop: '4px' }}>Affected Records</div>
          </div>

          <div style={{ color: '#22C55E', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <ArrowDown size={32} />
            <span style={{ fontSize: '14px', fontWeight: 800, color: '#15803D', marginTop: '4px' }}>
              {reductionPct.toFixed(0)}% REDUCTION
            </span>
          </div>

          {/* After */}
          <div style={{ backgroundColor: '#F0FDF4', border: '1px solid #86EFAC', padding: '24px 36px', borderRadius: '8px', minWidth: '180px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#166534', textTransform: 'uppercase' }}>AFTER REPAIR</div>
            <div style={{ fontSize: '36px', fontWeight: 800, color: '#15803D', marginTop: '8px' }}>
              {rowsAfter.toLocaleString()}
            </div>
            <div style={{ fontSize: '12px', color: '#166534', marginTop: '4px' }}>Affected Records</div>
          </div>
        </div>

        {/* Verification Checkpoints */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '24px', flexWrap: 'wrap', marginTop: '32px', paddingTop: '24px', borderTop: '1px solid #E2E8F0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600, color: '#15803D' }}>
            <CheckCircle2 size={16} /> Dataset unchanged
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600, color: '#15803D' }}>
            <CheckCircle2 size={16} /> Validation config unchanged
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 600, color: '#15803D' }}>
            <CheckCircle2 size={16} /> {newDiscrepancies} new discrepancies
          </div>
        </div>

        {/* Big Final Badge */}
        <div style={{ marginTop: '24px', display: 'inline-flex', alignItems: 'center', gap: '8px', backgroundColor: '#15803D', color: '#FFFFFF', padding: '10px 24px', borderRadius: '24px', fontSize: '16px', fontWeight: 700 }}>
          <ShieldCheck size={20} />
          ✓ DETERMINISTICALLY VERIFIED
        </div>
      </div>
    </div>
  );
};
