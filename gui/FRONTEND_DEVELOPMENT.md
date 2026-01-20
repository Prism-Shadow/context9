# Context9 前端开发文档

## 1. 项目概述

本文档描述了 Context9 管理后台前端系统的开发规范。该系统用于管理 Context9 服务的 API Keys、仓库配置以及访问权限。

### 1.1 核心功能

1. **管理员登录**：基于会话的管理员身份验证
2. **API Key 管理**：创建、删除、命名 API Keys
3. **API Key 权限管理**：为每个 API Key 分配可访问的仓库
4. **仓库配置管理**：增加、删除、编辑仓库配置（owner, repo, branch, root_spec_path）
5. **GitHub Token 管理**：为每个仓库配置、更新、删除 GitHub Token（用于访问私有仓库），支持 Token 验证

### 1.2 技术栈

- **前端框架**：React 18+
- **构建工具**：Vite
- **样式框架**：Tailwind CSS 3
- **状态管理**：React Context API + Hooks
- **HTTP 客户端**：Axios
- **路由**：React Router v6
- **表单处理**：React Hook Form
- **UI 组件库**：Headless UI（可选，用于无障碍组件）
- **后端数据库**：SQLite（通过 FastAPI 访问）

## 2. 项目结构

```
gui/
├── public/                 # 静态资源
├── src/
│   ├── components/         # 可复用组件
│   │   ├── common/         # 通用组件（Button, Input, Modal等）
│   │   ├── layout/         # 布局组件（Header, Sidebar, Layout）
│   │   └── forms/          # 表单组件
│   ├── pages/              # 页面组件
│   │   ├── Login.tsx       # 登录页
│   │   ├── Dashboard.tsx   # 仪表盘
│   │   ├── ApiKeys.tsx     # API Key 管理页
│   │   ├── Repositories.tsx # 仓库管理页
│   │   └── ApiKeyDetail.tsx # API Key 详情/权限管理页
│   ├── services/           # API 服务层
│   │   ├── api.ts          # Axios 实例配置
│   │   ├── auth.ts         # 认证相关 API
│   │   ├── apiKeys.ts      # API Key 相关 API
│   │   └── repositories.ts # 仓库相关 API
│   ├── contexts/           # React Context
│   │   ├── AuthContext.tsx # 认证上下文
│   │   └── AppContext.tsx  # 应用全局上下文
│   ├── hooks/              # 自定义 Hooks
│   │   ├── useAuth.ts      # 认证 Hook
│   │   └── useApi.ts       # API 调用 Hook
│   ├── utils/              # 工具函数
│   │   ├── constants.ts    # 常量定义
│   │   ├── helpers.ts      # 辅助函数
│   │   └── types.ts        # TypeScript 类型定义
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # 入口文件
│   └── index.css           # 全局样式（Tailwind 导入）
├── tailwind.config.js      # Tailwind 配置
├── vite.config.ts          # Vite 配置
├── tsconfig.json           # TypeScript 配置
├── package.json            # 依赖管理
└── README.md               # 项目说明
```

## 3. 数据库设计

### 3.1 数据表结构

#### 3.1.1 管理员表 (admins)

```sql
CREATE TABLE admins (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.2 API Keys 表 (api_keys)

```sql
CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    key_hash TEXT UNIQUE NOT NULL,
    key_value TEXT UNIQUE NOT NULL,  -- 存储明文 key（仅用于首次生成时返回）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INTEGER,
    FOREIGN KEY (created_by) REFERENCES admins(id)
);
```

#### 3.1.3 仓库配置表 (repositories)

```sql
CREATE TABLE repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner TEXT NOT NULL,
    repo TEXT NOT NULL,
    branch TEXT NOT NULL,
    root_spec_path TEXT DEFAULT 'spec.md',
    github_token_encrypted TEXT,  -- 加密存储的 GitHub Token（用于访问私有仓库）
    github_token_created_at TIMESTAMP,  -- GitHub Token 创建时间
    github_token_updated_at TIMESTAMP,  -- GitHub Token 更新时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(owner, repo, branch)
);
```

**注意**：
- `github_token_encrypted` 存储加密后的 GitHub Token，使用 AES-256 加密
- 只有在创建或更新时才会返回明文 token（仅返回一次）
- 查询列表时不会返回 token 值，需要单独调用获取接口

#### 3.1.4 API Key 权限关联表 (api_key_repositories)

```sql
CREATE TABLE api_key_repositories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL,
    repository_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (api_key_id) REFERENCES api_keys(id) ON DELETE CASCADE,
    FOREIGN KEY (repository_id) REFERENCES repositories(id) ON DELETE CASCADE,
    UNIQUE(api_key_id, repository_id)
);
```

## 4. 后端 API 设计

### 4.1 认证相关 API

#### 4.1.1 管理员登录

```http
POST /api/admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "password"
}

