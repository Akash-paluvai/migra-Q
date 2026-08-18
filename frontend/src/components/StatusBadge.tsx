import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, MinusCircle, Clock } from 'lucide-react';
import type { MigrationFinalStatus, MigrationState } from '../types/migration';

interface StatusBadgeProps {
  status: MigrationFinalStatus | MigrationState | string;
  label?: string;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, label }) => {
  const displayLabel = label || status.replace(/_/g, ' ');

  let styleClass = 'status-info';
  let icon = <Clock size={14} />;

  switch (status) {
    case 'VERIFIED':
    case 'SUCCESS':
    case 'PASS':
    case 'DIRECT_PASS':
    case 'REPAIRED_PASS':
      styleClass = 'status-verified';
      icon = <CheckCircle2 size={14} />;
      break;

    case 'BLOCKED':
    case 'DISCREPANCIES_FOUND':
    case 'WARN':
      styleClass = 'status-warn';
      icon = <AlertTriangle size={14} />;
      break;

    case 'BLOCKED_PROVIDER_LIMIT':
      styleClass = 'status-provider-limit';
      icon = <AlertTriangle size={14} />;
      break;

    case 'FAILED':
    case 'FAIL':
    case 'ERROR':
    case 'REJECTED':
      styleClass = 'status-fail';
      icon = <XCircle size={14} />;
      break;

    case 'NOT_APPLICABLE':
    case 'SKIPPED':
      styleClass = 'status-na';
      icon = <MinusCircle size={14} />;
      break;

    default:
      styleClass = 'status-info';
      icon = <Clock size={14} />;
      break;
  }

  return (
    <span className={`status-badge ${styleClass}`} aria-label={`Status: ${displayLabel}`}>
      {icon}
      <span>{displayLabel}</span>
    </span>
  );
};
