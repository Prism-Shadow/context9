import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import {
  getRepositories,
  createRepository,
  updateRepository,
  deleteRepository,
  setGithubToken,
  updateGithubToken,
  deleteGithubToken,
  verifyGithubToken,
} from '../services/repositories';
import { Table, Column } from '../components/common/Table';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { formatDate, copyToClipboard } from '../utils/helpers';
import type { Repository, CreateRepositoryRequest, UpdateRepositoryRequest } from '../utils/types';

interface RepositoryFormData {
  owner: string;
  repo: string;
  branch: string;
  root_spec_path: string;
  github_token?: string;
}

interface GithubTokenFormData {
  github_token: string;
}

export const Repositories: React.FC = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isTokenModalOpen, setIsTokenModalOpen] = useState(false);
  const [editingRepo, setEditingRepo] = useState<Repository | null>(null);
  const [tokenRepo, setTokenRepo] = useState<Repository | null>(null);
  const [newToken, setNewToken] = useState<string>('');
  const [showNewToken, setShowNewToken] = useState(false);
  const [verifyResult, setVerifyResult] = useState<any>(null);
  const [showToken, setShowToken] = useState(false);

  const {
    register: registerCreate,
    handleSubmit: handleSubmitCreate,
    formState: { errors: errorsCreate },
    reset: resetCreate,
  } = useForm<RepositoryFormData>();

  const {
    register: registerEdit,
    handleSubmit: handleSubmitEdit,
    formState: { errors: errorsEdit },
    reset: resetEdit,
  } = useForm<RepositoryFormData>();

  const {
    register: registerToken,
    handleSubmit: handleSubmitToken,
    formState: { errors: errorsToken },
    reset: resetToken,
  } = useForm<GithubTokenFormData>();

  useEffect(() => {
    loadRepositories();
  }, []);

  const loadRepositories = async () => {
    try {
      setLoading(true);
      const response = await getRepositories();
      setRepositories(response.items);
    } catch (error) {
      console.error('Failed to load repositories:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data: RepositoryFormData) => {
    try {
      const request: CreateRepositoryRequest = {
        owner: data.owner,
        repo: data.repo,
        branch: data.branch,
        root_spec_path: data.root_spec_path || 'spec.md',
        github_token: data.github_token || undefined,
      };
      const response = await createRepository(request);
      if (response.github_token) {
        setNewToken(response.github_token);
        setShowNewToken(true);
      }
      resetCreate();
      setIsCreateModalOpen(false);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || '创建失败');
    }
  };

  const handleEdit = (repo: Repository) => {
    setEditingRepo(repo);
    resetEdit({
      owner: repo.owner,
      repo: repo.repo,
      branch: repo.branch,
      root_spec_path: repo.root_spec_path,
    });
    setIsEditModalOpen(true);
  };

  const handleUpdate = async (data: RepositoryFormData) => {
    if (!editingRepo) return;
    try {
      const request: UpdateRepositoryRequest = {
        owner: data.owner,
        repo: data.repo,
        branch: data.branch,
        root_spec_path: data.root_spec_path,
        github_token: data.github_token || undefined,
      };
      const response = await updateRepository(editingRepo.id, request);
      if (response.github_token) {
        setNewToken(response.github_token);
        setShowNewToken(true);
      }
      setIsEditModalOpen(false);
      setEditingRepo(null);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || '更新失败');
    }
  };

  const handleDelete = async (repo: Repository) => {
    if (!confirm(`确定要删除仓库 "${repo.owner}/${repo.repo}" 吗？`)) return;
    try {
      await deleteRepository(repo.id);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || '删除失败');
    }
  };

  const handleManageToken = (repo: Repository) => {
    setTokenRepo(repo);
    resetToken();
    setVerifyResult(null);
    setIsTokenModalOpen(true);
  };

  const handleSetToken = async (data: GithubTokenFormData) => {
    if (!tokenRepo) return;
    try {
      const response = tokenRepo.has_github_token
        ? await updateGithubToken(tokenRepo.id, data.github_token)
        : await setGithubToken(tokenRepo.id, data.github_token);
      setNewToken(response.github_token);
      setShowNewToken(true);
      resetToken();
      setVerifyResult(null);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || '设置失败');
    }
  };

  const handleDeleteToken = async () => {
    if (!tokenRepo) return;
    if (!confirm('确定要删除 GitHub Token 吗？')) return;
    try {
      await deleteGithubToken(tokenRepo.id);
      setIsTokenModalOpen(false);
      setTokenRepo(null);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || '删除失败');
    }
  };

  const handleVerifyToken = async () => {
    if (!tokenRepo) return;
    try {
      const result = await verifyGithubToken(tokenRepo.id);
      setVerifyResult(result);
    } catch (error: any) {
      setVerifyResult({
        valid: false,
        error: error.response?.data?.detail || '验证失败',
      });
    }
  };

  const columns: Column<Repository>[] = [
    { key: 'owner', header: 'Owner' },
    { key: 'repo', header: 'Repo' },
    { key: 'branch', header: 'Branch' },
    { key: 'root_spec_path', header: 'Root Spec Path' },
    {
      key: 'has_github_token',
      header: 'GitHub Token',
      render: (item) => (item.has_github_token ? '已配置' : '未配置'),
    },
    {
      key: 'created_at',
      header: '创建时间',
      render: (item) => formatDate(item.created_at),
    },
  ];

  if (loading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">仓库管理</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>创建仓库</Button>
      </div>

      {showNewToken && newToken && (
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-800 mb-1">
                GitHub Token 已设置，请妥善保存（仅显示一次）：
              </p>
              <code className="text-sm text-yellow-900 bg-yellow-100 px-2 py-1 rounded">
                {newToken}
              </code>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  copyToClipboard(newToken);
                  alert('已复制到剪贴板');
                }}
              >
                复制
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setShowNewToken(false);
                  setNewToken('');
                }}
              >
                关闭
              </Button>
            </div>
          </div>
        </div>
      )}

      <Table
        data={repositories}
        columns={columns}
        onEdit={handleEdit}
        onDelete={handleDelete}
        actions={(item) => (
          <button
            onClick={() => handleManageToken(item)}
            className="text-primary-600 hover:text-primary-900"
          >
            管理 Token
          </button>
        )}
      />

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="创建仓库"
      >
        <form onSubmit={handleSubmitCreate(handleCreate)} className="space-y-4">
          <Input
            label="Owner"
            {...registerCreate('owner', { required: 'Owner 是必填项' })}
            error={errorsCreate.owner?.message}
          />
          <Input
            label="Repo"
            {...registerCreate('repo', { required: 'Repo 是必填项' })}
            error={errorsCreate.repo?.message}
          />
          <Input
            label="Branch"
            {...registerCreate('branch', { required: 'Branch 是必填项' })}
            error={errorsCreate.branch?.message}
          />
          <Input
            label="Root Spec Path"
            {...registerCreate('root_spec_path')}
            placeholder="spec.md"
            error={errorsCreate.root_spec_path?.message}
          />
          <Input
            label="GitHub Token (可选)"
            type={showToken ? 'text' : 'password'}
            {...registerCreate('github_token')}
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            error={errorsCreate.github_token?.message}
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              {showToken ? '隐藏' : '显示'} Token
            </button>
          </div>
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreateModalOpen(false)}
            >
              取消
            </Button>
            <Button type="submit" variant="primary">
              创建
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingRepo(null);
        }}
        title="编辑仓库"
      >
        <form onSubmit={handleSubmitEdit(handleUpdate)} className="space-y-4">
          <Input
            label="Owner"
            {...registerEdit('owner', { required: 'Owner 是必填项' })}
            error={errorsEdit.owner?.message}
          />
          <Input
            label="Repo"
            {...registerEdit('repo', { required: 'Repo 是必填项' })}
            error={errorsEdit.repo?.message}
          />
          <Input
            label="Branch"
            {...registerEdit('branch', { required: 'Branch 是必填项' })}
            error={errorsEdit.branch?.message}
          />
          <Input
            label="Root Spec Path"
            {...registerEdit('root_spec_path')}
            error={errorsEdit.root_spec_path?.message}
          />
          <Input
            label="GitHub Token (可选，留空不更新)"
            type={showToken ? 'text' : 'password'}
            {...registerEdit('github_token')}
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            error={errorsEdit.github_token?.message}
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              {showToken ? '隐藏' : '显示'} Token
            </button>
          </div>
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsEditModalOpen(false);
                setEditingRepo(null);
              }}
            >
              取消
            </Button>
            <Button type="submit" variant="primary">
              保存
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={isTokenModalOpen}
        onClose={() => {
          setIsTokenModalOpen(false);
          setTokenRepo(null);
          setVerifyResult(null);
        }}
        title={`管理 GitHub Token - ${tokenRepo?.owner}/${tokenRepo?.repo}`}
      >
        <form onSubmit={handleSubmitToken(handleSetToken)} className="space-y-4">
          <Input
            label="GitHub Token"
            type={showToken ? 'text' : 'password'}
            {...registerToken('github_token', {
              required: tokenRepo?.has_github_token ? false : 'GitHub Token 是必填项',
            })}
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            error={errorsToken.github_token?.message}
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="text-sm text-gray-600 hover:text-gray-800"
            >
              {showToken ? '隐藏' : '显示'} Token
            </button>
            {tokenRepo?.has_github_token && (
              <>
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={handleVerifyToken}
                >
                  验证 Token
                </Button>
                <Button
                  type="button"
                  variant="danger"
                  size="sm"
                  onClick={handleDeleteToken}
                >
                  删除 Token
                </Button>
              </>
            )}
          </div>
          {verifyResult && (
            <div
              className={`p-3 rounded ${
                verifyResult.valid
                  ? 'bg-green-50 text-green-700 border border-green-200'
                  : 'bg-red-50 text-red-700 border border-red-200'
              }`}
            >
              {verifyResult.valid ? (
                <div>
                  <p>✓ Token 有效</p>
                  {verifyResult.scopes && (
                    <p className="text-xs mt-1">
                      权限范围: {verifyResult.scopes.join(', ')}
                    </p>
                  )}
                  {verifyResult.rate_limit_remaining !== undefined && (
                    <p className="text-xs mt-1">
                      剩余请求数: {verifyResult.rate_limit_remaining}
                    </p>
                  )}
                </div>
              ) : (
                <p>✗ Token 无效: {verifyResult.error}</p>
              )}
            </div>
          )}
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsTokenModalOpen(false);
                setTokenRepo(null);
                setVerifyResult(null);
              }}
            >
              关闭
            </Button>
            <Button type="submit" variant="primary">
              {tokenRepo?.has_github_token ? '更新 Token' : '设置 Token'}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
