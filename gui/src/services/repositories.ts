import api from './api';
import type {
  Repository,
  CreateRepositoryRequest,
  UpdateRepositoryRequest,
  CreateRepositoryResponse,
  PaginatedResponse,
  SetGithubTokenRequest,
  SetGithubTokenResponse,
  VerifyGithubTokenResponse,
} from '../utils/types';

// 获取所有仓库
export const getRepositories = async (): Promise<PaginatedResponse<Repository>> => {
  const response = await api.get<PaginatedResponse<Repository>>('/api/admin/repositories');
  return response.data;
};

// 创建仓库
export const createRepository = async (
  data: CreateRepositoryRequest
): Promise<CreateRepositoryResponse> => {
  const response = await api.post<CreateRepositoryResponse>('/api/admin/repositories', data);
  return response.data;
};

// 更新仓库
export const updateRepository = async (
  id: number,
  data: UpdateRepositoryRequest
): Promise<Repository> => {
  const response = await api.patch<Repository>(`/api/admin/repositories/${id}`, data);
  return response.data;
};

// 删除仓库
export const deleteRepository = async (id: number): Promise<void> => {
  await api.delete(`/api/admin/repositories/${id}`);
};

// 设置仓库的 GitHub Token
export const setGithubToken = async (
  repositoryId: number,
  token: string
): Promise<SetGithubTokenResponse> => {
  const response = await api.put<SetGithubTokenResponse>(
    `/api/admin/repositories/${repositoryId}/github-token`,
    {
      github_token: token,
    }
  );
  return response.data;
};

// 更新仓库的 GitHub Token
export const updateGithubToken = async (
  repositoryId: number,
  token: string
): Promise<SetGithubTokenResponse> => {
  const response = await api.patch<SetGithubTokenResponse>(
    `/api/admin/repositories/${repositoryId}/github-token`,
    {
      github_token: token,
    }
  );
  return response.data;
};

// 删除仓库的 GitHub Token
export const deleteGithubToken = async (repositoryId: number): Promise<void> => {
  await api.delete(`/api/admin/repositories/${repositoryId}/github-token`);
};

// 验证仓库的 GitHub Token
export const verifyGithubToken = async (
  repositoryId: number
): Promise<VerifyGithubTokenResponse> => {
  const response = await api.post<VerifyGithubTokenResponse>(
    `/api/admin/repositories/${repositoryId}/github-token/verify`
  );
  return response.data;
};
