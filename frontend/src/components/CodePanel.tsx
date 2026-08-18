import React from 'react';

interface CodePanelProps {
  title?: string;
  code: string;
  language?: string;
  height?: string;
}

export const CodePanel: React.FC<CodePanelProps> = ({
  title,
  code,
  height = 'auto',
}) => {
  return (
    <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', overflow: 'hidden', minWidth: 0 }}>
      {title && (
        <div
          style={{
            backgroundColor: '#1E293B',
            color: '#94A3B8',
            fontSize: '12px',
            fontWeight: 600,
            padding: '8px 16px',
            borderBottom: '1px solid #334155',
            textTransform: 'uppercase',
            letterSpacing: '0.5px',
          }}
        >
          {title}
        </div>
      )}
      <pre className="code-panel" style={{ maxHeight: height, margin: 0, overflowX: 'auto' }}>
        <code>{code || '-- No SQL content'}</code>
      </pre>
    </div>
  );
};
