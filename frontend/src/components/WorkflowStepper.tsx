import React from 'react';
import type { MigrationState } from '../types/migration';

interface WorkflowStepperProps {
  currentState: MigrationState;
}

interface StepItem {
  id: string;
  label: string;
  states: MigrationState[];
}

const STEPS: StepItem[] = [
  { id: 'ANALYZE', label: 'Analyze', states: ['CREATED', 'ANALYZING'] },
  { id: 'TRANSLATE', label: 'Translate', states: ['TRANSLATING'] },
  { id: 'EXECUTE', label: 'Execute', states: ['EXECUTING'] },
  { id: 'VALIDATE', label: 'Validate', states: ['VALIDATING', 'DISCREPANCIES_FOUND'] },
  { id: 'DIAGNOSE', label: 'Diagnose', states: ['DIAGNOSING'] },
  { id: 'REPAIR', label: 'Repair', states: ['REPAIR_PROPOSED'] },
  { id: 'VERIFY', label: 'Verify', states: ['REPAIR_VERIFYING'] },
  { id: 'ASSURE', label: 'Assure', states: ['VERIFIED', 'BLOCKED', 'FAILED', 'ERROR'] },
];

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({ currentState }) => {
  const activeStepIndex = STEPS.findIndex((s) => s.states.includes(currentState));

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        backgroundColor: '#FFFFFF',
        border: '1px solid #E2E8F0',
        borderRadius: '8px',
        padding: '16px 24px',
        marginBottom: '24px',
        overflowX: 'auto',
      }}
    >
      {STEPS.map((step, idx) => {
        const isCompleted = activeStepIndex > idx || currentState === 'VERIFIED';
        const isCurrent = activeStepIndex === idx && currentState !== 'VERIFIED';
        const isBlocked = currentState === 'BLOCKED' && idx === activeStepIndex;

        let circleBg = '#E2E8F0';
        let circleColor = '#64748B';
        let labelColor = '#64748B';

        if (isCompleted) {
          circleBg = '#DCFCE7';
          circleColor = '#15803D';
          labelColor = '#0F172A';
        } else if (isCurrent) {
          circleBg = '#2563EB';
          circleColor = '#FFFFFF';
          labelColor = '#2563EB';
        } else if (isBlocked) {
          circleBg = '#FEF3C7';
          circleColor = '#D97706';
          labelColor = '#D97706';
        }

        return (
          <React.Fragment key={step.id}>
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', minWidth: '70px' }}>
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
                  fontSize: '12px',
                  fontWeight: 700,
                  marginBottom: '6px',
                }}
              >
                {isCompleted ? '✓' : idx + 1}
              </div>
              <span style={{ fontSize: '12px', fontWeight: isCurrent ? 700 : 500, color: labelColor }}>
                {step.label}
              </span>
            </div>

            {idx < STEPS.length - 1 && (
              <div
                style={{
                  flex: 1,
                  height: '2px',
                  backgroundColor: isCompleted ? '#22C55E' : '#E2E8F0',
                  margin: '0 8px',
                  marginTop: '-16px',
                }}
              />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};
