import { fetchApi } from './client';
import {
  DatasetDetail,
  DatasetPreviewResponse,
  DatasetSummary,
  DatasetTableSummary,
} from '../types/dataset';

export async function listDatasets(): Promise<DatasetSummary[]> {
  return fetchApi<DatasetSummary[]>('/api/v1/datasets');
}

export async function getDataset(datasetId: string): Promise<DatasetDetail> {
  return fetchApi<DatasetDetail>(`/api/v1/datasets/${datasetId}`);
}

export async function getDatasetSchema(datasetId: string): Promise<DatasetTableSummary[]> {
  return fetchApi<DatasetTableSummary[]>(`/api/v1/datasets/${datasetId}/schema`);
}

export async function getDatasetPreview(
  datasetId: string,
  table?: string,
  limit: number = 100
): Promise<DatasetPreviewResponse> {
  const query = new URLSearchParams();
  if (table) query.append('table', table);
  query.append('limit', String(limit));

  return fetchApi<DatasetPreviewResponse>(`/api/v1/datasets/${datasetId}/preview?${query.toString()}`);
}

export async function uploadDataset(
  file: File,
  displayName?: string,
  description?: string
): Promise<DatasetDetail> {
  const formData = new FormData();
  formData.append('file', file);
  if (displayName) formData.append('display_name', displayName);
  if (description) formData.append('description', description);

  const url = '/api/v1/datasets/upload';
  const res = await fetch(url, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const errorData = await res.json();
      if (errorData?.detail) detail = errorData.detail;
    } catch {
      // fallback
    }
    throw new Error(detail);
  }

  return (await res.json()) as DatasetDetail;
}

export async function deleteDataset(datasetId: string): Promise<{ status: string }> {
  return fetchApi<{ status: string }>(`/api/v1/datasets/${datasetId}`, {
    method: 'DELETE',
  });
}
