import React from 'react';
import { Cpu, CheckCircle2, Wrench, Lock } from 'lucide-react';

export const HowDecidesBlock: React.FC = () => {
  return (
    <div
      style={{
        backgroundColor: '#0A192F',
        color: '#FFFFFF',
        borderRadius: '8px',
        padding: '24px',
        marginTop: '24px',
      }}
    >
      <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: '#94A3B8', marginBottom: '16px' }}>
        HOW MIGRA-Q DECIDES
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', padding: '16px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Cpu size={20} color="#60A5FA" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#F8FAFC' }}>1. AI Generation</div>
          <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
            Generates target SQL candidate from legacy source logic.
          </div>
        </div>

        <div style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', padding: '16px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <CheckCircle2 size={20} color="#34D399" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#F8FAFC' }}>2. Deterministic Validation</div>
          <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
            DuckDB sandbox executes queries and measures behavioral differences.
          </div>
        </div>

        <div style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', padding: '16px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Wrench size={20} color="#FBBF24" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#F8FAFC' }}>3. Evidence & Repair</div>
          <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
            Classifies discrepancies and generates minimal targeted repair proposal.
          </div>
        </div>

        <div style={{ backgroundColor: 'rgba(255, 255, 255, 0.05)', padding: '16px', borderRadius: '6px', border: '1px solid rgba(255, 255, 255, 0.1)' }}>
          <Lock size={20} color="#A78BFA" style={{ marginBottom: '8px' }} />
          <div style={{ fontSize: '13px', fontWeight: 600, color: '#F8FAFC' }}>4. Hard Gates</div>
          <div style={{ fontSize: '12px', color: '#94A3B8', marginTop: '4px' }}>
            11 deterministic gates enforce zero remaining discrepancies before decision.
          </div>
        </div>
      </div>
    </div>
  );
};
