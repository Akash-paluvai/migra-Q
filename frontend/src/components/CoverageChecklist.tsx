import React from 'react';
import type { ScoreComponent } from '../types/migration';

interface CoverageChecklistProps {
  coverage: number | null;
  components: ScoreComponent[];
}

export const CoverageChecklist: React.FC<CoverageChecklistProps> = ({
  coverage,
  components,
}) => {
  const skippedComponents = components.filter((c) => c.status === 'NOT_APPLICABLE');
  const covText = coverage !== null && coverage !== undefined ? `${coverage.toFixed(0)}% evaluated` : 'Scope not evaluated';

  return (
    <div style={{ backgroundColor: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '16px 20px', marginTop: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A' }}>
          Evidence Coverage Breakdown ({covText}):
        </div>
        <div style={{ fontSize: '12px', color: '#64748B' }}>
          Coverage reflects validation dimensions actually evaluated.
        </div>
      </div>

      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}>
        {components.map((c) => {
          const isEvaluated = c.status === 'SCORED';
          return (
            <div
              key={c.name}
              style={{
                fontSize: '12px',
                padding: '6px 12px',
                borderRadius: '6px',
                backgroundColor: isEvaluated ? '#F0FDF4' : '#F1F5F9',
                color: isEvaluated ? '#15803D' : '#64748B',
                border: `1px solid ${isEvaluated ? '#BBF7D0' : '#CBD5E1'}`,
                fontWeight: 500,
              }}
            >
              {isEvaluated ? '✓' : '—'} {c.name}: {isEvaluated ? `SCORED (${(c.effective_weight * 100).toFixed(0)}% weight)` : 'SKIPPED (N/A)'}
            </div>
          );
        })}
      </div>

      {skippedComponents.length > 0 && (
        <div style={{ marginTop: '12px', fontSize: '12px', color: '#B45309', fontWeight: 500 }}>
          Why: {skippedComponents.map((c) => c.name).join(', ')} was SKIPPED in this validation run and excluded from the score denominator.
        </div>
      )}
    </div>
  );
};
