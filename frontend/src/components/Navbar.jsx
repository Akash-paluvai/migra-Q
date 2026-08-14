import React from 'react';

export default function Navbar({ activeTab, setActiveTab }) {
  return (
    <nav style={{ background: '#111827', borderBottom: '1px solid #374151', padding: '1rem 2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <div style={{ width: '32px', height: '32px', background: 'linear-gradient(135deg, #6366f1, #a855f7)', borderRadius: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>Q</div>
        <span style={{ fontSize: '1.25rem', fontWeight: '700', letterSpacing: '-0.5px' }}>Migra-Q</span>
      </div>
      <div style={{ display: 'flex', gap: '1.5rem' }}>
        {['dashboard', 'validation', 'benchmark'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              background: 'none',
              border: 'none',
              color: activeTab === tab ? '#6366f1' : '#9ca3af',
              fontWeight: activeTab === tab ? '600' : '400',
              cursor: 'pointer',
              textTransform: 'capitalize',
              fontSize: '1rem'
            }}
          >
            {tab}
          </button>
        ))}
      </div>
    </nav>
  );
}
