import React from 'react';
import { FileCode, Sparkles, CheckSquare, Wrench, ShieldCheck } from 'lucide-react';

export const HeroVisual: React.FC = () => {
  return (
    <div
      style={{
        backgroundColor: '#0F172A',
        borderRadius: '12px',
        padding: '32px 24px',
        border: '1px solid #334155',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.3)',
        marginTop: '24px',
        color: '#F8FAFC',
      }}
    >
      <div style={{ fontSize: '11px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: '#94A3B8', marginBottom: '20px', textAlign: 'center' }}>
        MIGRA-Q AUTOMATED MIGRATION & RE-VALIDATION WORKFLOW
      </div>

      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
          gap: '12px',
          alignItems: 'center',
        }}
      >
        {/* Node 1: Legacy Logic */}
        <div style={{ backgroundColor: '#1E293B', padding: '16px 12px', borderRadius: '8px', border: '1px solid #475569', textAlign: 'center' }}>
          <FileCode size={24} color="#60A5FA" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 600 }}>Legacy SQL</div>
          <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>Teradata Syntax</div>
        </div>

        <div style={{ color: '#475569', textAlign: 'center', fontSize: '18px', fontWeight: 700 }}>→</div>

        {/* Node 2: AI Translation */}
        <div style={{ backgroundColor: '#1E293B', padding: '16px 12px', borderRadius: '8px', border: '1px solid #475569', textAlign: 'center' }}>
          <Sparkles size={24} color="#A78BFA" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 600 }}>AI Translation</div>
          <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '2px' }}>BigQuery Candidate</div>
        </div>

        <div style={{ color: '#475569', textAlign: 'center', fontSize: '18px', fontWeight: 700 }}>→</div>

        {/* Node 3: Behavior Check */}
        <div style={{ backgroundColor: '#1E293B', padding: '16px 12px', borderRadius: '8px', border: '1px solid #F59E0B', textAlign: 'center' }}>
          <CheckSquare size={24} color="#F59E0B" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 600 }}>Behavior Check</div>
          <div style={{ fontSize: '11px', color: '#FCD34D', marginTop: '2px' }}>Drift Detected</div>
        </div>

        <div style={{ color: '#475569', textAlign: 'center', fontSize: '18px', fontWeight: 700 }}>→</div>

        {/* Node 4: AI Repair */}
        <div style={{ backgroundColor: '#1E293B', padding: '16px 12px', borderRadius: '8px', border: '1px solid #3B82F6', textAlign: 'center' }}>
          <Wrench size={24} color="#60A5FA" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 600 }}>AI Repair</div>
          <div style={{ fontSize: '11px', color: '#93C5FD', marginTop: '2px' }}>Minimal Patch</div>
        </div>

        <div style={{ color: '#475569', textAlign: 'center', fontSize: '18px', fontWeight: 700 }}>→</div>

        {/* Node 5: Verification */}
        <div style={{ backgroundColor: '#14532D', padding: '16px 12px', borderRadius: '8px', border: '1px solid #22C55E', textAlign: 'center' }}>
          <ShieldCheck size={24} color="#4ADE80" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#FFFFFF' }}>✓ VERIFIED</div>
          <div style={{ fontSize: '11px', color: '#86EFAC', marginTop: '2px' }}>0 Mismatches</div>
        </div>
      </div>
    </div>
  );
};
