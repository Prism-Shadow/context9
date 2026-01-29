import api from './api';
import type {
  Repository,
  CreateRepositoryRequest,
  UpdateRepositoryRequest,
  CreateRepositoryResponse,
  PaginatedResponse,
  SetGithubTokenResponse,
} from '../utils/types';

// Get all repositories
export const getRepositories = async (): Promise<PaginatedResponse<Repository>> => {
  const response = await api.get<PaginatedResponse<Repository>>('/api/admin/repositories');
  return response.data;
};

// Create repository
export const createRepository = async (
  data: CreateRepositoryRequest
): Promise<CreateRepositoryResponse> => {
  const response = await api.post<CreateRepositoryResponse>('/api/admin/repositories', data);
  return response.data;
};

// Update repository
export const updateRepository = async (
  id: number,
  data: UpdateRepositoryRequest
): Promise<Repository> => {
  const response = await api.patch<Repository>(`/api/admin/repositories/${id}`, data);
  return response.data;
};

// Delete repository
export const deleteRepository = async (id: number): Promise<void> => {
  await api.delete(`/api/admin/repositories/${id}`);
};

// Set repository's GitHub token
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

// Update repository's GitHub token
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

// Delete repository's GitHub token
export const deleteGithubToken = async (repositoryId: number): Promise<void> => {
  await api.delete(`/api/admin/repositories/${repositoryId}/github-token`);
};

// Export repositories (owner, repo, branch, root_spec_path, github_token)
export interface ExportRepositoryItem {
  owner: string;
  repo: string;
  branch: string;
  root_spec_path: string;
  github_token: string | null;
}

export interface ExportRepositoriesResponse {
  repositories: ExportRepositoryItem[];
}

export const exportRepositories = async (): Promise<ExportRepositoriesResponse> => {
  const response = await api.get<ExportRepositoriesResponse>(
    '/api/admin/repositories/export'
  );
  return response.data;
};

// Import repositories from exported JSON
export interface ImportRepositoriesError {
  owner: string;
  repo: string;
  branch: string;
  error: string;
}

export interface ImportRepositoriesResponse {
  created: number;
  skipped: number;
  errors: ImportRepositoriesError[];
}

export const importRepositories = async (
  data: ExportRepositoriesResponse
): Promise<ImportRepositoriesResponse> => {
  const response = await api.post<ImportRepositoriesResponse>(
    '/api/admin/repositories/import',
    data
  );
  return response.data;
};