import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { Cpu, Search, HelpCircle, ShieldCheck, CheckCircle2 } from 'lucide-react';

interface DiagnosisViewProps {
  report: MigrationAssuranceReport;
}

export const DiagnosisView: React.FC<DiagnosisViewProps> = ({ report }) => {
  const summary = report.diagnosis_summary;
  const discSummary = report.discrepancy_summary;

  if (!summary && (!discSummary || discSummary.discrepancy_count === 0)) {
    return (
      <div>
        <div className="card-panel">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#15803D' }}>
            <CheckCircle2 size={24} />
            <div>
              <h3>ZERO DISCREPANCIES DETECTED</h3>
              <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
                Source and target query executions yielded 100% identical outputs and schema structures. No AI diagnosis required.
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>AI-GROUNDED DISCREPANCY DIAGNOSIS</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Diagnosis ID: {summary?.diagnosis_id || 'N/A'} | Target Discrepancy: {summary?.discrepancy_id || 'D-001'}
            </p>
          </div>
          <div style={{ backgroundColor: '#EFF6FF', color: '#1E40AF', padding: '6px 14px', borderRadius: '6px', fontSize: '13px', fontWeight: 700, border: '1px solid #BFDBFE' }}>
            Diagnosis Confidence: {summary?.diagnosis_confidence ? `${(summary.diagnosis_confidence * 100).toFixed(0)}%` : 'N/A'}
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
            {summary?.observed_change || 'Behavioral mismatch detected between source and target query outputs.'}
          </div>
        </div>

        {/* Section 2: Likely Mechanism */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#2563EB' }}>
            <Cpu size={18} />
            <h4 style={{ fontSize: '15px', fontWeight: 700 }}>Likely Mechanism</h4>
          </div>
          <div style={{ fontSize: '14px', color: '#0F172A', fontWeight: 500, lineHeight: 1.6 }}>
            {summary?.observed_change || 'Mechanism details not available in Phase 9 summary.'}
          </div>
        </div>

        {/* Section 3: Possible Cause */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#2563EB' }}>
            <ShieldCheck size={18} />
            <h4 style={{ fontSize: '15px', fontWeight: 700 }}>Possible Cause</h4>
          </div>
          <div style={{ fontSize: '14px', color: '#0F172A', fontWeight: 500, lineHeight: 1.6 }}>
            {summary?.status ? `Diagnosis status: ${summary.status}` : 'Cause details require full AI diagnosis artifact.'}
          </div>
        </div>

        {/* Section 4: Uncertainty */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#D97706' }}>
            <HelpCircle size={18} />
            <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#B45309' }}>Uncertainty Statement</h4>
          </div>
          <div style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
            Uncertainty assessment requires full AI diagnosis artifact. Summary provides observed change and confidence only.
          </div>
        </div>
      </div>
    </div>
  );
};
