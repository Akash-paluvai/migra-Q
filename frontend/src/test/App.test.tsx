import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { LandingPage } from '../pages/LandingPage';
import { MigrationsPage } from '../pages/MigrationsPage';
import { HardGateTable } from '../components/HardGateTable';
import { CoverageChecklist } from '../components/CoverageChecklist';

// Mock API responses
vi.mock('../api/migrations', () => ({
  listMigrations: vi.fn().mockResolvedValue([
    {
      migration_id: 'MIG-TEST-100',
      source_dialect: 'teradata',
      target_dialect: 'bigquery',
      source_sql_hash: 'abc',
      dataset_id: 'customer_risk',
      dataset_hash: 'dh1',
      created_at: '2024-01-01',
      updated_at: '2024-01-01',
      current_state: 'VERIFIED',
      final_status: 'VERIFIED',
      assurance_score: 100.0,
      evidence_coverage: 75.0,
      assurance_version: '1.0.0',
    },
  ]),
  getMigration: vi.fn().mockResolvedValue({
    migration_id: 'MIG-TEST-100',
    source_dialect: 'teradata',
    target_dialect: 'bigquery',
    source_sql_hash: 'abc',
    dataset_id: 'customer_risk',
    dataset_hash: 'dh1',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
    current_state: 'VERIFIED',
    final_status: 'VERIFIED',
    assurance_score: 100.0,
    evidence_coverage: 75.0,
    assurance_version: '1.0.0',
  }),
  getFlagshipMigration: vi.fn().mockResolvedValue({
    migration_id: 'MIG-TEST-100',
    source_dialect: 'teradata',
    target_dialect: 'bigquery',
    source_sql_hash: 'abc',
    dataset_id: 'customer_risk',
    dataset_hash: 'dh1',
    created_at: '2024-01-01',
    updated_at: '2024-01-01',
    current_state: 'VERIFIED',
    final_status: 'VERIFIED',
    assurance_score: 100.0,
    evidence_coverage: 75.0,
    assurance_version: '1.0.0',
  }),
  getAssuranceReport: vi.fn().mockResolvedValue({
    migration_id: 'MIG-TEST-100',
    assurance_version: '1.0.0',
    created_at: '2024-01-01',
    final_status: 'VERIFIED',
    decision_reason: 'Verified by deterministic re-validation.',
    verification_path: 'REPAIRED_PASS',
    score: {
      evidence_score: 100.0,
      evidence_coverage: 75.0,
      band: 'STRONG_EVIDENCE',
      components: [
        { name: 'Schema compatibility', weight: 0.10, raw_score: 100.0, weighted_score: 13.3, effective_weight: 0.133, status: 'SCORED', source_check: 'SchemaValidator' },
        { name: 'Row reconciliation', weight: 0.30, raw_score: 100.0, weighted_score: 40.0, effective_weight: 0.40, status: 'SCORED', source_check: 'RowValidator' },
        { name: 'Aggregate reconciliation', weight: 0.20, raw_score: 100.0, weighted_score: 26.7, effective_weight: 0.267, status: 'SCORED', source_check: 'AggregateValidator' },
        { name: 'Business-rule equivalence', weight: 0.25, raw_score: 0.0, weighted_score: 0.0, effective_weight: 0.0, status: 'NOT_APPLICABLE', source_check: 'BusinessRuleValidator' },
        { name: 'Edge-case coverage', weight: 0.15, raw_score: 100.0, weighted_score: 20.0, effective_weight: 0.20, status: 'SCORED', source_check: 'EdgeCaseValidator' },
      ],
    },
    gate_evaluation: {
      gates: [
        { gate_id: 'GATE-001', gate_name: 'Source execution', outcome: 'PASS', reason: 'ok' },
        { gate_id: 'GATE-007', gate_name: 'Repair verification', outcome: 'PASS', reason: 'ok' },
      ],
      all_passed: true,
      total_gates: 11,
      passed_count: 11,
      failed_count: 0,
      not_applicable_count: 0,
    },
    translation_summary: {
      translation_id: 'TRN-100',
      source_dialect: 'teradata',
      target_dialect: 'bigquery',
      status: 'SUCCESS',
      source_sql_hash: 'abc',
      provider: 'mock',
      model: 'mock-1',
      created_at: '2024-01-01',
    },
    execution_summary: {
      source_execution_id: 'EXEC-SRC',
      target_execution_id: 'EXEC-TGT',
      source_status: 'SUCCESS',
      target_status: 'SUCCESS',
      source_row_count: 10000,
      target_row_count: 10000,
      dataset_id: 'customer_risk',
      dataset_hash: 'dh1',
    },
    validation_summary: {
      validation_id: 'VAL-100',
      overall_status: 'FAIL',
      checks: [
        { check_name: 'SchemaValidator', status: 'PASS', score: 1.0, mismatch_count: 0 },
        { check_name: 'RowValidator', status: 'FAIL', score: 0.96, mismatch_count: 9998 },
      ],
    },
    discrepancy_summary: {
      diagnosis_id: 'DIAG-100',
      discrepancy_count: 1,
      category_counts: { BOUNDARY_CONDITION: 1 },
      severity_counts: { HIGH: 1 },
      total_affected_rows: 9998,
    },
    verification_summary: {
      verification_id: 'VER-100',
      status: 'VERIFIED',
      original_discrepancy_count: 1,
      remaining_discrepancy_count: 0,
      new_discrepancy_count: 0,
      resolved_discrepancy_count: 1,
      affected_rows_before: 9998,
      affected_rows_after: 0,
      reduction_percentage: 100.0,
    },
    lineage: {
      translation_id: 'TRN-100',
      source_execution_id: 'EXEC-SRC',
      target_execution_id: 'EXEC-TGT',
      validation_id: 'VAL-100',
      diagnosis_id: 'DIAG-100',
      ai_diagnosis_id: 'AIDIAG-100',
      repair_id: 'REP-100',
      verification_id: 'VER-100',
      verification_path: 'REPAIRED_PASS',
      is_complete: true,
    },
    limitations: [],
    metadata: {},
  }),
}));

