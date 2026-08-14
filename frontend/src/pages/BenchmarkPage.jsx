import React from 'react';

export default function BenchmarkPage() {
  const cases = [
    { id: 'ORACLE_PG_01', name: 'Oracle NVL & SYSDATE to Postgres', status: 'Passed', score: 100, latency: '42ms' },
    { id: 'SNOWFLAKE_BQ_01', name: 'Snowflake ZEROIFNULL to BigQuery', status: 'Passed', score: 98, latency: '35ms' },
  ];

  return (
    <div className="container">
      <h1 style={{ fontSize: '1.75rem', marginBottom: '1.5rem' }}>Benchmark Evaluation Suite</h1>
      <div className="card">
        <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #374151', color: '#9ca3af' }}>
              <th style={{ padding: '0.75rem' }}>Case ID</th>
              <th style={{ padding: '0.75rem' }}>Test Case Name</th>
              <th style={{ padding: '0.75rem' }}>Status</th>
              <th style={{ padding: '0.75rem' }}>Confidence Score</th>
              <th style={{ padding: '0.75rem' }}>Latency</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.id} style={{ borderBottom: '1px solid #1f293d' }}>
                <td style={{ padding: '0.75rem', fontFamily: 'monospace' }}>{c.id}</td>
                <td style={{ padding: '0.75rem' }}>{c.name}</td>
                <td style={{ padding: '0.75rem', color: '#10b981' }}>{c.status}</td>
                <td style={{ padding: '0.75rem' }}>{c.score}/100</td>
                <td style={{ padding: '0.75rem', color: '#9ca3af' }}>{c.latency}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
