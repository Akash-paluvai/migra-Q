import { useEffect, useState } from 'react'

interface HealthStatus {
  status: string
  service?: string
  database?: string
}

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetch('/api/v1/health')
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif', padding: '2rem', maxWidth: '600px', margin: '0 auto' }}>
      <h1>MIGRA-Q</h1>
      <p>AI-Assisted Legacy Data Migration &amp; Semantic Assurance</p>
      <hr />
      <h2>Backend Health</h2>
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {health ? (
        <pre style={{ background: '#f4f4f4', padding: '1rem', borderRadius: '4px' }}>
          {JSON.stringify(health, null, 2)}
        </pre>
      ) : (
        !error && <p>Loading…</p>
      )}
    </div>
  )
}

export default App
