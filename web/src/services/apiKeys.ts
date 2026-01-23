import api from './api';
import type {
  ApiKey,
  ApiKeyDetail,
  CreateApiKeyRequest,
  CreateApiKeyResponse,
  UpdateApiKeyRequest,
  PaginatedResponse,
} from '../utils/types';

// 获取所有 API Keys
export const getApiKeys = async (): Promise<PaginatedResponse<ApiKey>> => {
  const response = await api.get<PaginatedResponse<ApiKey>>('/api/admin/api-keys');
  return response.data;
};

// 创建 API Key
export const createApiKey = async (
  data: CreateApiKeyRequest
): Promise<CreateApiKeyResponse> => {
  const response = await api.post<CreateApiKeyResponse>('/api/admin/api-keys', data);
  return response.data;
};

// 删除 API Key
export const deleteApiKey = async (id: number): Promise<void> => {
  await api.delete(`/api/admin/api-keys/${id}`);
};

// 更新 API Key 名称
export const updateApiKey = async (
  id: number,
  data: UpdateApiKeyRequest
): Promise<ApiKey> => {
  const response = await api.patch<ApiKey>(`/api/admin/api-keys/${id}`, data);
  return response.data;
};

// 获取 API Key 详情（包括权限）
export const getApiKeyDetail = async (id: number): Promise<ApiKeyDetail> => {
  const response = await api.get<ApiKeyDetail>(`/api/admin/api-keys/${id}`);
  return response.data;
};

// 更新 API Key 的仓库权限
export const updateApiKeyRepositories = async (
  id: number,
  repositoryIds: number[]
): Promise<void> => {
  await api.put(`/api/admin/api-keys/${id}/repositories`, {
    repository_ids: repositoryIds,
  });
};
