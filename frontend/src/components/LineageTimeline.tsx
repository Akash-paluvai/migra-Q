import React from 'react';
import type { AuditLineage, MigrationAssuranceReport } from '../types/migration';
import { GitCommit, Check, X, AlertTriangle } from 'lucide-react';

interface LineageTimelineProps {
  lineage: AuditLineage;
  report?: MigrationAssuranceReport;
}

export const LineageTimeline: React.FC<LineageTimelineProps> = ({ lineage, report }) => {
  const getStatusDisplay = (phase: string): React.ReactNode => {
    if (!report) return null;
    
    if (phase === 'Phase 4 Validation') {
      if (report.validation_summary?.overall_status === 'PASS') {
        return <span style={{ color: '#15803D', display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14} /> Pass</span>;
      }
      const count = report.discrepancy_summary?.discrepancy_count;
      if (count !== undefined && count !== null) {
        return <span style={{ color: '#DC2626', display: 'flex', alignItems: 'center', gap: '4px' }}><X size={14} /> {count} discrepancy{count !== 1 ? 's' : ''}</span>;
      }
      return <span style={{ color: '#DC2626', display: 'flex', alignItems: 'center', gap: '4px' }}><X size={14} /> Failed</span>;
    }
    if (phase === 'Phase 7 AI Diagnosis') {
      if (report.diagnosis_summary?.diagnosis_confidence) {
        const conf = (report.diagnosis_summary.diagnosis_confidence * 100).toFixed(0);
        return <span style={{ color: '#D97706', display: 'flex', alignItems: 'center', gap: '4px' }}><AlertTriangle size={14} /> {conf}% / limited evidence</span>;
      }
      if (report.diagnosis_summary?.status) {
         return <span style={{ color: '#15803D', display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14} /> {report.diagnosis_summary.status.charAt(0).toUpperCase() + report.diagnosis_summary.status.slice(1).toLowerCase()}</span>;
      }
      return <span style={{ color: '#15803D', display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14} /> Diagnosed</span>;
    }
    if (phase === 'Phase 7 Repair Proposal') {
      if (report.repair_summary?.status === 'FAILED') {
        return <span style={{ color: '#DC2626', display: 'flex', alignItems: 'center', gap: '4px' }}><X size={14} /> Failed</span>;
      }
      if (report.repair_summary?.repair_id) {
        return <span style={{ color: '#15803D', display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14} /> Proposed</span>;
      }
    }
    if (phase === 'Phase 8 Verification') {
      if (report.verification_summary?.status === 'VERIFIED') {
        return <span style={{ color: '#15803D', display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14} /> Verified</span>;
      } else if (report.verification_summary?.status === 'FAILED' || report.verification_summary?.status === 'FAILED_VERIFICATION') {
        return <span style={{ color: '#DC2626', display: 'flex', alignItems: 'center', gap: '4px' }}><X size={14} /> Failed verification</span>;
      }
    }
    if (phase === 'Phase 9 Assurance') {
      if (report.final_status === 'VERIFIED') {
        return <span style={{ color: '#15803D', display: 'flex', alignItems: 'center', gap: '4px' }}><Check size={14} /> Verified</span>;
      } else if (report.final_status) {
        const text = report.final_status.charAt(0).toUpperCase() + report.final_status.slice(1).toLowerCase();
        return <span style={{ color: '#DC2626', display: 'flex', alignItems: 'center', gap: '4px' }}><X size={14} /> {text}</span>;
      }
    }
    
    return null;
  };

  const nodes = [
    { label: 'Translation ID', value: lineage.translation_id, phase: 'Phase 6 Translation' },
    { label: 'Source Execution ID', value: lineage.source_execution_id, phase: 'Phase 3 Execution' },
    { label: 'Target Execution ID', value: lineage.target_execution_id, phase: 'Phase 3 Execution' },
    { label: 'Validation ID', value: lineage.validation_id, phase: 'Phase 4 Validation' },
    { label: 'Diagnosis ID', value: lineage.diagnosis_id, phase: 'Phase 5 Diagnosis' },
    { label: 'AI Diagnosis ID', value: lineage.ai_diagnosis_id, phase: 'Phase 7 AI Diagnosis' },
    { label: 'Repair ID', value: lineage.repair_id, phase: 'Phase 7 Repair Proposal' },
    { label: 'Verification ID', value: lineage.verification_id, phase: 'Phase 8 Verification' },
  ].filter((n) => Boolean(n.value));
  
  if (report) {
    nodes.push({ label: 'Assurance Status', value: report.final_status, phase: 'Phase 9 Assurance' });
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ fontSize: '14px', fontWeight: 600, color: '#0F172A' }}>
          Verification Path: <span style={{ color: 'var(--accent-primary)' }}>{lineage.verification_path}</span>
        </div>
        <div style={{ fontSize: '12px', fontWeight: 600, color: lineage.is_complete ? '#15803D' : '#D97706' }}>
          {lineage.is_complete ? '✓ Lineage Chain Complete & Proven' : '⚠ Lineage Incomplete'}
        </div>
      </div>

      <div style={{ position: 'relative', paddingLeft: '24px' }}>
        {/* Vertical timeline bar */}
        <div
          style={{
            position: 'absolute',
            left: '11px',
            top: '8px',
            bottom: '8px',
            width: '2px',
            backgroundColor: '#CBD5E1',
          }}
        />

        {nodes.map((node) => (
          <div key={node.phase + node.value} style={{ position: 'relative', marginBottom: '20px' }}>
            {/* Timeline icon dot */}
            <div
              style={{
                position: 'absolute',
                left: '-24px',
                top: '2px',
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: '#FFFFFF',
                border: '2px solid var(--accent-primary)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <GitCommit size={12} color="var(--accent-primary)" />
            </div>

            <div style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '6px', padding: '12px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#64748B' }}>
                  {node.phase}
                </span>
                <span style={{ fontSize: '12px', fontWeight: 600 }}>
                  {getStatusDisplay(node.phase) || <span style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 400 }}>{node.label}</span>}
                </span>
              </div>
              <div style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', fontWeight: 600, color: '#0F172A' }}>
                {node.value}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
