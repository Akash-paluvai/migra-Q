import React from 'react';
import type { MigrationAssuranceReport, MigrationState } from '../types/migration';

export type StepState =
  | 'NOT_STARTED'
  | 'RUNNING'
  | 'SUCCESS'
  | 'FAILED'
  | 'BLOCKED'
  | 'NOT_RUN'
  | 'NOT_REQUIRED'
  | 'NOT_APPLICABLE';

interface WorkflowStepperProps {
  currentState: MigrationState;
  report?: MigrationAssuranceReport | null;
}

interface StepDefinition {
  id: string;
  label: string;
  getStatus: (currentState: MigrationState, report?: MigrationAssuranceReport | null) => {
    state: StepState;
    badgeText?: string;
  };
}

const STEP_DEFINITIONS: StepDefinition[] = [
  {
    id: 'ANALYZE',
    label: 'Analyze',
    getStatus: () => ({ state: 'SUCCESS' }),
  },
  {
    id: 'TRANSLATE',
    label: 'Translate',
    getStatus: (curState, rep) => {
      if (curState === 'TRANSLATING') return { state: 'RUNNING' };
      if (!rep || !rep.translation_summary) return { state: 'NOT_STARTED' };
      const status = rep.translation_summary.status?.toUpperCase();
      if (status === 'SUCCESS') return { state: 'SUCCESS' };
      return { state: 'FAILED', badgeText: status || 'FAILED' };
    },
  },
  {
    id: 'EXECUTE',
    label: 'Execute',
    getStatus: (curState, rep) => {
      if (curState === 'EXECUTING') return { state: 'RUNNING' };
      if (!rep || !rep.translation_summary || rep.translation_summary.status !== 'SUCCESS') {
        return { state: 'NOT_RUN', badgeText: 'NOT RUN' };
      }
      if (!rep.execution_summary) return { state: 'NOT_RUN', badgeText: 'NOT RUN' };
      const srcOk = rep.execution_summary.source_status === 'SUCCESS';
      const tgtOk = rep.execution_summary.target_status === 'SUCCESS';
      if (srcOk && tgtOk) return { state: 'SUCCESS' };
      return { state: 'FAILED', badgeText: 'FAILED' };
    },
  },
  {
    id: 'VALIDATE',
    label: 'Validate',
    getStatus: (curState, rep) => {
      if (curState === 'VALIDATING') return { state: 'RUNNING' };
      if (!rep || !rep.execution_summary || rep.execution_summary.target_status !== 'SUCCESS') {
        return { state: 'NOT_RUN', badgeText: 'NOT RUN' };
      }
      if (!rep.validation_summary) return { state: 'NOT_RUN', badgeText: 'NOT RUN' };
      if (rep.validation_summary.overall_status === 'PASS') return { state: 'SUCCESS' };
      return { state: 'FAILED', badgeText: 'DISCREPANCIES' };
    },
  },
  {
    id: 'DIAGNOSE',
    label: 'Diagnose',
    getStatus: (curState, rep) => {
      if (curState === 'DIAGNOSING') return { state: 'RUNNING' };
      if (!rep || !rep.validation_summary) return { state: 'NOT_RUN', badgeText: 'NOT RUN' };
      if (rep.validation_summary.overall_status === 'PASS') {
        return { state: 'NOT_REQUIRED', badgeText: 'NOT REQ' };
      }
      if (rep.discrepancy_summary && rep.discrepancy_summary.discrepancy_count > 0) {
        return { state: 'SUCCESS' };
      }
      return { state: 'NOT_REQUIRED', badgeText: 'NOT REQ' };
    },
  },
  {
    id: 'REPAIR',
    label: 'Repair',
    getStatus: (curState, rep) => {
      if (curState === 'REPAIR_PROPOSED') return { state: 'RUNNING' };
      if (!rep || !rep.validation_summary) return { state: 'NOT_APPLICABLE', badgeText: 'N/A' };
      if (rep.validation_summary.overall_status === 'PASS') {
        return { state: 'NOT_REQUIRED', badgeText: 'NOT REQ' };
      }
      if (rep.repair_summary && rep.repair_summary.repair_id) {
        return { state: 'SUCCESS' };
      }
      return { state: 'NOT_APPLICABLE', badgeText: 'N/A' };
    },
  },
  {
    id: 'VERIFY',
    label: 'Verify',
    getStatus: (curState, rep) => {
      if (curState === 'REPAIR_VERIFYING') return { state: 'RUNNING' };
      if (!rep || !rep.validation_summary) return { state: 'NOT_APPLICABLE', badgeText: 'N/A' };
      if (rep.validation_summary.overall_status === 'PASS') {
        return { state: 'NOT_REQUIRED', badgeText: 'NOT REQ' };
      }
      if (!rep.repair_summary || !rep.repair_summary.repair_id) {
        return { state: 'NOT_APPLICABLE', badgeText: 'N/A' };
      }
      if (rep.verification_summary?.status === 'VERIFIED') {
        return { state: 'SUCCESS' };
      }
      if (rep.verification_summary?.status === 'FAILED') {
        return { state: 'FAILED', badgeText: 'FAILED' };
      }
      return { state: 'NOT_APPLICABLE', badgeText: 'N/A' };
    },
  },
  {
    id: 'ASSURE',
    label: 'Assure',
    getStatus: (_curState, rep) => {
      if (!rep) return { state: 'NOT_STARTED' };
      const finalStatus = rep.final_status?.toUpperCase();
      if (finalStatus === 'VERIFIED') return { state: 'SUCCESS', badgeText: 'VERIFIED' };
      if (finalStatus === 'BLOCKED') return { state: 'BLOCKED', badgeText: 'BLOCKED' };
      if (finalStatus === 'FAILED' || finalStatus === 'ERROR') return { state: 'FAILED', badgeText: 'FAILED' };
      return { state: 'RUNNING' };
    },
  },
];

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({ currentState, report }) => {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: '8px',
        padding: '16px 20px',
        marginBottom: '24px',
        overflowX: 'auto',
      }}
    >
      {STEP_DEFINITIONS.map((step, idx) => {
        const { state, badgeText } = step.getStatus(currentState, report);

        let circleBg = '#F1F5F9';
        let circleColor = '#64748B';
        let circleContent: React.ReactNode = idx + 1;
        let labelColor = '#64748B';
        let badgeBg: string | undefined;
        let badgeColor: string | undefined;

        if (state === 'SUCCESS') {
          circleBg = '#DCFCE7';
          circleColor = '#15803D';
          circleContent = '✓';
          labelColor = '#0F172A';
        } else if (state === 'RUNNING') {
          circleBg = '#2563EB';
          circleColor = '#FFFFFF';
          circleContent = '●';
          labelColor = '#2563EB';
        } else if (state === 'FAILED') {
          circleBg = '#FEE2E2';
          circleColor = '#DC2626';
          circleContent = '✕';
          labelColor = '#DC2626';
          badgeBg = '#FEE2E2';
          badgeColor = '#DC2626';
        } else if (state === 'BLOCKED') {
          circleBg = '#FEF3C7';
          circleColor = '#D97706';
          circleContent = '!';
          labelColor = '#D97706';
          badgeBg = '#FEF3C7';
          badgeColor = '#D97706';
        } else if (state === 'NOT_REQUIRED' || state === 'NOT_APPLICABLE') {
          circleBg = '#F8FAFC';
          circleColor = '#94A3B8';
          circleContent = '–';
          labelColor = '#94A3B8';
          badgeBg = '#F1F5F9';
          badgeColor = '#64748B';
        } else if (state === 'NOT_RUN') {
          circleBg = '#F1F5F9';
          circleColor = '#94A3B8';
          circleContent = '–';
          labelColor = '#94A3B8';
          badgeBg = '#F1F5F9';
          badgeColor = '#64748B';
        }

        return (
          <React.Fragment key={step.id}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '75px' }}>
              <div
                style={{
                  width: '28px',
                  height: '28px',
                  borderRadius: '50%',
                  backgroundColor: circleBg,
                  color: circleColor,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '13px',
                  fontWeight: 700,
                  marginBottom: '6px',
                  border: state === 'FAILED' ? '1px solid #FCA5A5' : state === 'BLOCKED' ? '1px solid #FCD34D' : 'none',
                }}
              >
                {circleContent}
              </div>
              <span style={{ fontSize: '12px', fontWeight: state === 'SUCCESS' || state === 'RUNNING' ? 700 : 500, color: labelColor }}>
                {step.label}
              </span>
              {badgeText && (
                <span
                  style={{
                    fontSize: '9px',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    padding: '1px 5px',
                    borderRadius: '4px',
                    backgroundColor: badgeBg || '#F1F5F9',
                    color: badgeColor || '#64748B',
                    marginTop: '2px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {badgeText}
                </span>
              )}
            </div>

            {idx < STEP_DEFINITIONS.length - 1 && (
              <div
                style={{
                  flex: 1,
                  height: '2px',
                  backgroundColor: state === 'SUCCESS' ? '#22C55E' : '#E2E8F0',
                  margin: '0 6px',
                  marginTop: '-18px',
                }}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
