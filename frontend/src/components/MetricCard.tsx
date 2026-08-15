import React from 'react';

interface MetricCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  trend?: string;
  status?: 'success' | 'warn' | 'fail' | 'neutral';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subtitle,
  status = 'neutral',
}) => {
  let borderColor = '#E2E8F0';
  let valueColor = '#0F172A';

  if (status === 'success') {
    borderColor = '#BBF7D0';
    valueColor = '#15803D';
  } else if (status === 'fail') {
    borderColor = '#FCA5A5';
    valueColor = '#B91C1C';
  } else if (status === 'warn') {
    borderColor = '#FDE68A';
    valueColor = '#B45309';
  }

  return (
    <div
      style={{
        backgroundColor: '#FFFFFF',
        border: `1px solid ${borderColor}`,
        borderRadius: '8px',
        padding: '20px',
        boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
      }}
    >
      <div style={{ fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#64748B', marginBottom: '8px' }}>
        {label}
      </div>
      <div style={{ fontSize: '28px', fontWeight: 700, color: valueColor, letterSpacing: '-0.5px' }}>
        {typeof value === 'number' ? value.toLocaleString() : value}
      </div>
      {subtitle && (
        <div style={{ fontSize: '12px', color: '#64748B', marginTop: '4px' }}>
          {subtitle}
        </div>
      )}
    </div>
  );
};
