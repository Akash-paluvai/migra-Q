import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface ErrorStateProps {
  title?: string;
  message: string;
  onRetry?: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  title = 'Unable to Load Data',
  message,
  onRetry,
}) => (
  <div
    style={{
      backgroundColor: '#FEF2F2',
      border: '1px solid #FCA5A5',
      borderRadius: '8px',
      padding: '32px',
      textAlign: 'center',
      margin: '24px 0',
    }}
  >
    <AlertTriangle size={36} color="#DC2626" style={{ margin: '0 auto 12px auto' }} />
    <h3 style={{ fontSize: '18px', fontWeight: 600, color: '#991B1B' }}>{title}</h3>
    <p style={{ fontSize: '14px', color: '#7F1D1D', marginTop: '4px', maxWidth: '600px', margin: '8px auto 0 auto' }}>
      {message}
    </p>
    {onRetry && (
      <button
        onClick={onRetry}
        className="btn-secondary"
        style={{ marginTop: '16px', borderColor: '#FCA5A5', color: '#991B1B' }}
      >
        Retry Request
      </button>
    )}
  </div>
);
