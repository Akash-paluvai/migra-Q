import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Play, Shield, Code, Database, Cpu } from 'lucide-react';
import { HeroVisual } from '../components/HeroVisual';
import { getFlagshipMigration } from '../api/migrations';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleExploreFlagship = async () => {
    try {
      setLoadingDemo(true);
      setErrorMsg(null);
      const flagship = await getFlagshipMigration();
      navigate(`/migrations/${flagship.migration_id}`);
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : 'Failed to load flagship demo.');
    } finally {
      setLoadingDemo(false);
    }
  };

  return (
    <div>
      {/* Hero Section */}
      <section
        style={{
          backgroundColor: '#FFFFFF',
          border: '1px solid #E2E8F0',
          borderRadius: '12px',
          padding: '48px 40px',
          marginBottom: '40px',
          boxShadow: '0 4px 6px -1px rgba(0,0,0,0.05)',
        }}
      >
        <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1.5px', color: '#2563EB', marginBottom: '12px' }}>
          AI-ASSISTED DATA MODERNIZATION CONTROL PLANE
        </div>

        <h1 style={{ fontSize: '40px', fontWeight: 800, color: '#0F172A', lineHeight: 1.15, letterSpacing: '-1px' }}>
          MIGRA-Q
        </h1>
        <div style={{ fontSize: '22px', fontWeight: 600, color: '#334155', marginTop: '6px', marginBottom: '16px' }}>
          AI-Assisted Migration & Semantic Assurance
        </div>

        <p style={{ fontSize: '18px', color: '#475569', maxWidth: '800px', lineHeight: 1.6, marginBottom: '8px' }}>
          "Translate legacy data logic. Verify behavior. Repair with evidence."
        </p>

        <p style={{ fontSize: '14px', fontStyle: 'italic', color: '#64748B', marginBottom: '28px' }}>
          "Syntactic success is not semantic correctness."
        </p>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flexWrap: 'wrap' }}>
          <Link to="/migrations/new" className="btn-primary" style={{ padding: '12px 24px', fontSize: '15px' }}>
            Start a Migration
            <ArrowRight size={18} />
          </Link>

          <button
            onClick={handleExploreFlagship}
            disabled={loadingDemo}
            className="btn-secondary"
            style={{ padding: '12px 24px', fontSize: '15px', backgroundColor: '#F8FAFC' }}
          >
            <Play size={16} color="#2563EB" />
            {loadingDemo ? 'Loading Flagship...' : 'Explore Flagship Demo'}
          </button>
        </div>

        {errorMsg && (
          <div style={{ marginTop: '16px', color: '#DC2626', fontSize: '13px', fontWeight: 500 }}>
            ⚠ {errorMsg}
          </div>
        )}

        {/* Custom Hero Workflow Visual */}
        <HeroVisual />
      </section>

      {/* Outcome Strip */}
      <section
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '16px',
          marginBottom: '40px',
        }}
      >
        {[
          { title: 'AI-Assisted Candidate Translation', desc: 'Generates dialect-accurate SQL candidates', icon: <Code size={20} color="#2563EB" /> },
          { title: 'Deterministic Re-Validation', desc: 'Executes sandbox comparison on actual data', icon: <Database size={20} color="#2563EB" /> },
          { title: 'Evidence-Based Repair', desc: 'Classifies discrepancies and proposes patches', icon: <Cpu size={20} color="#2563EB" /> },
          { title: 'Audit-Ready Lineage', desc: 'Immutably links translation to verification ID', icon: <Shield size={20} color="#2563EB" /> },
        ].map((item) => (
          <div
            key={item.title}
            style={{
              backgroundColor: '#FFFFFF',
              border: '1px solid #E2E8F0',
              borderRadius: '8px',
              padding: '20px',
            }}
          >
            <div style={{ marginBottom: '10px' }}>{item.icon}</div>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#0F172A' }}>{item.title}</div>
            <div style={{ fontSize: '13px', color: '#64748B', marginTop: '4px' }}>{item.desc}</div>
          </div>
        ))}
      </section>

      {/* Platform Capability Sections (01, 02, 03) */}
      <section>
        <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', color: '#64748B', marginBottom: '16px' }}>
          PLATFORM CAPABILITIES
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '24px' }}>
          {/* Capability 01 */}
          <div className="card-panel">
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#2563EB', marginBottom: '12px' }}>01</div>
            <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#0F172A', marginBottom: '8px' }}>Translate</h3>
            <p style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
              Convert legacy SQL logic (Teradata, Oracle, Netezza) into target cloud dialects (BigQuery, Snowflake) using dialect-aware structural translation models.
            </p>
          </div>

          {/* Capability 02 */}
          <div className="card-panel">
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#2563EB', marginBottom: '12px' }}>02</div>
            <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#0F172A', marginBottom: '8px' }}>Verify</h3>
            <p style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
              Compare runtime execution behavior rather than relying solely on syntax parsing. Multi-layer validators isolate row mismatches, schema drift, and boundary flaws.
            </p>
          </div>

          {/* Capability 03 */}
          <div className="card-panel">
            <div style={{ fontSize: '28px', fontWeight: 800, color: '#2563EB', marginBottom: '12px' }}>03</div>
            <h3 style={{ fontSize: '20px', fontWeight: 700, color: '#0F172A', marginBottom: '8px' }}>Assure</h3>
            <p style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
              Diagnose semantic discrepancies with AI, apply targeted repairs, and deterministically re-validate 100% reduction through 11 hard quality gates.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
};
