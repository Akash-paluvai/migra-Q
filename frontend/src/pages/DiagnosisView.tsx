import React, { useState, useEffect } from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { HelpCircle } from 'lucide-react';
import { fetchApi } from '../api/client';
import { SkippedStageCard } from '../components/SkippedStageCard';

interface DiagnosisViewProps {
  report: MigrationAssuranceReport;
}

export const DiagnosisView: React.FC<DiagnosisViewProps> = ({ report }) => {
  const summary = report.diagnosis_summary;
  const discSummary = report.discrepancy_summary;

  const [diagnosisData, setDiagnosisData] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    let isMounted = true;
    async function loadDiagnosis() {
      const diagnosisId = report.lineage?.diagnosis_id || summary?.diagnosis_id;
      if (!diagnosisId) return;

      setLoading(true);
      try {
        const rawRes = await fetchApi<any>(`/api/v1/ai-diagnoses/${diagnosisId}`);
        if (isMounted) {
          setDiagnosisData(rawRes);
        }
      } catch (err) {
        console.error('Failed to load full AI diagnosis artifact', err);
      } finally {
        if (isMounted) setLoading(false);
      }
    }

    loadDiagnosis();
    return () => { isMounted = false; };
  }, [report]);

  // Case 1: Translation or Execution failed before validation
  if (report.final_status === 'FAILED' && (!summary || !summary.diagnosis_id)) {
    return (
      <div className="card-panel" style={{ padding: '32px', textAlign: 'center' }}>
        <h3 style={{ color: '#64748B', marginBottom: '8px' }}>Diagnosis Not Applicable</h3>
        <p style={{ color: '#94A3B8', fontSize: '14px', maxWidth: '500px', margin: '0 auto' }}>
          AI Diagnosis was NOT RUN because upstream translation or execution failed.
        </p>
      </div>
    );
  }

  // Case 2: Validation passed with 0 discrepancies
  const isPassWithoutDiscrepancies = report.validation_summary?.overall_status === 'PASS' && (!discSummary || discSummary.discrepancy_count === 0);
  
  if (isPassWithoutDiscrepancies || summary?.status === 'NOT_REQUIRED') {
    return (
      <SkippedStageCard
        title="AI DIAGNOSIS NOT REQUIRED"
        stageName="Diagnosis"
        description="Semantic validation completed successfully. No discrepancies were detected, so AI diagnosis was intentionally not invoked."
        reason="No semantic drift was detected during deterministic source-vs-target validation. 100% of rows matched identically."
        upstreamLink={`/migrations/${report.migration_id}/validation`}
        upstreamLinkLabel="View Validation Evidence"
        metrics={[
          { label: 'Discrepancies', value: 0 },
          { label: 'Validation Status', value: report.validation_summary?.overall_status || 'PASS' },
          { label: 'Diagnosis', value: 'SKIPPED' },
          { label: 'Repair', value: 'SKIPPED' },
          { label: 'Verification', value: 'SKIPPED' }
        ]}
      />
    );
  }

  // Case 3: Validation found discrepancies but Diagnosis hasn't run yet
  const isPending = (!summary || !summary.diagnosis_id) && report.final_status !== 'FAILED';
  
  if (isPending) {
    return (
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: '#D97706' }}>
          <HelpCircle size={24} />
          <div>
            <h3>AI DIAGNOSIS PENDING</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Diagnosis will run after semantic validation detects a repairable discrepancy.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const observedChange = diagnosisData?.diagnosis?.observed_behavior_change 
    || summary?.observed_change 
    || 'Behavioral mismatch detected between source and target query outputs.';
    
  const likelyMechanism = diagnosisData?.diagnosis?.likely_mechanism 
    || 'Mechanism details not available in Phase 9 summary.';
    
  const possibleCause = diagnosisData?.diagnosis?.grounded_claims?.[0]?.claim 
    || (summary?.status ? `Diagnosis status: ${summary.status}` : 'Cause details require full AI diagnosis artifact.');
    
  const uncertainty = diagnosisData?.diagnosis?.uncertainty_statement 
    || 'Uncertainty assessment requires full AI diagnosis artifact. Summary provides observed change and confidence only.';

  const verificationStatus = report.verification_summary?.status || (report.repair_summary?.repair_id ? 'PENDING' : 'SKIPPED');

  return (
    <div className="card-panel" style={{ padding: 0, overflow: 'hidden' }}>
      {/* Header */}
      <div style={{ padding: '24px', borderBottom: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: 'var(--bg-primary)', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', color: 'var(--accent-primary)' }}>
          <div style={{
            width: '24px', height: '24px', borderRadius: '50%', backgroundColor: 'var(--accent-primary)', color: '#FFF', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px'
          }}>●</div>
          <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700 }}>AI DIAGNOSIS</h3>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ padding: '4px 12px', backgroundColor: '#EFF6FF', borderRadius: '6px', fontSize: '12px', fontWeight: 600, color: '#1E40AF', border: '1px solid #BFDBFE' }}>
            DIAGNOSED
          </div>
          {summary?.diagnosis_confidence && (
            <div style={{ padding: '4px 12px', backgroundColor: '#EFF6FF', borderRadius: '6px', fontSize: '12px', fontWeight: 600, color: '#1E40AF', border: '1px solid #BFDBFE' }}>
              Confidence {(summary.diagnosis_confidence * 100).toFixed(0)}%
            </div>
          )}
        </div>
      </div>

      <div style={{ padding: '32px 24px', backgroundColor: 'var(--bg-secondary)' }}>
        <p style={{ fontSize: '15px', color: 'var(--text-primary)', lineHeight: 1.6, margin: '0 0 32px 0', maxWidth: '800px' }}>
          Deterministic validation detected a semantic discrepancy.<br />
          AI diagnosis was invoked to explain the observed behavior.
        </p>

        {loading && (
          <div style={{ padding: '32px', textAlign: 'center', color: '#64748B' }}>
            Loading canonical AI diagnosis artifact...
          </div>
        )}

        {!loading && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '32px' }}>
            {/* Context Table */}
            <div>
              <div style={{ backgroundColor: 'var(--bg-primary)', border: '1px solid var(--border-color)', borderRadius: '8px', overflow: 'hidden' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 500 }}>Discrepancies</span>
                  <span style={{ fontSize: '14px', color: 'var(--text-primary)', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{discSummary?.discrepancy_count || 1}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 500 }}>Validation</span>
                  <span style={{ fontSize: '14px', color: 'var(--text-primary)', fontWeight: 600 }}>FAIL</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 500 }}>Diagnosis</span>
                  <span style={{ fontSize: '14px', color: 'var(--text-primary)', fontWeight: 600 }}>COMPLETE</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px', borderBottom: '1px solid var(--border-color)' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 500 }}>Repair</span>
                  <span style={{ fontSize: '14px', color: 'var(--text-primary)', fontWeight: 600 }}>
                    {report.repair_summary?.repair_id ? 'PROPOSED' : 'PENDING'}
                  </span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 16px' }}>
                  <span style={{ fontSize: '14px', color: 'var(--text-secondary)', fontWeight: 500 }}>Verification</span>
                  <span style={{ fontSize: '14px', color: 'var(--text-primary)', fontWeight: 600 }}>{verificationStatus}</span>
                </div>
              </div>
            </div>

            {/* Structured Info */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <div>
                <h4 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px', letterSpacing: '0.5px' }}>
                  Observed Behavior
                </h4>
                <div style={{ height: '1px', backgroundColor: 'var(--border-color)', marginBottom: '12px' }} />
                <p style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.6, margin: 0 }}>
                  {observedChange}
                </p>
              </div>

              <div>
                <h4 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px', letterSpacing: '0.5px' }}>
                  Likely Mechanism
                </h4>
                <div style={{ height: '1px', backgroundColor: 'var(--border-color)', marginBottom: '12px' }} />
                <p style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.6, margin: 0 }}>
                  {likelyMechanism}
                </p>
              </div>

              <div>
                <h4 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px', letterSpacing: '0.5px' }}>
                  Possible Cause
                </h4>
                <div style={{ height: '1px', backgroundColor: 'var(--border-color)', marginBottom: '12px' }} />
                <p style={{ fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.6, margin: 0 }}>
                  {possibleCause}
                </p>
              </div>
              
              <div style={{ marginTop: '8px', padding: '12px 16px', backgroundColor: '#FEF3C7', border: '1px solid #FDE68A', borderRadius: '8px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: '#B45309' }}>
                  <HelpCircle size={16} />
                  <h4 style={{ fontSize: '13px', fontWeight: 700, margin: 0 }}>Uncertainty Statement</h4>
                </div>
                <p style={{ fontSize: '13px', color: '#92400E', lineHeight: 1.5, margin: 0 }}>
                  {uncertainty}
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
