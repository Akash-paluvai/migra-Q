import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, Play, Shield, Code, Database } from 'lucide-react';
import { HeroVisual } from '../components/HeroVisual';
import { fetchApi } from '../api/client';

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();
  const [loadingDemo, setLoadingDemo] = useState(false);

  const handleExploreFlagship = async () => {
    try {
      setLoadingDemo(true);
      // Try fetching the specific migration instance
      await fetchApi('/api/v1/migrations/MIG-7BF1E8BDF850/assurance');
      navigate('/migrations/MIG-7BF1E8BDF850');
    } catch (err) {
      // If it doesn't exist, fallback to the interactive demo creation
      navigate('/new?demo=flagship');
    } finally {
      setLoadingDemo(false);
    }
  };

  return (
    <div style={{ margin: '-32px -32px 0 -32px' }}>
      {/* Hero Section (Dark Navy) */}
      <section
        style={{
          background: 'var(--gradient-hero)',
          padding: '80px 64px',
          color: '#FFFFFF',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <div style={{ position: 'relative', zIndex: 2, maxWidth: '800px' }}>
          <div style={{ fontSize: '14px', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '1px', color: '#94A3B8', marginBottom: '16px' }}>
            Platform - MIGRA-Q
          </div>

          <h1 style={{ fontSize: '48px', fontWeight: 700, lineHeight: 1.2, marginBottom: '24px', letterSpacing: '-1px' }}>
            MIGRA-Q: AI-Assisted Data<br/>Modernization Product Suite
          </h1>

          <p style={{ fontSize: '18px', color: '#CBD5E1', lineHeight: 1.6, marginBottom: '40px', maxWidth: '600px' }}>
            Reimagining Enterprise Data Transformation with AI Precision, Deterministic Execution, and Built-in Quality Assurance.
          </p>

          <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
            <Link 
              to="/new" 
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--accent-primary)',
                color: '#fff',
                padding: '12px 24px',
                borderRadius: '8px',
                fontWeight: 600,
                textDecoration: 'none',
                transition: 'all 0.2s'
              }}
            >
              Start a Migration <ArrowRight size={18} />
            </Link>
            <button
              onClick={handleExploreFlagship}
              disabled={loadingDemo}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                background: 'rgba(255, 255, 255, 0.1)',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#fff',
                padding: '12px 24px',
                borderRadius: '8px',
                fontWeight: 600,
                cursor: loadingDemo ? 'not-allowed' : 'pointer',
                opacity: loadingDemo ? 0.7 : 1,
                transition: 'all 0.2s'
              }}
            >
              <Play size={18} /> {loadingDemo ? 'Loading...' : 'Explore Flagship Demo'}
            </button>
          </div>
        </div>
        
        {/* Abstract Tech Background Pattern (simulating the reference image) */}
        <div style={{ position: 'absolute', right: '5%', top: '50%', transform: 'translateY(-50%)', opacity: 0.2, pointerEvents: 'none' }}>
           <Database size={400} color="#FFFFFF" />
        </div>
      </section>

      {/* Main Content Wrapper */}
      <div style={{ padding: '64px', maxWidth: '1400px', margin: '0 auto' }}>
        
        {/* Overview Section */}
        <section style={{ marginBottom: '80px', display: 'flex', gap: '64px', alignItems: 'center' }}>
          <div style={{ flex: 1 }}>
            <h2 style={{ fontSize: '28px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '16px' }}>
              Overview
            </h2>
            <p style={{ fontSize: '16px', color: 'var(--text-secondary)', lineHeight: 1.7, marginBottom: '24px' }}>
              MIGRA-Q is an enterprise-grade AI platform designed to accelerate the modernization and migration of legacy data ecosystems to cloud-native architectures. Leveraging advanced large language models (LLMs), it intelligently extracts business logic, automates code conversion, and performs deterministic reconciliation to enable seamless transformation of legacy workloads.
            </p>
            <p style={{ fontSize: '16px', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
              MIGRA-Q supports modernization scenarios such as Teradata to BigQuery migrations, orchestrating a transparent transformation journey across the entire migration lifecycle with a strong focus on predictability, auditability, and built-in data quality.
            </p>
          </div>
          <div style={{ flex: 1 }}>
             <HeroVisual />
          </div>
        </section>

        {/* Key Differentiators */}
        <section style={{ marginBottom: '80px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: 700, color: 'var(--accent-primary)', marginBottom: '32px' }}>
            Key Differentiators
          </h2>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '32px' }}>
            {/* Differentiator 1 */}
            <div className="card-panel" style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
               <div style={{ color: 'var(--accent-primary)' }}>
                 <Code size={48} strokeWidth={1.5} />
               </div>
               <div>
                 <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '12px' }}>Unified Modernization Engine</h3>
                 <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                   An end-to-end platform that harmonizes logic extraction, code translation, code optimization, pipeline conversion, and historical data reconciliation — streamlining data and application migration across heterogeneous systems.
                 </p>
               </div>
            </div>

            {/* Differentiator 2 */}
            <div className="card-panel" style={{ display: 'flex', gap: '24px', alignItems: 'flex-start' }}>
               <div style={{ color: 'var(--accent-primary)' }}>
                 <Shield size={48} strokeWidth={1.5} />
               </div>
               <div>
                 <h3 style={{ fontSize: '20px', fontWeight: 700, marginBottom: '12px' }}>Built-in Data Quality Assurance</h3>
                 <p style={{ fontSize: '15px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                   Integrated validation modules continuously profile, monitor, and remediate discrepancies through deterministic execution — ensuring trustworthy analytics from day one of migration with strict hard quality gates.
                 </p>
               </div>
            </div>
          </div>
        </section>

        {/* Platform Capabilities */}
        <section>
          <div style={{ fontSize: '14px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)', marginBottom: '16px', textAlign: 'center' }}>
            PLATFORM CAPABILITIES
          </div>
          
          <h2 style={{ fontSize: '32px', fontWeight: 700, textAlign: 'center', marginBottom: '48px' }}>
            How MIGRA-Q Decides & Validates
          </h2>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
            {[
              { num: '01', title: 'AI-Assisted Translation', desc: 'Convert legacy SQL logic into target cloud dialects using dialect-aware structural translation models.' },
              { num: '02', title: 'Deterministic Re-Validation', desc: 'Compare runtime execution behavior on actual data, isolating row mismatches and boundary flaws.' },
              { num: '03', title: 'Evidence-Based Repair', desc: 'Diagnose semantic discrepancies with AI and apply targeted patches based on execution evidence.' },
              { num: '04', title: 'Audit-Ready Assurance', desc: 'Immutably link translations to their verification ID, enforcing 11 hard quality gates for sign-off.' }
            ].map(cap => (
              <div key={cap.num} className="card-panel" style={{ position: 'relative', overflow: 'hidden' }}>
                <div style={{ fontSize: '48px', fontWeight: 800, color: 'var(--bg-tertiary)', position: 'absolute', top: '-10px', right: '10px', zIndex: 0 }}>
                  {cap.num}
                </div>
                <div style={{ position: 'relative', zIndex: 1 }}>
                  <h3 style={{ fontSize: '20px', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '12px' }}>{cap.title}</h3>
                  <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                    {cap.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

      </div>
    </div>
  );
};