describe('Phase 10 Enterprise UI Suite', () => {
  it('renders landing page hero headline and capabilities', () => {
    render(
      <MemoryRouter>
        <LandingPage />
      </MemoryRouter>
    );
    expect(screen.getByText(/AI-Assisted Migration & Semantic Assurance/i)).toBeInTheDocument();
    expect(screen.getByText(/01/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Translate' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Verify' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Assure' })).toBeInTheDocument();
  });

  it('renders migrations list workbench', async () => {
    render(
      <MemoryRouter>
        <MigrationsPage />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText('MIGRATIONS')).toBeInTheDocument();
      expect(screen.getByText('MIG-TEST-100')).toBeInTheDocument();
    });
  });

  it('renders hard gate table with itemized PASS / NOT APPLICABLE / FAIL counts', () => {
    render(
      <HardGateTable
        evaluation={{
          gates: [
            { gate_id: 'GATE-001', gate_name: 'Source execution', outcome: 'PASS', reason: 'ok' },
            { gate_id: 'GATE-006', gate_name: 'No new discrepancies', outcome: 'NOT_APPLICABLE', reason: 'skipped' },
          ],
          all_passed: true,
          total_gates: 11,
          passed_count: 7,
          failed_count: 0,
          not_applicable_count: 4,
        }}
      />
    );
    expect(screen.getByText('7 PASS, 4 NOT APPLICABLE, 0 FAIL')).toBeInTheDocument();
  });

  it('renders coverage checklist explaining evaluated vs skipped components', () => {
    render(
      <CoverageChecklist
        coverage={75}
        components={[
          { name: 'Schema compatibility', weight: 0.1, raw_score: 100, weighted_score: 10, effective_weight: 0.133, status: 'SCORED', source_check: 's' },
          { name: 'Business-rule equivalence', weight: 0.25, raw_score: 0, weighted_score: 0, effective_weight: 0, status: 'NOT_APPLICABLE', source_check: 'b' },
        ]}
      />
    );
    expect(screen.getByText(/Evidence Coverage Breakdown \(75% evaluated\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Business-rule equivalence was SKIPPED in this validation run/i)).toBeInTheDocument();
  });
});
