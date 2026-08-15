export interface ColumnSchema {
  name: string;
  data_type: string;
  nullable: boolean;
  ordinal_position: number;
  primary_key: boolean;
  description?: string;
  sample_values?: any[];
}

export interface DatasetTableSummary {
  table_name: string;
  row_count: number;
  columns: ColumnSchema[];
}

export interface DatasetSummary {
  dataset_id: string;
  display_name: string;
  description: string;
  source: string;
  profile: string;
  row_count_total: number;
  table_count: number;
  size_bytes: number;
  created_at: string;
  dataset_hash: string;
  schema_version: string;
  is_builtin: boolean;
  is_upload: boolean;
  status: string;
  tags: string[];
}

export interface DatasetDetail extends DatasetSummary {
  table_summaries: DatasetTableSummary[];
  manifest_path?: string;
}

export interface DatasetPreviewResponse {
  dataset_id: string;
  table_name: string;
  total_rows: number;
  returned_rows: number;
  columns: ColumnSchema[];
  rows: Record<string, any>[];
}
