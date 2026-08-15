import React from 'react';
import type { HardGateEvaluation } from '../types/migration';
import { StatusBadge } from './StatusBadge';

interface HardGateTableProps {
  evaluation: HardGateEvaluation;
}

export const HardGateTable: React.FC<HardGateTableProps> = ({ evaluation }) => {
  const { gates, passed_count, not_applicable_count, failed_count } = evaluation;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
        <div style={{ fontSize: '14px', fontWeight: 600, color: '#0F172A' }}>
          Hard Gate Evaluation Summary:
        </div>
        <div style={{ fontSize: '13px', fontWeight: 700, color: '#334155', backgroundColor: '#F1F5F9', padding: '6px 12px', borderRadius: '6px', border: '1px solid #CBD5E1' }}>
          {passed_count} PASS, {not_applicable_count} NOT APPLICABLE, {failed_count} FAIL
        </div>
      </div>

      <div className="enterprise-table-container">
        <table className="enterprise-table">
          <thead>
            <tr>
              <th>Gate ID</th>
              <th>Gate Name</th>
              <th>Status</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {gates.map((g) => (
              <tr key={g.gate_id}>
                <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '13px' }}>
                  {g.gate_id}
                </td>
                <td style={{ fontWeight: 500 }}>{g.gate_name}</td>
                <td>
                  <StatusBadge status={g.outcome} />
                </td>
                <td style={{ fontSize: '13px', color: '#64748B' }}>{g.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
