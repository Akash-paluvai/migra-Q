import React from 'react';

export default function SQLDiffViewer({ sourceSQL, targetSQL, sourceDialect, targetDialect }) {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1rem' }}>
      <div style={{ background: '#0b0f19', border: '1px solid #374151', borderRadius: '8px', padding: '1rem' }}>
        <div style={{ fontSize: '0.85rem', color: '#6366f1', textTransform: 'uppercase', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Source ({sourceDialect})
        </div>
        <pre style={{ color: '#e5e7eb', fontSize: '0.9rem', overflowX: 'auto', whiteSpace: 'pre-wrap' }}>{sourceSQL}</pre>
      </div>
      <div style={{ background: '#0b0f19', border: '1px solid #374151', borderRadius: '8px', padding: '1rem' }}>
        <div style={{ fontSize: '0.85rem', color: '#10b981', textTransform: 'uppercase', marginBottom: '0.5rem', fontWeight: 'bold' }}>
          Translated Target ({targetDialect})
        </div>
        <pre style={{ color: '#e5e7eb', fontSize: '0.9rem', overflowX: 'auto', whiteSpace: 'pre-wrap' }}>{targetSQL}</pre>
      </div>
    </div>
  );
}
