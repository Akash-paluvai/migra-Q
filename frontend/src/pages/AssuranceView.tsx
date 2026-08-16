import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { StatusBadge } from '../components/StatusBadge';
import { HardGateTable } from '../components/HardGateTable';
import { CoverageChecklist } from '../components/CoverageChecklist';
import { HowDecidesBlock } from '../components/HowDecidesBlock';
import { ShieldCheck, Award, Layers } from 'lucide-react';

interface AssuranceViewProps {
  report: MigrationAssuranceReport;
}

export const AssuranceView: React.FC<AssuranceViewProps> = ({ report }) => {
  const { score, gate_evaluation, final_status, decision_reason, verification_path } = report;

  return (
    <div>
      {/* Header */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>MIGRATION ASSURANCE CONTROL CENTER</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Assurance Engine Version: {report.assurance_version} | Verification Path: {verification_path}
            </p>
          </div>
          <StatusBadge status={final_status} />
        </div>
      </div>

      {/* 3 Distinct Concepts Grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
        {/* Concept 1: Assurance Score */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Award size={20} color="#2563EB" />
            <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#64748B' }}>
              ASSURANCE SCORE
            </span>
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#0F172A' }}>
            {score.evidence_score !== null && score.evidence_score !== undefined ? (
              <>
                {score.evidence_score.toFixed(1)}{' '}
                <span style={{ fontSize: '18px', fontWeight: 500, color: '#64748B' }}>/ 100</span>
              </>
            ) : (
              'N/A'
            )}
          </div>
          <div style={{ fontSize: '12px', color: '#64748B', marginTop: '6px' }}>
            How well the evaluated validation dimensions performed.
          </div>
        </div>

        {/* Concept 2: Evidence Coverage */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <Layers size={20} color="#2563EB" />
            <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#64748B' }}>
              EVIDENCE COVERAGE
            </span>
          </div>
          <div style={{ fontSize: '32px', fontWeight: 800, color: '#0F172A' }}>
            {score.evidence_coverage !== null && score.evidence_coverage !== undefined
              ? `${score.evidence_coverage.toFixed(0)}%`
              : 'N/A'}
          </div>
          <div style={{ fontSize: '12px', color: '#64748B', marginTop: '6px' }}>
            How much of the configured validation scope was actually evaluated.
          </div>
        </div>

        {/* Concept 3: Final Decision */}
        <div className="card-panel" style={{ marginBottom: 0 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
            <ShieldCheck size={20} color="#15803D" />
            <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#64748B' }}>
              FINAL DECISION
            </span>
          </div>
          <div style={{ marginBottom: '6px' }}>
            <StatusBadge status={final_status} />
          </div>
          <div style={{ fontSize: '12px', color: '#64748B', marginTop: '6px' }}>
            Determined by hard gates and verification evidence.
          </div>
        </div>
      </div>

      {/* Coverage Explanation Breakdown */}
      <div className="card-panel">
        <h3>VALIDATION SCOPE COVERAGE</h3>
        <CoverageChecklist coverage={score.evidence_coverage} components={score.components} />
      </div>

      {/* Hard Gate Results Table */}
      <div className="card-panel">
        <h3>DETERMINISTIC HARD GATES</h3>
        <p style={{ fontSize: '13px', color: '#64748B', marginBottom: '16px' }}>
          All 11 gates must evaluate to PASS or NOT_APPLICABLE for VERIFIED decision.
        </p>
        <HardGateTable evaluation={gate_evaluation} />
      </div>

      {/* Decision Rationale */}
      <div className="card-panel">
        <h3>DECISION RATIONALE</h3>
        <p style={{ fontSize: '14px', color: '#334155', lineHeight: 1.6, marginTop: '4px' }}>
          {decision_reason}
        </p>
      </div>

      {/* How MIGRA-Q Decides Architecture Panel */}
      <HowDecidesBlock />
    </div>
  );
};
