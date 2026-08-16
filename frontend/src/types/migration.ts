/**
 * Strict TypeScript contracts for Phase 1–9 MIGRA-Q domain models.
 * NO `any` types allowed.
 */

export type MigrationState =
  | 'CREATED'
  | 'ANALYZING'
  | 'TRANSLATING'
  | 'EXECUTING'
  | 'VALIDATING'
  | 'DISCREPANCIES_FOUND'
  | 'DIAGNOSING'
  | 'REPAIR_PROPOSED'
  | 'REPAIR_VERIFYING'
  | 'VERIFIED'
  | 'FAILED'
  | 'BLOCKED'
  | 'ERROR';

export type MigrationFinalStatus =
  | 'VERIFIED'
  | 'BLOCKED'
  | 'FAILED'
  | 'IN_PROGRESS'
  | 'ERROR';

export type VerificationPath = 'DIRECT_PASS' | 'REPAIRED_PASS';

export type GateOutcome = 'PASS' | 'FAIL' | 'NOT_APPLICABLE';

export type ComponentStatus = 'SCORED' | 'NOT_APPLICABLE' | 'ERROR';

export interface MigrationRunResponse {
  migration_id: string;
  current_state: MigrationState;
  source_dialect: string;
  target_dialect: string;
  dataset_id: string;
  source_sql_hash: string;
}

export type AssuranceBand =
  | 'STRONG_EVIDENCE'
  | 'MINOR_CONCERNS'
  | 'SIGNIFICANT_CONCERNS'
  | 'POOR_ASSURANCE';

export interface HardGateResult {
  gate_id: string;
  gate_name: string;
  outcome: GateOutcome;
  reason: string;
}

export interface HardGateEvaluation {
  gates: HardGateResult[];
  all_passed: boolean;
  total_gates: number;
  passed_count: number;
  failed_count: number;
  not_applicable_count: number;
}

export interface ScoreComponent {
  name: string;
  weight: number;
  raw_score: number;
  weighted_score: number;
  effective_weight: number;
  status: ComponentStatus;
  source_check: string;
}

export interface AssuranceScore {
  evidence_score: number | null;
  evidence_coverage: number | null;
  band: AssuranceBand | null;
  components: ScoreComponent[];
}

export interface TranslationSummary {
  translation_id: string;
  source_dialect: string;
  target_dialect: string;
  status: string;
  candidate_validation_status?: string | null;
  source_sql_hash: string;
  source_sql?: string;
  candidate_sql?: string;
  provider: string;
  model: string;
  created_at: string;
}

export interface ExecutionSummary {
  source_execution_id: string;
  target_execution_id: string;
  source_status: string;
  target_status: string;
  source_row_count: number;
  target_row_count: number;
  dataset_id: string;
  dataset_hash: string;
}

export interface ValidationCheckSummary {
  check_name: string;
  status: string;
  score: number;
  mismatch_count: number;
}

export interface ValidationSummary {
  validation_id: string;
  overall_status: string;
  checks: ValidationCheckSummary[];
}

export interface DiscrepancySummary {
  diagnosis_id: string;
  discrepancy_count: number;
  category_counts: Record<string, number>;
  severity_counts: Record<string, number>;
  total_affected_rows: number;
}

export interface DiagnosisSummary {
  diagnosis_id: string;
  discrepancy_id: string;
  status: string;
  observed_change: string;
  diagnosis_confidence: number;
}

export interface RepairSummary {
  repair_id: string;
  status: string;
  repair_confidence: number;
  changed_region: string;
  original_sql?: string;
  proposed_sql?: string;
}

export interface VerificationSummary {
  verification_id: string;
  status: string;
  original_discrepancy_count: number;
  remaining_discrepancy_count: number;
  new_discrepancy_count: number;
  resolved_discrepancy_count: number;
  affected_rows_before: number;
  affected_rows_after: number;
  reduction_percentage: number;
}

