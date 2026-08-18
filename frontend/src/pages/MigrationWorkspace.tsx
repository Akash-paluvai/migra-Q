import React, { useEffect, useState } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';
import { RefreshCw, ArrowLeft } from 'lucide-react';
import { getAssuranceReport, getMigration } from '../api/migrations';
import type { MigrationAssuranceReport, MigrationRecord } from '../types/migration';
import { WorkflowStepper } from '../components/WorkflowStepper';
import { StatusBadge } from '../components/StatusBadge';
import { MetricCard } from '../components/MetricCard';
import { WhyBlockedCard } from '../components/WhyBlockedCard';
import { LoadingState } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';

import { TranslationView } from './TranslationView';
import { ValidationView } from './ValidationView';
import { DiscrepanciesView } from './DiscrepanciesView';
import { DiagnosisView } from './DiagnosisView';
import { RepairView } from './RepairView';
import { VerificationView } from './VerificationView';
import { AssuranceView } from './AssuranceView';
import { LineageView } from './LineageView';

export const MigrationWorkspace: React.FC = () => {
  const { migrationId } = useParams<{ migrationId: string }>();
  const location = useLocation();
  const [report, setReport] = useState<MigrationAssuranceReport | null>(null);
  const [record, setRecord] = useState<MigrationRecord | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const activeTab = location.pathname.split('/')[3] || 'overview';

  const loadData = async () => {
    if (!migrationId) return;
    try {
      setLoading(true);
      setError(null);
      const repData = await getAssuranceReport(migrationId);
      const recData = await getMigration(migrationId);
      setReport(repData);
      setRecord(recData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch migration workspace data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    const intervalId = setInterval(async () => {
      if (!migrationId) return;
      try {
        const repData = await getAssuranceReport(migrationId);
        const recData = await getMigration(migrationId);
        setReport(repData);
        setRecord(recData);

        const state = recData.current_state;
        const isTerminal = ['VERIFIED', 'FAILED', 'BLOCKED', 'ERROR'].includes(state);
        if (isTerminal) {
          clearInterval(intervalId);
        }
      } catch (err) {
        clearInterval(intervalId);
      }
    }, 3000);

    return () => clearInterval(intervalId);
  }, [migrationId]);

  if (loading) {
    return <LoadingState message={`Loading migration ${migrationId}...`} />;
  }

  if (error || !report || !record) {
    return <ErrorState message={error || 'Migration report not found.'} onRetry={loadData} />;
  }

  const initialValStatus = report.validation_summary?.overall_status || 'N/A';
  const discrepancyCount = report.discrepancy_summary?.discrepancy_count || 0;
  const affectedRecords = report.discrepancy_summary?.total_affected_rows || 0;
  const repairStatus = report.verification_summary?.verification_id
    ? report.verification_summary.status
    : 'NOT_ATTEMPTED';

  const isPassWithoutDiscrepancies = report.validation_summary?.overall_status === 'PASS' && (!report.discrepancy_summary || report.discrepancy_summary.discrepancy_count === 0);

  const tabs = [
    { id: 'overview', label: 'Overview', path: `/migrations/${migrationId}` },
    { id: 'translation', label: 'Translation', path: `/migrations/${migrationId}/translation` },
    { id: 'validation', label: 'Validation', path: `/migrations/${migrationId}/validation` },
    { id: 'discrepancies', label: 'Discrepancies', path: `/migrations/${migrationId}/discrepancies` },
    { id: 'diagnosis', label: 'AI Diagnosis', path: `/migrations/${migrationId}/diagnosis`, isSkipped: isPassWithoutDiscrepancies || report.diagnosis_summary?.status === 'NOT_REQUIRED' },
    { id: 'repair', label: 'Repair', path: `/migrations/${migrationId}/repair`, isSkipped: !report.repair_summary?.repair_id && report.validation_summary?.overall_status === 'PASS' },
    { id: 'verification', label: 'Verification', path: `/migrations/${migrationId}/verification`, isSkipped: report.validation_summary?.overall_status === 'PASS' },
    { id: 'assurance', label: 'Assurance', path: `/migrations/${migrationId}/assurance` },
    { id: 'lineage', label: 'Lineage', path: `/migrations/${migrationId}/lineage` },
  ];

  return (
    <div>
      {/* Top Back Link */}
      <div style={{ marginBottom: '16px' }}>
        <Link to="/migrations" style={{ fontSize: '13px', color: '#64748B', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
          <ArrowLeft size={14} /> Back to Migrations List
        </Link>
      </div>

      {/* Migration Workspace Header */}
      <div className="card-panel" style={{ padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <h1 style={{ fontSize: '24px', fontWeight: 800, color: '#0F172A', fontFamily: 'var(--font-mono)' }}>
                {report.migration_id}
              </h1>
              <StatusBadge status={report.final_status} />
            </div>

            <div style={{ fontSize: '14px', color: '#64748B', marginTop: '6px' }}>
              Source: <strong style={{ color: '#0F172A', textTransform: 'capitalize' }}>{record.source_dialect}</strong> → Target: <strong style={{ color: '#0F172A', textTransform: 'capitalize' }}>{record.target_dialect}</strong> | Dataset: <strong style={{ color: '#0F172A', fontFamily: 'var(--font-mono)' }}>{record.dataset_id}</strong>
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button onClick={loadData} className="btn-secondary" style={{ padding: '8px 14px' }}>
              <RefreshCw size={14} /> Refresh Status
            </button>
          </div>
        </div>
      </div>

      {/* Horizontal Workflow Stepper */}
      <WorkflowStepper currentState={record.current_state} report={report} />

      {/* Secondary Tab Navigation */}
      <div
        style={{
          display: 'flex',
          gap: '8px',
          borderBottom: '1px solid #E2E8F0',
          marginBottom: '24px',
          overflowX: 'auto',
        }}
      >
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <Link
              key={tab.id}
              to={tab.path}
              style={{
                padding: '10px 16px',
                fontSize: '14px',
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'var(--accent-primary)' : '#64748B',
                borderBottom: isActive ? '2px solid var(--accent-primary)' : '2px solid transparent',
                textDecoration: 'none',
                whiteSpace: 'nowrap',
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {tab.label}
                {tab.isSkipped && (
                  <span style={{ fontSize: '10px', backgroundColor: isActive ? 'var(--accent-light)' : '#F1F5F9', color: isActive ? 'var(--accent-hover)' : '#64748B', padding: '2px 6px', borderRadius: '4px', fontWeight: 700 }}>
                    SKIPPED
                  </span>
                )}
              </div>
            </Link>
          );
        })}
      </div>

      {/* Active Tab View Content */}
      {activeTab === 'overview' && (
        <div>
          {/* Why Blocked Panel (if status is BLOCKED) */}
          <WhyBlockedCard report={report} />

          {/* Top KPI Grid */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '24px' }}>
            <MetricCard
              label="Initial Validation"
              value={initialValStatus}
              status={initialValStatus === 'PASS' ? 'success' : initialValStatus === 'FAIL' ? 'fail' : 'neutral'}
            />
            <MetricCard
              label="Discrepancies"
              value={discrepancyCount}
              status={discrepancyCount === 0 ? 'success' : 'warn'}
            />
            <MetricCard
              label="Affected Records"
              value={affectedRecords}
              subtitle="Behavioral drift count"
              status={affectedRecords === 0 ? 'success' : 'warn'}
            />
            <MetricCard
              label="Repair Status"
              value={repairStatus}
              status={repairStatus === 'VERIFIED' ? 'success' : 'neutral'}
            />
            <MetricCard
              label="Assurance Score"
              value={report.score && report.score.evidence_score !== null && report.score.evidence_score !== undefined ? `${report.score.evidence_score.toFixed(1)} / 100` : 'N/A'}
              status={report.score && report.score.evidence_score !== null && report.score.evidence_score !== undefined ? 'success' : 'neutral'}
            />
            <MetricCard
              label="Evidence Coverage"
              value={report.score && report.score.evidence_coverage !== null && report.score.evidence_coverage !== undefined ? `${report.score.evidence_coverage.toFixed(0)}%` : 'N/A'}
              subtitle="Evaluated scope"
              status="neutral"
            />
          </div>

          {/* Overview Details Panel */}
          <div className="card-panel">
            <h3 style={{ marginBottom: '12px' }}>EXECUTIVE DECISION SUMMARY</h3>
            <div style={{ fontSize: '15px', fontWeight: 600, color: '#0F172A', marginBottom: '8px' }}>
              Final Decision: <StatusBadge status={report.final_status} />
            </div>
            <p style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
              {report.decision_reason}
            </p>
          </div>
        </div>
      )}

      {activeTab === 'translation' && <TranslationView report={report} />}
      {activeTab === 'validation' && <ValidationView report={report} />}
      {activeTab === 'discrepancies' && <DiscrepanciesView report={report} />}
      {activeTab === 'diagnosis' && <DiagnosisView report={report} />}
      {activeTab === 'repair' && <RepairView report={report} />}
      {activeTab === 'verification' && <VerificationView report={report} />}
      {activeTab === 'assurance' && <AssuranceView report={report} />}
      {activeTab === 'lineage' && <LineageView report={report} />}
    </div>
  );
};
