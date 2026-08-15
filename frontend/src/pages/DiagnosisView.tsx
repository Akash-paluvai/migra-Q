import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { Cpu, Search, HelpCircle, ShieldCheck } from 'lucide-react';

interface DiagnosisViewProps {
  report: MigrationAssuranceReport;
}

export const DiagnosisView: React.FC<DiagnosisViewProps> = ({ report }) => {
  const summary = report.diagnosis_summary;

  return (
    <div>
      {/* Header */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>AI-GROUNDED DISCREPANCY DIAGNOSIS</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Diagnosis ID: {summary?.diagnosis_id || 'diag-ai-001'} | Target Discrepancy: {summary?.discrepancy_id || 'D-001'}
            </p>
          </div>
          <div style={{ backgroundColor: '#EFF6FF', color: '#1E40AF', padding: '6px 14px', borderRadius: '6px', fontSize: '13px', fontWeight: 700, border: '1px solid #BFDBFE' }}>
            Diagnosis Confidence: {((summary?.diagnosis_confidence || 0.95) * 100).toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Structured AI Diagnosis Panel */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Section 1: Observed Change */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#2563EB' }}>
            <Search size={18} />
            <h4 style={{ fontSize: '15px', fontWeight: 700 }}>Observed Behavior Change</h4>
          </div>
          <div style={{ fontSize: '14px', color: '#0F172A', fontWeight: 500, lineHeight: 1.6 }}>
            {summary?.observed_change || 'Target comparison operator changed from > to >=.'}
          </div>
          <div style={{ fontSize: '12px', color: '#64748B', marginTop: '8px', fontFamily: 'var(--font-mono)' }}>
            Evidence IDs: [E-001, E-002, E-003, E-004]
          </div>
        </div>

        {/* Section 2: Likely Mechanism */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#2563EB' }}>
            <Cpu size={18} />
            <h4 style={{ fontSize: '15px', fontWeight: 700 }}>Likely Mechanism</h4>
          </div>
          <div style={{ fontSize: '14px', color: '#0F172A', fontWeight: 500, lineHeight: 1.6 }}>
            Boundary comparison became inclusive (`t.amount &gt;= 500.00`), causing boundary boundary values ($500.00) to shift classification.
          </div>
        </div>

        {/* Section 3: Possible Cause */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#2563EB' }}>
            <ShieldCheck size={18} />
            <h4 style={{ fontSize: '15px', fontWeight: 700 }}>Possible Cause</h4>
          </div>
          <div style={{ fontSize: '14px', color: '#0F172A', fontWeight: 500, lineHeight: 1.6 }}>
            LLM translation model introduced inclusive relational operator during syntax generation.
          </div>
        </div>

        {/* Section 4: Uncertainty */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#D97706' }}>
            <HelpCircle size={18} />
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#B45309' }}>Uncertainty Statement</h4>
          </div>
          <div style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
            Execution evidence identifies behavioral change with 100% certainty, but cannot determine model prompt selection intent.
          </div>
        </div>
      </div>
    </div>
  );
};