export interface AuditLineage {
  translation_id: string;
  source_execution_id: string;
  target_execution_id: string;
  validation_id: string;
  diagnosis_id: string;
  ai_diagnosis_id: string;
  repair_id: string;
  verification_id: string;
  verification_path: VerificationPath;
  is_complete: boolean;
}

export interface MigrationRecord {
  migration_id: string;
  source_dialect: string;
  target_dialect: string;
  source_sql_hash: string;
  dataset_id: string;
  dataset_hash: string;
  created_at: string;
  updated_at: string;
  current_state: MigrationState;
  final_status: MigrationFinalStatus;
  assurance_score?: number | null;
  evidence_coverage?: number | null;
  assurance_version: string;
}

export interface MigrationStateEvent {
  migration_id: string;
  from_state: MigrationState;
  to_state: MigrationState;
  reason: string;
  artifact_id: string;
  created_at: string;
}

export interface MigrationAssuranceReport {
  migration_id: string;
  assurance_version: string;
  created_at: string;
  final_status: MigrationFinalStatus;
  decision_reason: string;
  verification_path: VerificationPath;
  score: AssuranceScore;
  gate_evaluation: HardGateEvaluation;
  translation_summary?: TranslationSummary | null;
  execution_summary?: ExecutionSummary | null;
  validation_summary?: ValidationSummary | null;
  discrepancy_summary?: DiscrepancySummary | null;
  diagnosis_summary?: DiagnosisSummary | null;
  repair_summary?: RepairSummary | null;
  verification_summary?: VerificationSummary | null;
  lineage: AuditLineage;
  limitations: string[];
  metadata: Record<string, unknown>;
}

export interface TranslationResult {
  metadata: {
    translation_id: string;
    source_dialect: string;
    target_dialect: string;
    provider: string;
    model: string;
    created_at: string;
  };
  status: string;
  candidate_validation_status?: string | null;
  response?: {
    target_sql: string;
    explanation?: string;
  } | null;
}

export interface ValidationReport {
  validation_id: string;
  source_execution_id: string;
  target_execution_id: string;
  dataset_id: string;
  overall_status: string;
  checks: Array<{
    check_name: string;
    status: string;
    score: number;
    severity: string;
    summary: string;
    mismatch_count: number;
  }>;
}

export interface DiscrepancyRecord {
  discrepancy_id: string;
  validation_id: string;
  category: string;
  severity: string;
  classification_confidence: number;
  classification_reason: string;
  affected_row_count: number;
  affected_percentage: number;
  created_at: string;
}

export interface DiscrepancyReport {
  diagnosis_id: string;
  validation_id: string;
  discrepancy_count: number;
  discrepancies: DiscrepancyRecord[];
  category_counts: Record<string, number>;
  severity_counts: Record<string, number>;
}

export interface AIDiagnosis {
  diagnosis_id: string;
  discrepancy_id: string;
  status: string;
  observed_change: string;
  likely_mechanism: string;
  possible_cause: string;
  uncertainty: string;
  diagnosis_confidence: number;
}

export interface RepairProposal {
  repair_id: string;
  discrepancy_id: string;
  status: string;
  original_sql: string;
  proposed_sql: string;
  repair_confidence: number;
  changed_region: string;
}

export interface DiagnosisAIResult {
  metadata: {
    diagnosis_id: string;
    discrepancy_id: string;
    created_at: string;
  };
  diagnosis: AIDiagnosis;
  repair_proposal: RepairProposal;
}

export interface RepairVerificationResult {
  verification_id: string;
  repair_id: string;
  discrepancy_id: string;
  status: string;
  original_discrepancy_count: number;
  remaining_discrepancy_count: number;
  new_discrepancy_count: number;
  resolved_discrepancy_count: number;
  affected_rows_before: number;
  affected_rows_after: number;
  reduction_percentage: number;
  original_target_sql: string;
  repaired_target_sql: string;
  summary: string;
  metadata: {
    dataset_hash_before: string;
    dataset_hash_after?: string | null;
    validation_config_hash_before: string;
    validation_config_hash_after?: string | null;
  };
}
