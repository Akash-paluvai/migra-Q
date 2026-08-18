import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, Search, Filter, RefreshCw } from 'lucide-react';
import { listMigrations } from '../api/migrations';
import type { MigrationRecord } from '../types/migration';
import { StatusBadge } from '../components/StatusBadge';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';

export const MigrationsPage: React.FC = () => {
  const [migrations, setMigrations] = useState<MigrationRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [filterState, setFilterState] = useState<string>('ALL');

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await listMigrations();
      setMigrations(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch migrations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const filteredMigrations = migrations.filter((m) => {
    const matchesSearch =
      m.migration_id.toLowerCase().includes(search.toLowerCase()) ||
      m.source_dialect.toLowerCase().includes(search.toLowerCase()) ||
      m.target_dialect.toLowerCase().includes(search.toLowerCase()) ||
      m.dataset_id.toLowerCase().includes(search.toLowerCase());

    const matchesState = filterState === 'ALL' || m.final_status === filterState || m.current_state === filterState;

    return matchesSearch && matchesState;
  });

  return (
    <div>
      {/* Header & Workbench Actions */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
        <div>
          <h1 className="page-title">MIGRATIONS</h1>
          <p className="page-subtitle">
            Monitor migration status, semantic discrepancies, and assurance outcomes.
          </p>
        </div>

        <div style={{ display: 'flex', gap: '12px' }}>
          <button onClick={loadData} className="btn-secondary" style={{ padding: '8px 14px' }}>
            <RefreshCw size={14} /> Refresh
          </button>

          <Link to="/migrations/new" className="btn-primary">
            <Plus size={16} /> New Migration
          </Link>
        </div>
      </div>

      {/* Filter Controls */}
      <div
        style={{
          display: 'flex',
          gap: '16px',
          backgroundColor: '#FFFFFF',
          padding: '16px',
          borderRadius: '8px',
          border: '1px solid #E2E8F0',
          marginBottom: '24px',
          alignItems: 'center',
          flexWrap: 'wrap',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flex: 1, minWidth: '240px' }}>
          <Search size={16} color="#64748B" />
          <input
            type="text"
            placeholder="Search by ID, dialect, dataset..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{
              width: '100%',
              border: 'none',
              outline: 'none',
              fontSize: '14px',
              color: '#0F172A',
            }}
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Filter size={16} color="#64748B" />
          <span style={{ fontSize: '13px', color: '#64748B', fontWeight: 500 }}>Status:</span>
          <select
            value={filterState}
            onChange={(e) => setFilterState(e.target.value)}
            style={{
              padding: '6px 12px',
              borderRadius: '6px',
              border: '1px solid #CBD5E1',
              fontSize: '13px',
              backgroundColor: '#FFFFFF',
              color: '#0F172A',
            }}
          >
            <option value="ALL">All Statuses</option>
            <option value="VERIFIED">VERIFIED</option>
            <option value="BLOCKED">BLOCKED</option>
            <option value="FAILED">FAILED</option>
            <option value="IN_PROGRESS">IN_PROGRESS</option>
          </select>
        </div>
      </div>

      {/* Content Area */}
      {loading ? (
        <LoadingState message="Fetching migrations list..." />
      ) : error ? (
        <ErrorState message={error} onRetry={loadData} />
      ) : filteredMigrations.length === 0 ? (
        <EmptyState
          title="No Migrations Found"
          message="No migration runs match the current criteria."
          action={
            <Link to="/migrations/new" className="btn-primary">
              Start New Migration
            </Link>
          }
        />
      ) : (
        <div className="enterprise-table-container">
          <table className="enterprise-table">
            <thead>
              <tr>
                <th>Migration ID</th>
                <th>Source</th>
                <th>Target</th>
                <th>Dataset</th>
                <th>State</th>
                <th>Final Status</th>
                <th>Assurance Score</th>
                <th>Coverage</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {filteredMigrations.map((m) => (
                <tr key={m.migration_id}>
                  <td style={{ fontFamily: 'var(--font-mono)', fontWeight: 600, fontSize: '13px' }}>
                    <Link
                      to={`/migrations/${m.migration_id}`}
                      style={{ color: 'var(--accent-primary)', textDecoration: 'none' }}
                    >
                      {m.migration_id}
                    </Link>
                  </td>
                  <td style={{ textTransform: 'capitalize' }}>{m.source_dialect}</td>
                  <td style={{ textTransform: 'capitalize' }}>{m.target_dialect}</td>
                  <td style={{ fontFamily: 'var(--font-mono)', fontSize: '13px', color: '#64748B' }}>
                    {m.dataset_id}
                  </td>
                  <td>
                    <span style={{ fontSize: '12px', fontWeight: 600, color: '#475569' }}>
                      {m.current_state}
                    </span>
                  </td>
                  <td>
                    <StatusBadge status={m.final_status} />
                  </td>
                  <td style={{ fontWeight: 600 }}>
                    {m.assurance_score != null ? `${m.assurance_score.toFixed(1)} / 100` : '—'}
                  </td>
                  <td>
                    {m.evidence_coverage != null ? `${m.evidence_coverage.toFixed(0)}%` : '—'}
                  </td>
                  <td>
                    <Link
                      to={`/migrations/${m.migration_id}`}
                      className="btn-secondary"
                      style={{ padding: '4px 10px', fontSize: '12px' }}
                    >
                      View Details →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