Response 200:
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "admin": {
    "id": 1,
    "username": "admin"
  }
}
```

#### 4.1.2 获取当前管理员信息

```http
GET /api/admin/me
Authorization: Bearer {token}

Response 200:
{
  "id": 1,
  "username": "admin"
}
```

#### 4.1.3 登出

```http
POST /api/admin/logout
Authorization: Bearer {token}

Response 200:
{
  "message": "Logged out successfully"
}
```

### 4.2 API Key 管理 API

#### 4.2.1 获取所有 API Keys

```http
GET /api/admin/api-keys
Authorization: Bearer {token}

Response 200:
{
  "items": [
    {
      "id": 1,
      "name": "Production Key",
      "created_at": "2024-01-01T00:00:00Z",
      "repository_count": 3
    }
  ],
  "total": 1
}
```

#### 4.2.2 创建 API Key

```http
POST /api/admin/api-keys
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "New API Key"
}

Response 201:
{
  "id": 1,
  "name": "New API Key",
  "key_value": "ctx9_xxxxxxxxxxxxxxxxxxxx",  // 仅返回一次
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### 4.2.3 删除 API Key

```http
DELETE /api/admin/api-keys/{id}
Authorization: Bearer {token}

Response 200:
{
  "message": "API Key deleted successfully"
}
```

#### 4.2.4 更新 API Key 名称

```http
PATCH /api/admin/api-keys/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "Updated Name"
}

Response 200:
{
  "id": 1,
  "name": "Updated Name",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

#### 4.2.5 获取 API Key 详情（包括权限）

```http
GET /api/admin/api-keys/{id}
Authorization: Bearer {token}

Response 200:
{
  "id": 1,
  "name": "Production Key",
  "created_at": "2024-01-01T00:00:00Z",
  "repositories": [
    {
      "id": 1,
      "owner": "owner1",
      "repo": "repo1",
      "branch": "main",
      "root_spec_path": "spec.md"
    }
  ]
}
```

#### 4.2.6 更新 API Key 的仓库权限

```http
PUT /api/admin/api-keys/{id}/repositories
Authorization: Bearer {token}
Content-Type: application/json

{
  "repository_ids": [1, 2, 3]
}

Response 200:
{
  "message": "Permissions updated successfully"
}
```

### 4.3 仓库管理 API

#### 4.3.1 获取所有仓库

```http
GET /api/admin/repositories
Authorization: Bearer {token}

Response 200:
{
  "items": [
    {
      "id": 1,
      "owner": "owner1",
      "repo": "repo1",
      "branch": "main",
      "root_spec_path": "spec.md",
      "has_github_token": true,  -- 是否已配置 GitHub Token
      "github_token_created_at": "2024-01-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 1
}
```

**注意**：列表接口不返回 token 明文，只返回是否已配置 token 的标识。

#### 4.3.2 创建仓库

```http
POST /api/admin/repositories
Authorization: Bearer {token}
Content-Type: application/json

{
  "owner": "owner1",
  "repo": "repo1",
  "branch": "main",
  "root_spec_path": "spec.md",
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"  -- 可选，GitHub Token
}

Response 201:
{
  "id": 1,
  "owner": "owner1",
  "repo": "repo1",
  "branch": "main",
  "root_spec_path": "spec.md",
  "has_github_token": true,
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx",  -- 仅返回一次，请妥善保存
  "github_token_created_at": "2024-01-01T00:00:00Z",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**注意**：如果提供了 `github_token`，响应中会返回一次明文 token，之后将无法再次获取。

#### 4.3.3 更新仓库配置

```http
PATCH /api/admin/repositories/{id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "owner": "owner1",
  "repo": "repo1",
  "branch": "develop",
  "root_spec_path": "docs/spec.md",
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"  -- 可选，更新 GitHub Token
}

Response 200:
{
  "id": 1,
  "owner": "owner1",
  "repo": "repo1",
  "branch": "develop",
  "root_spec_path": "docs/spec.md",
  "has_github_token": true,
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx",  -- 仅当更新 token 时返回一次
  "github_token_updated_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**注意**：
- 所有字段都是可选的，只更新提供的字段
- 如果提供了 `github_token`，会更新 token 并返回一次明文

#### 4.3.4 删除仓库

```http
DELETE /api/admin/repositories/{id}
Authorization: Bearer {token}

Response 200:
{
  "message": "Repository deleted successfully"
}
```

#### 4.3.5 设置仓库的 GitHub Token

```http
PUT /api/admin/repositories/{id}/github-token
Authorization: Bearer {token}
Content-Type: application/json

{
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx"
}

Response 200:
{
  "id": 1,
  "github_token": "ghp_xxxxxxxxxxxxxxxxxxxx",  -- 仅返回一次，请妥善保存
  "github_token_created_at": "2024-01-01T00:00:00Z",
  "github_token_updated_at": "2024-01-01T00:00:00Z"
}
```

#### 4.3.6 更新仓库的 GitHub Token

```http
PATCH /api/admin/repositories/{id}/github-token
Authorization: Bearer {token}
Content-Type: application/json

{
  "github_token": "ghp_new_xxxxxxxxxxxxxxxxxxxx"
}

Response 200:
{
  "id": 1,
  "github_token": "ghp_new_xxxxxxxxxxxxxxxxxxxx",  -- 仅返回一次，请妥善保存
  "github_token_updated_at": "2024-01-01T00:00:00Z"
}
```

#### 4.3.7 删除仓库的 GitHub Token

```http
DELETE /api/admin/repositories/{id}/github-token
Authorization: Bearer {token}

Response 200:
{
  "message": "GitHub Token deleted successfully"
}
```

#### 4.3.8 验证 GitHub Token（可选）

```http
POST /api/admin/repositories/{id}/github-token/verify
Authorization: Bearer {token}

Response 200:
{
  "valid": true,
  "scopes": ["repo", "read:org"],  -- Token 的权限范围
  "rate_limit_remaining": 5000
}

Response 200 (invalid token):
{
  "valid": false,
  "error": "Invalid token"
}
```

## 5. 前端页面设计

### 5.1 登录页面 (`/login`)

**功能**：
- 管理员用户名和密码输入
- 表单验证
- 错误提示
- 登录成功后跳转到仪表盘

**UI 设计要点**：
- 居中布局
- 简洁的表单设计
- 响应式设计

### 5.2 仪表盘 (`/dashboard`)

**功能**：
- 显示系统概览统计
  - API Keys 总数
  - 仓库总数
  - 活跃 API Keys 数量
- 快速操作入口

### 5.3 API Keys 管理页面 (`/api-keys`)

**功能**：
- 显示所有 API Keys 列表
- 创建新 API Key（弹出模态框）
- 删除 API Key（带确认）
- 编辑 API Key 名称
- 查看/管理 API Key 权限（跳转到详情页）

**列表显示字段**：
- 名称
- 创建时间
- 关联仓库数量
- 操作按钮（编辑、删除、管理权限）

### 5.4 API Key 详情/权限管理页面 (`/api-keys/:id`)

**功能**：
- 显示 API Key 基本信息
- 管理该 API Key 可访问的仓库
  - 显示已关联的仓库列表
  - 多选仓库进行关联/取消关联
  - 保存权限变更

### 5.5 仓库管理页面 (`/repositories`)

**功能**：
- 显示所有仓库配置列表
- 创建新仓库配置（弹出表单模态框）
- 编辑仓库配置（弹出表单模态框）
- 删除仓库配置（带确认）
- 管理 GitHub Token：
  - 设置 GitHub Token（弹出表单）
  - 更新 GitHub Token（弹出表单）
  - 删除 GitHub Token（带确认）
  - 验证 GitHub Token（显示验证结果）

**列表显示字段**：
- Owner
- Repo
- Branch
- Root Spec Path
- GitHub Token 状态（已配置/未配置）
- 创建时间
- 操作按钮（编辑、删除、管理 Token）

**GitHub Token 管理**：
- Token 输入框（密码类型，显示/隐藏切换）
- Token 验证按钮（验证 token 是否有效）
- 设置/更新 Token 时，成功后会显示一次明文 token（带复制按钮）
- 删除 Token 需要二次确认

## 6. 核心组件设计

### 6.1 布局组件

#### 6.1.1 Layout

```tsx
// src/components/layout/Layout.tsx
interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">{children}</main>
      </div>
    </div>
  );
};
```

#### 6.1.2 Header

包含：
- Logo/标题
- 当前登录管理员信息
- 登出按钮

#### 6.1.3 Sidebar

导航菜单：
- 仪表盘
- API Keys
- 仓库管理
- 登出

### 6.2 通用组件

#### 6.2.1 Button

```tsx
// src/components/common/Button.tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}
```

#### 6.2.2 Input

```tsx
// src/components/common/Input.tsx
interface InputProps {
  type?: string;
  label?: string;
  error?: string;
  value: string;
  onChange: (value: string) => void;
}
```

#### 6.2.3 Modal

```tsx
// src/components/common/Modal.tsx
interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}
```

#### 6.2.4 Table

```tsx
// src/components/common/Table.tsx
interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  onEdit?: (item: T) => void;
  onDelete?: (item: T) => void;
}
```

### 6.3 表单组件

使用 React Hook Form 进行表单管理：

#### 6.3.1 创建 API Key 表单

```tsx
// 示例：创建 API Key 表单
import { useForm } from 'react-hook-form';

