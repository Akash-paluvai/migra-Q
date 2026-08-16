import { fetchApi } from './client';
import type {
  MigrationAssuranceReport,
  MigrationRecord,
  MigrationRunResponse,
  MigrationStateEvent,
} from '../types/migration';

export async function listMigrations(): Promise<MigrationRecord[]> {
  return fetchApi<MigrationRecord[]>('/api/v1/migrations');
}

export async function getMigration(migrationId: string): Promise<MigrationRecord> {
  return fetchApi<MigrationRecord>(`/api/v1/migrations/${migrationId}`);
}

export async function getFlagshipMigration(): Promise<MigrationRecord> {
  return fetchApi<MigrationRecord>('/api/v1/migrations/flagship');
}

export async function runMigration(data: {
  source_sql: string;
  source_dialect?: string;
  target_dialect?: string;
  dataset_id?: string;
}): Promise<MigrationRunResponse> {
  return fetchApi<MigrationRunResponse>('/api/v1/migrations/run', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function getAssuranceReport(migrationId: string): Promise<MigrationAssuranceReport> {
  return fetchApi<MigrationAssuranceReport>(`/api/v1/migrations/${migrationId}/assurance`);
}

export async function getMigrationEvents(migrationId: string): Promise<MigrationStateEvent[]> {
  return fetchApi<MigrationStateEvent[]>(`/api/v1/migrations/${migrationId}/events`);
}

export async function getMigrationArtifacts(migrationId: string): Promise<Record<string, unknown>> {
  return fetchApi<Record<string, unknown>>(`/api/v1/migrations/${migrationId}/artifacts`);
}
