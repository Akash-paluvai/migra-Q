import { apiClient } from './client';
import {
  DatasetDetail,
  DatasetPreviewResponse,
  DatasetSummary,
  DatasetTableSummary,
} from '../types/dataset';

export async function listDatasets(): Promise<DatasetSummary[]> {
  const { data } = await apiClient.get<DatasetSummary[]>('/api/v1/datasets');
  return data;
}

export async function getDataset(datasetId: string): Promise<DatasetDetail> {
  const { data } = await apiClient.get<DatasetDetail>(`/api/v1/datasets/${datasetId}`);
  return data;
}

export async function getDatasetSchema(datasetId: string): Promise<DatasetTableSummary[]> {
  const { data } = await apiClient.get<DatasetTableSummary[]>(`/api/v1/datasets/${datasetId}/schema`);
  return data;
}

export async function getDatasetPreview(
  datasetId: string,
  table?: string,
  limit: number = 100
): Promise<DatasetPreviewResponse> {
  const { data } = await apiClient.get<DatasetPreviewResponse>(`/api/v1/datasets/${datasetId}/preview`, {
    params: { table, limit },
  });
  return data;
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

  const { data } = await apiClient.post<DatasetDetail>('/api/v1/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return data;
}

export async function deleteDataset(datasetId: string): Promise<{ status: string }> {
  const { data } = await apiClient.delete<{ status: string }>(`/api/v1/datasets/${datasetId}`);
  return data;
}
