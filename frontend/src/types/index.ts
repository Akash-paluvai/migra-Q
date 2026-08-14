export type Dialect = 'oracle' | 'postgres' | 'snowflake' | 'bigquery' | 'mysql' | 'sqlite' | 'duckdb';

export interface MigrationJob {
  migration_id: string;
  source_dialect: Dialect;
  target_dialect: Dialect;
  source_sql: string;
  target_sql: string;
  status: string;
}

export interface AssuranceScorecard {
  migration_id: string;
  assurance_score: number;
  gate_passed: boolean;
  score_breakdown: Record<string, number>;
  recommendations: string[];
}