interface ApiKeyFormData {
  name: string;
}

const CreateApiKeyForm: React.FC = () => {
  const { register, handleSubmit, formState: { errors } } = useForm<ApiKeyFormData>();
  
  const onSubmit = async (data: ApiKeyFormData) => {
    // 调用 API
  };
  
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      {/* 表单字段 */}
    </form>
  );
};
```

#### 6.3.2 GitHub Token 管理表单

```tsx
// src/components/forms/GithubTokenForm.tsx
import { useForm } from 'react-hook-form';
import { useState } from 'react';
import { Button } from '../common/Button';
import { Input } from '../common/Input';

interface GithubTokenFormData {
  github_token: string;
}

interface GithubTokenFormProps {
  repositoryId: number;
  onSubmit: (token: string) => Promise<void>;
  onVerify?: () => Promise<void>;
  existingToken?: boolean;
}

export const GithubTokenForm: React.FC<GithubTokenFormProps> = ({
  repositoryId,
  onSubmit,
  onVerify,
  existingToken = false,
}) => {
  const [showToken, setShowToken] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState<{
    valid: boolean;
    scopes?: string[];
    error?: string;
  } | null>(null);

  const { register, handleSubmit, formState: { errors }, reset } = useForm<GithubTokenFormData>();

  const handleFormSubmit = async (data: GithubTokenFormData) => {
    await onSubmit(data.github_token);
    reset();
  };

  const handleVerify = async () => {
    if (!onVerify) return;
    setVerifying(true);
    try {
      const result = await onVerify();
      setVerifyResult({ valid: true, ...result });
    } catch (error: any) {
      setVerifyResult({ valid: false, error: error.message });
    } finally {
      setVerifying(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
      <div>
        <Input
          type={showToken ? 'text' : 'password'}
          label="GitHub Token"
          value={register('github_token').value || ''}
          onChange={(value) => {
            register('github_token').onChange({ target: { value } });
          }}
          error={errors.github_token?.message}
          placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
        />
        <div className="mt-2 flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowToken(!showToken)}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            {showToken ? '隐藏' : '显示'} Token
          </button>
          {existingToken && onVerify && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={handleVerify}
              disabled={verifying}
            >
              {verifying ? '验证中...' : '验证 Token'}
            </Button>
          )}
        </div>
        {verifyResult && (
          <div className={`mt-2 text-sm ${verifyResult.valid ? 'text-green-600' : 'text-red-600'}`}>
            {verifyResult.valid ? (
              <div>
                <p>✓ Token 有效</p>
                {verifyResult.scopes && (
                  <p className="text-xs text-gray-600">权限范围: {verifyResult.scopes.join(', ')}</p>
                )}
              </div>
            ) : (
              <p>✗ Token 无效: {verifyResult.error}</p>
            )}
          </div>
        )}
      </div>
      <div className="flex gap-2">
        <Button type="submit" variant="primary">
          {existingToken ? '更新 Token' : '设置 Token'}
        </Button>
      </div>
    </form>
  );
};
```

#### 6.3.3 仓库配置表单（包含 GitHub Token）

```tsx
// src/components/forms/RepositoryForm.tsx
import { useForm } from 'react-hook-form';

interface RepositoryFormData {
  owner: string;
  repo: string;
  branch: string;
  root_spec_path: string;
  github_token?: string;
}

interface RepositoryFormProps {
  initialData?: Partial<RepositoryFormData>;
  onSubmit: (data: RepositoryFormData) => Promise<void>;
}

export const RepositoryForm: React.FC<RepositoryFormProps> = ({
  initialData,
  onSubmit,
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<RepositoryFormData>({
    defaultValues: initialData,
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <Input
        label="Owner"
        {...register('owner', { required: 'Owner 是必填项' })}
        error={errors.owner?.message}
      />
      <Input
        label="Repo"
        {...register('repo', { required: 'Repo 是必填项' })}
        error={errors.repo?.message}
      />
      <Input
        label="Branch"
        {...register('branch', { required: 'Branch 是必填项' })}
        error={errors.branch?.message}
      />
      <Input
        label="Root Spec Path"
        {...register('root_spec_path')}
        placeholder="spec.md"
        error={errors.root_spec_path?.message}
      />
      <Input
        type="password"
        label="GitHub Token (可选)"
        {...register('github_token')}
        placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
        error={errors.github_token?.message}
      />
      <Button type="submit" variant="primary">
        保存
      </Button>
    </form>
  );
};
```

## 7. 状态管理

### 7.1 AuthContext

```tsx
// src/contexts/AuthContext.tsx
interface AuthContextType {
  user: Admin | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);
```

**功能**：
- 管理登录状态
- 存储 JWT token（localStorage）
- 提供登录/登出方法
- 自动刷新 token（如需要）

### 7.2 API 服务层

```tsx
// src/services/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8011',
  headers: {
    'Content-Type': 'application/json',
  },
});

// 请求拦截器：添加 token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// 响应拦截器：处理错误
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // 清除 token，跳转到登录页
      localStorage.removeItem('token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

### 7.3 仓库服务 API 示例

```tsx
// src/services/repositories.ts
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
  const response = await api.get('/api/admin/repositories');
  return response.data;
};

// 创建仓库
export const createRepository = async (
  data: CreateRepositoryRequest
): Promise<CreateRepositoryResponse> => {
  const response = await api.post('/api/admin/repositories', data);
  return response.data;
};

// 更新仓库
export const updateRepository = async (
  id: number,
  data: UpdateRepositoryRequest
): Promise<Repository> => {
  const response = await api.patch(`/api/admin/repositories/${id}`, data);
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
  const response = await api.put(`/api/admin/repositories/${repositoryId}/github-token`, {
    github_token: token,
  });
  return response.data;
};

// 更新仓库的 GitHub Token
export const updateGithubToken = async (
  repositoryId: number,
  token: string
): Promise<SetGithubTokenResponse> => {
  const response = await api.patch(`/api/admin/repositories/${repositoryId}/github-token`, {
    github_token: token,
  });
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
  const response = await api.post(`/api/admin/repositories/${repositoryId}/github-token/verify`);
  return response.data;
};
```

### 7.4 TypeScript 类型定义

```tsx
// src/utils/types.ts

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
  key_value: string;  // 仅返回一次
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
  github_token?: string;  // 仅返回一次
}

// GitHub Token 管理类型
export interface SetGithubTokenRequest {
  github_token: string;
}

export interface SetGithubTokenResponse {
  id: number;
  github_token: string;  // 仅返回一次
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
```

## 8. 路由配置

```tsx
// src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { ApiKeys } from './pages/ApiKeys';
import { ApiKeyDetail } from './pages/ApiKeyDetail';
import { Repositories } from './pages/Repositories';
import { Layout } from './components/layout/Layout';

// 受保护的路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return <div>Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return <Layout>{children}</Layout>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-keys"
          element={
            <ProtectedRoute>
              <ApiKeys />
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-keys/:id"
          element={
            <ProtectedRoute>
              <ApiKeyDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/repositories"
          element={
            <ProtectedRoute>
              <Repositories />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
```

## 9. 样式规范

### 9.1 Tailwind CSS 配置

```javascript
// tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#faf5ff',
          100: '#f3e8ff',
          500: '#a855f7',
          600: '#9333ea',
          700: '#7e22ce',
          900: '#581c87',
        },
      },
    },
  },
  plugins: [],
}
```

### 9.2 设计系统

**颜色**：
- 主色：蓝色系（primary-500, primary-600）
- 成功：绿色（green-500）
- 警告：黄色（yellow-500）
- 危险：红色（red-500）
- 中性：灰色系（gray-50 到 gray-900）

**间距**：
- 使用 Tailwind 的间距系统（4px 基准）

**字体**：
- 默认：系统字体栈
- 标题：加粗（font-bold）
- 正文：常规（font-normal）

## 10. 开发指南

### 10.1 项目初始化

```bash
# 在项目根目录下创建 gui 目录
cd /path/to/Context9
mkdir gui
cd gui

# 使用 Vite 创建 React + TypeScript 项目
npm create vite@latest . -- --template react-ts

# 安装依赖
npm install

# 安装 Tailwind CSS
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

# 安装其他依赖
npm install axios react-router-dom react-hook-form
npm install -D @types/react-router-dom
```

### 10.2 环境变量配置

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8011
```

### 10.3 开发命令

```bash
# 启动开发服务器
npm run dev

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### 10.4 代码规范

- 使用 TypeScript 进行类型检查
- 使用 ESLint 和 Prettier 进行代码格式化
- 组件使用函数式组件 + Hooks
- 遵循 React 最佳实践（组件拆分、状态提升等）

### 10.5 测试建议

- 单元测试：使用 Vitest
- 组件测试：使用 React Testing Library
- E2E 测试：使用 Playwright（可选）

## 11. 后端集成要求

### 11.1 需要新增的后端模块

1. **数据库模块** (`context9/database/`)
   - `models.py`：SQLAlchemy 模型定义
   - `database.py`：数据库连接和会话管理
   - `init_db.py`：数据库初始化脚本

2. **认证模块扩展** (`context9/auth/`)
   - `admin_auth.py`：管理员认证（JWT）
   - `password.py`：密码哈希和验证

3. **API 路由模块** (`context9/api/`)
   - `admin.py`：管理员相关路由
   - `api_keys.py`：API Key 管理路由
   - `repositories.py`：仓库管理路由

4. **依赖注入**
   - `dependencies.py`：FastAPI 依赖（获取当前用户等）

### 11.2 后端技术栈建议

- **ORM**：SQLAlchemy 或 SQLModel
- **认证**：JWT（python-jose）
- **密码哈希**：passlib[bcrypt]
- **加密**：cryptography（用于 GitHub Token 加密）
- **数据库迁移**：Alembic（可选）

### 11.2.1 GitHub Token 加密实现建议

```python
# context9/auth/encryption.py
from cryptography.fernet import Fernet
import os
import base64

# 从环境变量获取加密密钥
ENCRYPTION_KEY = os.getenv("GITHUB_TOKEN_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # 生成新密钥（仅用于开发）
    ENCRYPTION_KEY = Fernet.generate_key().decode()

def encrypt_token(token: str) -> str:
    """加密 GitHub Token"""
    f = Fernet(ENCRYPTION_KEY.encode())
    encrypted = f.encrypt(token.encode())
    return base64.b64encode(encrypted).decode()

def decrypt_token(encrypted_token: str) -> str:
    """解密 GitHub Token"""
    f = Fernet(ENCRYPTION_KEY.encode())
    encrypted = base64.b64decode(encrypted_token.encode())
    return f.decrypt(encrypted).decode()
```

**环境变量配置**：
```env
# 生产环境必须设置，使用 Fernet.generate_key() 生成
GITHUB_TOKEN_ENCRYPTION_KEY=your_base64_encoded_key_here
```

### 11.3 后端 API 路由结构

```python
# context9/server.py 中需要添加新的路由组
from fastapi import APIRouter

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

# 注册子路由
from .api import admin, api_keys, repositories

admin_router.include_router(admin.router)
admin_router.include_router(api_keys.router)
admin_router.include_router(repositories.router)

app.include_router(admin_router)
```

## 12. 安全考虑

1. **前端安全**：
   - JWT token 存储在 localStorage（考虑使用 httpOnly cookie）
   - 敏感操作需要二次确认
   - XSS 防护（React 自动转义）

2. **后端安全**：
   - 密码使用 bcrypt 哈希
   - API Key 使用安全的随机生成算法
   - JWT token 设置合理的过期时间
   - 使用 HTTPS（生产环境）

3. **API Key 生成**：
   - 使用加密安全的随机数生成器
   - 格式：`ctx9_` + 32 字符随机字符串
   - 存储时使用哈希（SHA-256）

4. **GitHub Token 安全**：
   - GitHub Token 必须加密存储（使用 AES-256 加密）
   - 加密密钥存储在环境变量中，不要提交到代码仓库
   - Token 明文仅在创建/更新时返回一次，之后无法再次获取
   - 前端显示 Token 时使用密码输入框（type="password"）
   - 提供 Token 验证功能，验证 Token 是否有效及权限范围
   - 删除 Token 需要二次确认

## 13. 部署建议

### 13.1 前端构建

```bash
npm run build
```

构建产物在 `dist/` 目录，可以：
- 使用 Nginx 提供静态文件服务
- 或集成到 FastAPI 中（使用 `StaticFiles`）

### 13.2 集成到 FastAPI

```python
from fastapi.staticfiles import StaticFiles

# 在 server.py 中添加
app.mount("/", StaticFiles(directory="gui/dist", html=True), name="static")
```

### 13.3 环境配置

- 开发环境：前后端分离，使用代理或 CORS
- 生产环境：前端构建后由 FastAPI 统一服务

## 14. 开发时间估算

- **项目初始化**：1 天
- **认证模块**：2 天
- **API Key 管理**：3 天
- **仓库管理**：2 天
- **权限管理**：2 天
- **UI/UX 优化**：2 天
- **测试和调试**：2 天

**总计**：约 14 个工作日

## 15. 参考资料

- [React 官方文档](https://react.dev)
- [Tailwind CSS 文档](https://tailwindcss.com)
- [FastAPI 文档](https://fastapi.tiangolo.com)
- [React Router 文档](https://reactrouter.com)
- [React Hook Form 文档](https://react-hook-form.com)

---

**文档版本**：v1.0  
**最后更新**：2024-01-01

