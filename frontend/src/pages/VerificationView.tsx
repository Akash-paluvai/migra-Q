import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { ArrowDown, HelpCircle } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { SkippedStageCard } from '../components/SkippedStageCard';

interface VerificationViewProps {
  report: MigrationAssuranceReport;
}

export const VerificationView: React.FC<VerificationViewProps> = ({ report }) => {
  const summary = report.verification_summary;
  const hasVerification = Boolean(summary && summary.verification_id && summary.verification_id.trim());

  if (!hasVerification || !summary) {
    if (report.final_status === 'FAILED') {
      return (
        <div className="card-panel" style={{ padding: '32px', textAlign: 'center' }}>
          <h3 style={{ color: '#64748B', marginBottom: '8px' }}>Verification Not Applicable</h3>
          <p style={{ color: '#94A3B8', fontSize: '14px', maxWidth: '500px', margin: '0 auto' }}>
            Phase 8 Repair Verification was NOT RUN because upstream translation or execution failed.
          </p>
        </div>
      );
    }

    if (report.validation_summary?.overall_status === 'PASS') {
      return (
        <SkippedStageCard
          title="DIRECT PASS — VERIFICATION NOT REQUIRED"
          stageName="Verification"
          description="Initial validation passed directly with 0 discrepancies. Deterministic re-validation after repair was not required."
          reason="No semantic drift was detected during deterministic validation."
          upstreamLink={`/migrations/${report.migration_id}/validation`}
          upstreamLinkLabel="View Validation Evidence"
          metrics={[
            { label: 'Discrepancies', value: 0 },
            { label: 'Validation Status', value: 'PASS' },
            { label: 'Verification Status', value: 'SKIPPED' }
          ]}
        />
      );
    }

    return (
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#D97706' }}>
          <HelpCircle size={24} />
          <div>
            <h3>VERIFICATION PENDING</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Deterministic re-validation will run after an AI repair candidate is proposed.
            </p>
          </div>
        </div>
      </div>
    );


  }

  const rowsBefore = summary.affected_rows_before || 0;
  const rowsAfter = summary.affected_rows_after || 0;
  const reductionPct = summary.reduction_percentage || 0;
  const newDiscrepancies = summary.new_discrepancy_count || 0;
  const status = summary.status || 'NOT_ATTEMPTED';

  return (
    <div>
      {/* Header */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>REPAIR EXECUTION & DETERMINISTIC RE-VALIDATION</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Verification ID: {summary.verification_id} | Path: {report.verification_path}
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
            <span style={{ fontSize: '13px', fontWeight: 700, marginTop: '4px' }}>
              {reductionPct.toFixed(0)}% REDUCTION
            </span>
          </div>

          {/* After */}
          <div style={{ backgroundColor: '#F0FDF4', border: '1px solid #86EFAC', padding: '24px 36px', borderRadius: '8px', minWidth: '180px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#166534', textTransform: 'uppercase' }}>AFTER REPAIR</div>
            <div style={{ fontSize: '36px', fontWeight: 800, color: '#15803D', marginTop: '8px' }}>
              {rowsAfter.toLocaleString()}
            </div>
            <div style={{ fontSize: '12px', color: '#14532D', marginTop: '4px' }}>Remaining Discrepancies</div>
          </div>
        </div>
      </div>

      {/* Verification Audit Metrics */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '12px' }}>DETERMINISTIC VERIFICATION METRICS</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Original Discrepancies</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#0F172A', marginTop: '4px' }}>
              {summary.original_discrepancy_count}
            </div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Resolved Discrepancies</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: '#15803D', marginTop: '4px' }}>
              {summary.resolved_discrepancy_count}
            </div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>New Discrepancies Introduced</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: newDiscrepancies === 0 ? '#15803D' : '#DC2626', marginTop: '4px' }}>
              {newDiscrepancies}
            </div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Verification Status</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: status === 'VERIFIED' ? '#15803D' : '#D97706', marginTop: '4px' }}>
              {status}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
