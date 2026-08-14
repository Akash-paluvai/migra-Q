import React from 'react';

export default function AssuranceGauge({ score, passed }) {
  const color = passed ? '#10b981' : score >= 70 ? '#f59e0b' : '#ef4444';

  return (
    <div style={{ textAlign: 'center', padding: '1.5rem', background: '#111827', borderRadius: '12px', border: `1px solid ${color}` }}>
      <div style={{ fontSize: '0.9rem', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '0.25rem' }}>Assurance Score</div>
      <div style={{ fontSize: '3rem', fontWeight: '800', color }}>{score} / 100</div>
      <div style={{ marginTop: '0.5rem', fontSize: '0.95rem', fontWeight: '600', color }}>
        {passed ? '✅ Quality Gate PASSED' : '❌ Quality Gate FAILED'}
      </div>
    </div>
  );
}
