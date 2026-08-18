import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { SqlDiffViewer } from '../components/SqlDiffViewer';
import { ShieldCheck, AlertTriangle, HelpCircle } from 'lucide-react';
import { StatusBadge } from '../components/StatusBadge';
import { SkippedStageCard } from '../components/SkippedStageCard';

interface RepairViewProps {
  report: MigrationAssuranceReport;
}

export const RepairView: React.FC<RepairViewProps> = ({ report }) => {
  const summary = report.repair_summary;
  const verSummary = report.verification_summary;
  const isVerified = verSummary?.status === 'VERIFIED';
  const hasRepair = Boolean(summary && summary.repair_id && summary.repair_id.trim());

  // Case 1: Translation or Execution failed
  if (report.final_status === 'FAILED' && !hasRepair) {
    return (
      <div className="card-panel" style={{ padding: '32px', textAlign: 'center' }}>
        <h3 style={{ color: '#64748B', marginBottom: '8px' }}>Repair Not Applicable</h3>
        <p style={{ color: '#94A3B8', fontSize: '14px', maxWidth: '500px', margin: '0 auto' }}>
          Automated AI repair was NOT RUN because upstream translation or execution failed.
        </p>
      </div>
    );
  }

  // Case 2: Validation passed with 0 discrepancies (no repair needed)
  if (!hasRepair && report.validation_summary?.overall_status === 'PASS') {
    return (
      <SkippedStageCard
        title="NO REPAIR REQUIRED"
        stageName="Repair"
        description="Target SQL candidate passed all semantic validation gates with 0 discrepancies. Automated repair was not needed."
        reason="No semantic drift was detected during deterministic validation."
        upstreamLink={`/migrations/${report.migration_id}/validation`}
        upstreamLinkLabel="View Validation Evidence"
        metrics={[
          { label: 'Discrepancies', value: 0 },
          { label: 'Validation Status', value: 'PASS' },
          { label: 'Repair Status', value: 'SKIPPED' }
        ]}
      />
    );
  }

  // Case 3: No repair proposal generated yet (Pending)
  if (!hasRepair && report.final_status !== 'FAILED') {
    return (
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#D97706' }}>
          <HelpCircle size={24} />
          <div>
            <h3>REPAIR PENDING</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Repair will run after AI Diagnosis completes successfully.
            </p>
          </div>
        </div>
      </div>
    );
  }

  // Case 4: No repair proposal generated (Catch all)
  if (!hasRepair || !summary) {
    return (
      <div className="card-panel" style={{ padding: '32px', textAlign: 'center' }}>
        <h3 style={{ color: '#64748B', marginBottom: '8px' }}>No Repair Proposal Available</h3>
        <p style={{ color: '#94A3B8', fontSize: '14px', maxWidth: '500px', margin: '0 auto' }}>
          No automated repair candidate was generated for this migration.
        </p>
      </div>
    );
  }

  const origSql = summary.original_sql || report.translation_summary?.candidate_sql || '';
  const repSql = summary.proposed_sql || origSql;

  return (
    <div>
      {/* Header & Verification Badge */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>AI-GROUNDED REPAIR PROPOSAL</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Repair ID: {summary.repair_id} | Status: {summary.status}
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <StatusBadge status={summary.status} />

            {isVerified ? (
              <div style={{ backgroundColor: '#F0FDF4', color: '#15803D', padding: '6px 14px', borderRadius: '6px', fontSize: '13px', fontWeight: 700, border: '1px solid #BBF7D0', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldCheck size={16} />
                ✓ INDEPENDENTLY VERIFIED
              </div>
            ) : (
              <div style={{ backgroundColor: '#FFFBEB', color: '#B45309', padding: '6px 14px', borderRadius: '6px', fontSize: '13px', fontWeight: 700, border: '1px solid #FDE68A', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={16} />
                REPAIR PROPOSED
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Repair Explanation Summary */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '16px', color: '#0F172A' }}>REPAIR SUMMARY</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Target Region</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#166534', marginTop: '4px' }}>{summary.changed_region || 'Unknown Region'}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Repair Status</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '4px' }}>{summary.status}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Confidence</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-primary)', marginTop: '4px' }}>{(summary.repair_confidence * 100).toFixed(0)}%</div>
          </div>
        </div>

        {report.diagnosis_summary?.observed_change && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '8px' }}>Diagnosed Root Cause</div>
            <p style={{ margin: 0, color: '#475569', fontSize: '13px', lineHeight: 1.6 }}>
              {report.diagnosis_summary.observed_change}
            </p>
          </div>
        )}

        <div style={{ backgroundColor: '#F0F9FF', padding: '16px', borderRadius: '8px', border: '1px solid #BAE6FD', marginTop: '20px' }}>
          <div style={{ fontSize: '13px', color: '#0369A1' }}>
            <span style={{ fontWeight: 700 }}>Why this matters:</span> This automated repair modifies the target candidate SQL to resolve the identified semantic discrepancies, ensuring data equivalence with the source execution.
          </div>
        </div>
      </div>

      {/* SQL Diff Panel */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '16px' }}>SQL REPAIR DIFF (CANDIDATE vs PROPOSED)</h3>
        <SqlDiffViewer
          originalSql={origSql}
          repairedSql={repSql}
        />
      </div>

      {/* Repair Metadata */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '12px' }}>REPAIR ATTRIBUTES</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Repair ID</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '4px' }}>{summary.repair_id}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Repair Confidence</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-primary)', marginTop: '4px' }}>{(summary.repair_confidence * 100).toFixed(0)}%</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Target Region</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#166534', marginTop: '4px' }}>{summary.changed_region || 'N/A'}</div>
          </div>
        </div>
      </div>
    </div>
  );
};
