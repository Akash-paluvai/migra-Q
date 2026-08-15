import React from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { LineageTimeline } from '../components/LineageTimeline';

interface LineageViewProps {
  report: MigrationAssuranceReport;
}

export const LineageView: React.FC<LineageViewProps> = ({ report }) => {
  return (
    <div>
      <div className="card-panel">
        <h3 style={{ marginBottom: '4px' }}>AUDIT LINEAGE & PROVENANCE CHAIN</h3>
        <p style={{ fontSize: '13px', color: '#64748B', marginBottom: '24px' }}>
          Immutably tracks artifact dependencies across all Phase 1–9 execution stages.
        </p>

        <LineageTimeline lineage={report.lineage} />
      </div>
    </div>
  );
};
