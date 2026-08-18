import React, { useEffect, useState } from 'react';
import type { MigrationAssuranceReport } from '../types/migration';
import { CodePanel } from '../components/CodePanel';
import { fetchApi } from '../api/client';
import { XCircle } from 'lucide-react';
import { format } from 'sql-formatter';

interface TranslationViewProps {
  report: MigrationAssuranceReport;
}

interface CanonicalTranslationData {
  translation_id: string;
  migration_id?: string;
  source_sql: string;
  target_sql: string;
  source_dialect: string;
  target_dialect: string;
  source_sql_hash: string;
  status: string;
  candidate_validation_status?: string | null;
  provider: string;
  model: string;
  error_message?: string | null;
  normalized_sql_hash?: string;
  transformations?: any[];
  transformation_count?: number;
}

export const TranslationView: React.FC<TranslationViewProps> = ({ report }) => {
  const [translationData, setTranslationData] = useState<CanonicalTranslationData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [lineageError, setLineageError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    async function loadCanonicalTranslation() {
      setLoading(true);
      setLineageError(null);

      const translationId = report.lineage?.translation_id || report.translation_summary?.translation_id;
      if (!translationId) {
        if (isMounted) {
          setLineageError('No translation artifact ID in audit lineage.');
          setLoading(false);
        }
        return;
      }

      let migrationRes: Record<string, any> = {};
      try {
        migrationRes = await fetchApi<Record<string, any>>(`/api/v1/migrations/${report.migration_id}`);
      } catch (err) {
        console.error("Failed to fetch migration record", err);
      }

      try {
        const rawRes = await fetchApi<Record<string, any>>(`/api/v1/translations/${translationId}`);
        const metadata = rawRes.metadata || {};
        const response = rawRes.response || {};

        const data: CanonicalTranslationData = {
          translation_id: metadata.translation_id || translationId,
          migration_id: metadata.migration_id || report.migration_id,
          source_sql: migrationRes.source_sql || '-- Error retrieving source SQL from migration record',
          target_sql: response.target_sql || report.translation_summary?.candidate_sql || '',
          source_dialect: metadata.source_dialect || report.translation_summary?.source_dialect || '',
          target_dialect: metadata.target_dialect || report.translation_summary?.target_dialect || '',
          source_sql_hash: metadata.source_sql_hash || report.translation_summary?.source_sql_hash || '',
          normalized_sql_hash: migrationRes.normalized_sql_hash || '',
          status: rawRes.status || report.translation_summary?.status || 'NOT_RUN',
          candidate_validation_status: rawRes.candidate_validation_status || report.translation_summary?.candidate_validation_status || null,
          provider: metadata.provider || report.translation_summary?.provider || 'translator',
          model: metadata.model || report.translation_summary?.model || '',
          error_message: metadata.error_message || rawRes.validation_summary || null,
          transformations: rawRes.transformations || [],
          transformation_count: rawRes.transformation_count || 0,
        };

        // Enforce universal lineage check on client side
        if (data.migration_id && data.migration_id !== report.migration_id) {
          if (isMounted) {
            setLineageError(`Artifact lineage mismatch — translation.migration_id (${data.migration_id}) != report.migration_id (${report.migration_id})`);
            setLoading(false);
          }
          return;
        }

        if (isMounted) {
          setTranslationData(data);
          setLoading(false);
        }
      } catch (err: any) {
        // Fallback to report.translation_summary if endpoint fails but verify migration_id
        if (isMounted) {
          const summary = report.translation_summary;
          if (summary) {
            setTranslationData({
              translation_id: summary.translation_id || '',
              migration_id: report.migration_id,
              source_sql: migrationRes.source_sql || summary.source_sql || '',
              target_sql: summary.candidate_sql || '',
              source_dialect: summary.source_dialect || '',
              target_dialect: summary.target_dialect || '',
              source_sql_hash: summary.source_sql_hash || '',
              normalized_sql_hash: migrationRes.normalized_sql_hash || '',
              status: summary.status || 'NOT_RUN',
              candidate_validation_status: summary.candidate_validation_status || null,
              provider: summary.provider || 'translator',
              model: summary.model || '',
              error_message: report.decision_reason || null,
              transformations: summary.transformations || [],
              transformation_count: summary.transformation_count || 0,
            });
          } else {
            setLineageError(`Failed to fetch canonical translation artifact: ${err?.message || err}`);
          }
          setLoading(false);
        }
      }
    }

    loadCanonicalTranslation();

    return () => {
      isMounted = false;
    };
  }, [report]);

  if (loading) {
    return (
      <div className="card-panel" style={{ padding: '32px', textAlign: 'center', color: '#64748B' }}>
        Loading canonical translation artifact...
      </div>
    );
  }

  if (lineageError) {
    return (
      <div className="card-panel" style={{ backgroundColor: '#FEF2F2', border: '1px solid #FECACA', padding: '24px' }}>
        <h3 style={{ color: '#991B1B', marginBottom: '8px' }}>Artifact Lineage Error</h3>
        <p style={{ color: '#7F1D1D', fontSize: '14px', fontWeight: 600 }}>
          Artifact lineage mismatch — refusing to display stale data.
        </p>
        <p style={{ color: '#B91C1C', fontSize: '12px', marginTop: '6px' }}>{lineageError}</p>
      </div>
    );
  }

  const data = translationData!;
  const isFailed = data.status !== 'SUCCESS';
  const candStatus = data.candidate_validation_status || (isFailed ? 'N/A' : 'VALID_SYNTAX');

  const transformations = data?.transformations || [];
  const actualTransformations = transformations.filter((t: any) => t.type !== 'ASSUMPTION');
  const actualAssumptions = transformations.filter((t: any) => t.type === 'ASSUMPTION');
  const numTransformations = actualTransformations.length;
  const numAssumptions = actualAssumptions.length;

  return (
    <div>
      {/* Failure Banner if Translation Failed */}
      {isFailed && (
        <div
          className="card-panel"
          style={{
            backgroundColor: '#FEF2F2',
            border: '1px solid #FECACA',
            padding: '20px',
            marginBottom: '20px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '16px',
          }}
        >
          <XCircle size={24} color="#DC2626" style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <h3 style={{ color: '#991B1B', fontSize: '16px', marginBottom: '4px' }}>
              Translation Failed ({data.status})
            </h3>
            <p style={{ color: '#7F1D1D', fontSize: '14px', lineHeight: 1.5 }}>
              {data.error_message || report.decision_reason || 'Translation could not produce valid target candidate SQL. Downstream phases have been stopped.'}
            </p>
          </div>
        </div>
      )}

      {/* Header & Status Labels */}
      <div className="card-panel">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3>AI-TRANSLATED TARGET CANDIDATE</h3>
            <p style={{ fontSize: '13px', color: '#64748B', marginTop: '2px' }}>
              Generated by dialect-aware translation model ({data.provider}{data.model ? ` / ${data.model}` : ''})
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <div
              style={{
                backgroundColor: candStatus === 'VALID_SYNTAX' ? '#F0FDF4' : '#F1F5F9',
                color: candStatus === 'VALID_SYNTAX' ? '#166534' : '#475569',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                border: candStatus === 'VALID_SYNTAX' ? '1px solid #86EFAC' : '1px solid #CBD5E1',
              }}
            >
              Candidate: {candStatus}
            </div>
            <div
              style={{
                backgroundColor: isFailed ? '#FEF2F2' : '#FFFBEB',
                color: isFailed ? '#DC2626' : '#92400E',
                padding: '6px 12px',
                borderRadius: '6px',
                fontSize: '12px',
                fontWeight: 600,
                border: isFailed ? '1px solid #FECACA' : '1px solid #FDE68A',
              }}
            >
              Semantic Status: {data.status}
            </div>
          </div>
        </div>
      </div>

      {/* Explanation Summary */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '16px', color: '#0F172A' }}>TRANSLATION SUMMARY</h3>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: '16px', marginBottom: '24px' }}>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Source</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '4px' }}>{(data.source_dialect || 'UNKNOWN').toUpperCase()}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Target</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '4px' }}>{(data.target_dialect || 'UNKNOWN').toUpperCase()}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Translation</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: isFailed ? '#DC2626' : '#059669', marginTop: '4px' }}>{data.status}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Semantic Candidate</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: candStatus === 'VALID_SYNTAX' ? '#166534' : '#475569', marginTop: '4px' }}>{candStatus}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Changes</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '4px' }}>{numTransformations} detected</div>
          </div>
        </div>

        {actualTransformations.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '8px' }}>Detected transformations</div>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#475569', fontSize: '13px', lineHeight: 1.6 }}>
              {actualTransformations.map((t: any, i: number) => (
                <li key={i} style={{ marginBottom: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{t.source} → {t.target}</div>
                  <div style={{ fontSize: '12px', color: '#64748B' }}>{t.occurrences} occurrence{t.occurrences > 1 ? 's' : ''}</div>
                  {t.explanation && (
                    <div style={{ fontSize: '12px', color: '#64748B', marginTop: '2px' }}>{t.explanation}</div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        {actualAssumptions.length > 0 && (
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '13px', fontWeight: 700, color: '#334155', marginBottom: '8px' }}>Translation assumptions &mdash; {numAssumptions}</div>
            <ul style={{ margin: 0, paddingLeft: '20px', color: '#475569', fontSize: '13px', lineHeight: 1.6 }}>
              {actualAssumptions.map((a: any, i: number) => (
                <li key={i} style={{ marginBottom: '8px' }}>
                  <div style={{ fontWeight: 600 }}>{a.target}</div>
                  {a.explanation && a.explanation !== a.target && (
                    <div style={{ fontSize: '12px', color: '#64748B', marginTop: '2px' }}>{a.explanation}</div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div style={{ backgroundColor: '#F0F9FF', padding: '16px', borderRadius: '8px', border: '1px solid #BAE6FD', marginTop: '20px' }}>
          <div style={{ fontSize: '13px', color: '#0369A1' }}>
            <span style={{ fontWeight: 700 }}>Why this matters: </span>
            {isFailed 
              ? 'Transformation details unavailable. Translation failed before a target candidate was generated.' 
              : numTransformations > 0 
                ? `${numTransformations} dialect-specific transformation${numTransformations !== 1 ? 's were' : ' was'} applied. ${numAssumptions} compatibility assumption${numAssumptions !== 1 ? 's were' : ' was'} recorded and should be considered when reviewing the translation.` 
                : 'No dialect-specific transformations were reported for this translation.'}
          </div>
        </div>
      </div>

      {/* Code Comparison Layout */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '16px' }}>SQL CODE COMPARISON</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: '20px' }}>
          <CodePanel
            title={`SOURCE SQL (${(data.source_dialect || 'SOURCE').toUpperCase()})`}
            code={data.source_sql ? (() => { try { return format(data.source_sql); } catch(e) { return data.source_sql; } })() : '-- Source SQL unavailable'}
          />

          <CodePanel
            title={`TARGET SQL CANDIDATE (${(data.target_dialect || 'TARGET').toUpperCase()})`}
            code={data.target_sql ? (() => { try { return format(data.target_sql); } catch(e) { return data.target_sql; } })() : (isFailed ? `-- Target SQL candidate unavailable due to translation failure (${data.status})` : '-- Candidate target SQL unavailable')}
          />
        </div>
      </div>

      {/* Structured Metadata Breakdown */}
      <div className="card-panel">
        <h3 style={{ marginBottom: '12px' }}>CANONICAL TRANSLATION AUDIT METADATA</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Translation ID</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '4px' }}>{data.translation_id}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Migration ID</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#0F172A', marginTop: '4px' }}>{data.migration_id || report.migration_id}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Source SQL Hash</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--accent-primary)', marginTop: '4px' }}>{data.source_sql_hash || 'SHA256'}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Normalized SQL Hash</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#059669', marginTop: '4px' }}>{data.normalized_sql_hash || 'SHA256'}</div>
          </div>
          <div style={{ backgroundColor: '#F8FAFC', padding: '14px', borderRadius: '6px', border: '1px solid #E2E8F0' }}>
            <div style={{ fontSize: '12px', fontWeight: 600, color: '#64748B' }}>Target Dialect</div>
            <div style={{ fontSize: '13px', fontWeight: 600, color: '#166534', marginTop: '4px' }}>{(data.target_dialect || 'TARGET').toUpperCase()}</div>
          </div>
        </div>
      </div>
    </div>
  );
};
