import React from 'react';

interface SqlDiffViewerProps {
  originalSql: string;
  repairedSql: string;
  diffHighlight?: {
    originalExpression: string;
    repairedExpression: string;
  };
}

export const SqlDiffViewer: React.FC<SqlDiffViewerProps> = ({
  originalSql,
  repairedSql,
  diffHighlight,
}) => {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
      {/* Original Candidate */}
      <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', overflow: 'hidden' }}>
        <div style={{ backgroundColor: '#FEF2F2', color: '#991B1B', padding: '8px 16px', fontSize: '12px', fontWeight: 600, borderBottom: '1px solid #FCA5A5' }}>
          BEFORE REPAIR (INCORRECT CANDIDATE)
        </div>
        <pre className="code-panel" style={{ margin: 0 }}>
          <code>
            {diffHighlight ? (
              originalSql.split(diffHighlight.originalExpression).map((part, i, arr) => (
                <React.Fragment key={i}>
                  {part}
                  {i < arr.length - 1 && (
                    <span className="diff-removed">{diffHighlight.originalExpression}</span>
                  )}
                </React.Fragment>
              ))
            ) : (
              originalSql
            )}
          </code>
        </pre>
      </div>

      {/* Repaired Candidate */}
      <div style={{ border: '1px solid #E2E8F0', borderRadius: '8px', overflow: 'hidden' }}>
        <div style={{ backgroundColor: '#F0FDF4', color: '#166534', padding: '8px 16px', fontSize: '12px', fontWeight: 600, borderBottom: '1px solid #86EFAC' }}>
          AFTER REPAIR (REPAIRED PROPOSAL)
        </div>
        <pre className="code-panel" style={{ margin: 0 }}>
          <code>
            {diffHighlight ? (
              repairedSql.split(diffHighlight.repairedExpression).map((part, i, arr) => (
                <React.Fragment key={i}>
                  {part}
                  {i < arr.length - 1 && (
                    <span className="diff-added">{diffHighlight.repairedExpression}</span>
                  )}
                </React.Fragment>
              ))
            ) : (
              repairedSql
            )}
          </code>
        </pre>
      </div>
    </div>
  );
};
