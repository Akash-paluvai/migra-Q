import React from 'react';
import type { AuditLineage } from '../types/migration';
import { GitCommit } from 'lucide-react';

interface LineageTimelineProps {
  lineage: AuditLineage;
}

export const LineageTimeline: React.FC<LineageTimelineProps> = ({ lineage }) => {
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

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
        <div style={{ fontSize: '14px', fontWeight: 600, color: '#0F172A' }}>
          Verification Path: <span style={{ color: '#2563EB' }}>{lineage.verification_path}</span>
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
          <div key={node.label} style={{ position: 'relative', marginBottom: '20px' }}>
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
                border: '2px solid #2563EB',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <GitCommit size={12} color="#2563EB" />
            </div>

            <div style={{ backgroundColor: '#FFFFFF', border: '1px solid #E2E8F0', borderRadius: '6px', padding: '12px 16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#64748B' }}>
                  {node.phase}
                </span>
                <span style={{ fontSize: '11px', color: '#94A3B8' }}>{node.label}</span>
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
