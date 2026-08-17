import React from 'react';
import { Link } from 'react-router-dom';
import { CheckCircle2, ArrowRight } from 'lucide-react';

interface SkippedStageCardProps {
  title: string;
  stageName: string;
  description: string;
  reason: string;
  upstreamLink: string;
  upstreamLinkLabel: string;
  metrics: { label: string; value: string | number }[];
}

export const SkippedStageCard: React.FC<SkippedStageCardProps> = ({
  title,
  stageName,
  description,
  reason,
  upstreamLink,
  upstreamLinkLabel,
  metrics
}) => {
  return (
    <div className="card-panel" style={{ padding: 0, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '24px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'var(--bg-primary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--status-pass-text)' }}>
          <CheckCircle2 size={24} />
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700 }}>{title}</h3>
        </div>
        <div style={{ padding: '4px 12px', backgroundColor: 'var(--bg-secondary)', borderRadius: '6px', fontSize: '12px', fontWeight: 600, color: 'var(--text-secondary)', border: '1px solid var(--border-color)' }}>
          NOT REQUIRED
        </div>
      </div>

      <div style={{ padding: '32px 24px', backgroundColor: 'var(--bg-secondary)' }}>
        <p style={{ fontSize: '15px', color: 'var(--text-primary)', lineHeight: 1.6, margin: '0 0 32px 0', maxWidth: '800px' }}>
          {description}
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '32px' }}>
          {/* Validation Context Details */}
          <div>
            <h4 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '16px', letterSpacing: '0.5px' }}>
              Pipeline Context
            </h4>
            <div style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}>
              {metrics.map((m, idx) => (
                <div key={m.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: idx < metrics.length - 1 ? '1px solid var(--border-color)' : 'none' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 500 }}>{m.label}</span>
                  <span style={{ fontSize: '14px', color: 'var(--text-primary)', fontWeight: 600, fontFamily: typeof m.value === 'number' ? 'var(--font-mono)' : 'inherit' }}>
                    {m.value}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Reasoning */}
          <div>
            <h4 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '16px', letterSpacing: '0.5px' }}>
              Why was {stageName.toLowerCase()} skipped?
            </h4>
            <p style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.6, backgroundColor: 'var(--bg-primary)', padding: '16px', borderRadius: '8px', border: '1px solid var(--border-color)', margin: 0 }}>
              {reason}
            </p>
            
            <div style={{ marginTop: '24px' }}>
              <Link to={upstreamLink} className="btn-primary" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px', textDecoration: 'none' }}>
                {upstreamLinkLabel}
                <ArrowRight size={16} />
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
