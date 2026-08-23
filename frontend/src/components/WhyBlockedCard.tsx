import React from 'react';
import { AlertOctagon } from 'lucide-react';
import type { MigrationAssuranceReport } from '../types/migration';

interface WhyBlockedCardProps {
  report: MigrationAssuranceReport;
}

export const WhyBlockedCard: React.FC<WhyBlockedCardProps> = ({ report }) => {
  if (report.final_status !== 'BLOCKED') {
    return null;
  }

  // Preflight failure overrides other display logic
  if (report.preflight_summary?.status === 'FAILED') {
    return (
      <div
        style={{
          backgroundColor: '#FEF2F2',
          border: '2px solid #FCA5A5',
          borderRadius: '8px',
          padding: '24px',
          marginBottom: '24px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#B91C1C', marginBottom: '12px' }}>
          <AlertOctagon size={24} />
          <h3 style={{ fontSize: '18px', fontWeight: 700 }}>Schema Preflight — BLOCKED</h3>
        </div>

        <div style={{ fontSize: '14px', color: '#7F1D1D', fontWeight: 600, marginBottom: '16px' }}>
          {report.preflight_summary.reason || 'Query references columns that do not exist.'}
        </div>

        {report.preflight_summary.missing_columns && report.preflight_summary.missing_columns.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#991B1B', marginBottom: '8px', textTransform: 'uppercase' }}>Missing column{report.preflight_summary.missing_columns.length > 1 ? 's' : ''}</div>
            {report.preflight_summary.missing_columns.map((c, i) => (
              <div key={i} style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', color: '#7F1D1D', marginBottom: '4px' }}>
                {c.table ? `${c.table}.` : ''}{c.column}
              </div>
            ))}
          </div>
        )}

        {report.preflight_summary.unresolved_tables && report.preflight_summary.unresolved_tables.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#991B1B', marginBottom: '8px', textTransform: 'uppercase' }}>Unresolved table{report.preflight_summary.unresolved_tables.length > 1 ? 's' : ''}</div>
            {report.preflight_summary.unresolved_tables.map((t, i) => (
              <div key={i} style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', color: '#7F1D1D', marginBottom: '4px' }}>
                {t}
              </div>
            ))}
          </div>
        )}

        {report.preflight_summary.available_columns && Object.keys(report.preflight_summary.available_columns).length > 0 && (
          <div style={{ backgroundColor: '#FEF3C7', padding: '12px', borderRadius: '6px', marginBottom: '16px' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#92400E', marginBottom: '8px' }}>Available schema</div>
            {Object.entries(report.preflight_summary.available_columns).map(([table, cols]) => (
              <div key={table} style={{ marginBottom: '8px' }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: '#B45309' }}>{table}</div>
                <ul style={{ margin: 0, paddingLeft: '16px', fontSize: '12px', color: '#92400E' }}>
                  {cols.map((c: string) => <li key={c}>{c}</li>)}
                </ul>
              </div>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <a
            href={`/migrations/${report.migration_id}/translation`}
            style={{
              padding: '8px 16px',
              backgroundColor: '#3B82F6',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-block'
            }}
          >
            Edit Target SQL
          </a>
          <div style={{ fontSize: '13px', color: '#991B1B' }}>
            Execution was not attempted. Edit the query to continue.
          </div>
        </div>
      </div>
    );
  }

  // Normal semantic discrepancy block
  const failedGates = report.gate_evaluation?.gates?.filter((g) => g.outcome === 'FAIL') || [];
  const affectedCount = report.discrepancy_summary?.total_affected_rows || 0;
  const discrepancyCount = report.discrepancy_summary?.discrepancy_count || 1;

  return (
    <div
      style={{
        backgroundColor: '#FEF2F2',
        border: '2px solid #FCA5A5',
        borderRadius: '8px',
        padding: '24px',
        marginBottom: '24px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#B91C1C', marginBottom: '12px' }}>
        <AlertOctagon size={24} />
        <h3 style={{ fontSize: '18px', fontWeight: 700 }}>FINAL STATUS: BLOCKED</h3>
      </div>

      <div style={{ fontSize: '14px', color: '#7F1D1D', fontWeight: 600, marginBottom: '8px' }}>
        Why? {discrepancyCount} unresolved semantic discrepancy detected.
      </div>

      <div style={{ fontSize: '13px', color: '#991B1B', marginBottom: '12px' }}>
        Impact: {affectedCount.toLocaleString()} affected records require remediation before migration can be verified.
      </div>

      {failedGates.length > 0 && (
        <div style={{ backgroundColor: '#FFFFFF', padding: '12px 16px', borderRadius: '6px', border: '1px solid #FECACA' }}>
          <div style={{ fontSize: '12px', fontWeight: 600, color: '#991B1B', marginBottom: '4px' }}>
            Failed Hard Gate:
          </div>
          {failedGates.map((g) => (
            <div key={g.gate_id} style={{ fontSize: '13px', fontFamily: 'var(--font-mono)', color: '#7F1D1D' }}>
              {g.gate_id}: {g.gate_name} — {g.reason}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
