// 管理员类型
export interface Admin {
  id: number;
  username: string;
}

// API Key 类型
export interface ApiKey {
  id: number;
  name: string;
  created_at: string;
  updated_at?: string;
  repository_count?: number;
}

export interface ApiKeyDetail extends ApiKey {
  repositories: Repository[];
}

export interface CreateApiKeyRequest {
  name: string;
}

export interface CreateApiKeyResponse extends ApiKey {
  key_value: string; // 仅返回一次
}

export interface UpdateApiKeyRequest {
  name: string;
}

// 仓库类型
export interface Repository {
  id: number;
  owner: string;
  repo: string;
  branch: string;
  root_spec_path: string;
  has_github_token?: boolean;
  github_token_created_at?: string;
  github_token_updated_at?: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateRepositoryRequest {
  owner: string;
  repo: string;
  branch: string;
  root_spec_path?: string;
  github_token?: string;
}

export interface UpdateRepositoryRequest {
  owner?: string;
  repo?: string;
  branch?: string;
  root_spec_path?: string;
  github_token?: string;
}

export interface CreateRepositoryResponse extends Repository {
  github_token?: string; // 仅返回一次
}

// GitHub Token 管理类型
export interface SetGithubTokenRequest {
  github_token: string;
}

export interface SetGithubTokenResponse {
  id: number;
  github_token: string; // 仅返回一次
  github_token_created_at: string;
  github_token_updated_at?: string;
}

export interface VerifyGithubTokenResponse {
  valid: boolean;
  scopes?: string[];
  rate_limit_remaining?: number;
  error?: string;
}

// API 响应类型
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

export interface ApiResponse<T> {
  data: T;
  message?: string;
}

// 错误类型
export interface ApiError {
  detail: string;
  status_code?: number;
}

// 登录相关类型
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  admin: Admin;
}
