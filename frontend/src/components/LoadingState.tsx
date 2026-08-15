import React from 'react';
import { Loader2 } from 'lucide-react';

export const LoadingState: React.FC<{ message?: string }> = ({
  message = 'Loading migration data from MIGRA-Q backend...',
}) => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '64px 32px' }}>
    <Loader2 size={32} color="#2563EB" style={{ animation: 'spin 1s linear infinite' }} />
    <p style={{ marginTop: '16px', fontSize: '14px', color: '#64748B' }}>{message}</p>
    <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
  </div>
);
