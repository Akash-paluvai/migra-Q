import React from 'react';
import { Layers } from 'lucide-react';

interface EmptyStateProps {
  title: string;
  message: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ title, message, action }) => (
  <div
    style={{
      backgroundColor: '#FFFFFF',
      border: '1px border-dashed #CBD5E1',
      borderRadius: '8px',
      padding: '48px 32px',
      textAlign: 'center',
      margin: '24px 0',
    }}
  >
    <Layers size={40} color="#94A3B8" style={{ margin: '0 auto 12px auto' }} />
    <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#0F172A' }}>{title}</h3>
    <p style={{ fontSize: '14px', color: '#64748B', marginTop: '4px', maxWidth: '500px', margin: '8px auto 0 auto' }}>
      {message}
    </p>
    {action && <div style={{ marginTop: '20px' }}>{action}</div>}
  </div>
);
