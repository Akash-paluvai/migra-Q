import React, { useState, useEffect } from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { Cpu, Search, HelpCircle, ShieldCheck } from 'lucide-react';
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

  return (
    <div>
      {/* Header */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>AI-GROUNDED DISCREPANCY DIAGNOSIS</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Diagnosis ID: {summary?.diagnosis_id || 'N/A'} | Target Discrepancy: {summary?.discrepancy_id || 'D-001'}
            </p>
          </div>
          <div style={{ backgroundColor: '#EFF6FF', color: '#1E40AF', padding: '6px 14px', borderRadius: '6px', fontSize: '13px', fontWeight: 700, border: '1px solid #BFDBFE' }}>
            Diagnosis Confidence: {summary?.diagnosis_confidence ? `${(summary.diagnosis_confidence * 100).toFixed(0)}%` : 'N/A'}
          </div>
        </div>
      </div>

      {loading && (
        <div className="card-panel" style={{ padding: '32px', textAlign: 'center', color: '#64748B' }}>
          Loading canonical AI diagnosis artifact...
        </div>
      )}

      {/* Structured AI Diagnosis Panel */}
      {!loading && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px', marginBottom: '24px' }}>
          {/* Section 1: Observed Change */}
          <div className="card-panel" style={{ marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#2563EB' }}>
              <Search size={18} />
              <h4 style={{ fontSize: '15px', fontWeight: 700 }}>Observed Behavior Change</h4>
            </div>
            <div style={{ fontSize: '14px', color: '#0F172A', fontWeight: 500, lineHeight: 1.6 }}>
              {observedChange}
            </div>
          </div>

          {/* Section 2: Likely Mechanism */}
          <div className="card-panel" style={{ marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#2563EB' }}>
              <Cpu size={18} />
              <h4 style={{ fontSize: '15px', fontWeight: 700 }}>Likely Mechanism</h4>
            </div>
            <div style={{ fontSize: '14px', color: '#0F172A', fontWeight: 500, lineHeight: 1.6 }}>
              {likelyMechanism}
            </div>
          </div>

          {/* Section 3: Possible Cause */}
          <div className="card-panel" style={{ marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#2563EB' }}>
              <ShieldCheck size={18} />
              <h4 style={{ fontSize: '15px', fontWeight: 700 }}>Possible Cause</h4>
            </div>
            <div style={{ fontSize: '14px', color: '#0F172A', fontWeight: 500, lineHeight: 1.6 }}>
              {possibleCause}
            </div>
          </div>

          {/* Section 4: Uncertainty */}
          <div className="card-panel" style={{ marginBottom: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px', color: '#D97706' }}>
              <HelpCircle size={18} />
              <h4 style={{ fontSize: '15px', fontWeight: 700, color: '#B45309' }}>Uncertainty Statement</h4>
            </div>
            <div style={{ fontSize: '14px', color: '#475569', lineHeight: 1.6 }}>
              {uncertainty}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
