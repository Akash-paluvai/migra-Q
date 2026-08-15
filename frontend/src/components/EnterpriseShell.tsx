import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Database, ShieldCheck, Activity } from 'lucide-react';

interface EnterpriseShellProps {
  children: React.ReactNode;
}

export const EnterpriseShell: React.FC<EnterpriseShellProps> = ({ children }) => {
  const location = useLocation();

  return (
    <div className="app-container">
      {/* Top Navigation Bar */}
      <header className="top-nav">
        <div className="nav-brand">
          <Link to="/" className="brand-container">
            <ShieldCheck size={26} color="#2563EB" />
            <span className="brand-logo-text">MIGRA-Q</span>
            <span className="brand-tagline">AI-Assisted Migration & Semantic Assurance</span>
          </Link>
        </div>

        <nav className="nav-links">
          <Link
            to="/"
            className={`nav-link ${location.pathname === '/' ? 'active' : ''}`}
          >
            Overview
          </Link>
          <Link
            to="/migrations"
            className={`nav-link ${location.pathname.startsWith('/migrations') ? 'active' : ''}`}
          >
            Migrations
          </Link>
        </nav>

        <div className="nav-controls">
          <span className="badge-env">
            <Database size={12} style={{ display: 'inline', marginRight: 4 }} />
            Profile: dev
          </span>
          <span className="badge-env" style={{ color: '#86EFAC', borderColor: 'rgba(34,197,94,0.3)' }}>
            <Activity size={12} style={{ display: 'inline', marginRight: 4 }} />
            System Healthy
          </span>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="page-main">
        {children}
      </main>

      {/* Unobtrusive Enterprise Footer */}
      <footer className="enterprise-footer">
        <p>MIGRA-Q — AI-Assisted SQL Logic Migration & Semantic Re-Validation Engine</p>
        <p style={{ marginTop: 4, fontSize: 11, color: '#94A3B8' }}>
          Independent prototype inspired by enterprise data-modernization challenges.
        </p>
      </footer>
    </div>
  );
};
