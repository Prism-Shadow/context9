import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useLocale } from '../contexts/LocaleContext';
import {
  getRepositories,
  createRepository,
  updateRepository,
  deleteRepository,
} from '../services/repositories';
import { Table, Column } from '../components/common/Table';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { formatDate, parseGitHubUrl } from '../utils/helpers';
import type { Repository, CreateRepositoryRequest, UpdateRepositoryRequest } from '../utils/types';

interface RepositoryFormData {
  owner: string;
  repo: string;
  branch: string;
  root_spec_path: string;
  github_token?: string;
}

export const Repositories: React.FC = () => {
  const { t } = useLocale();
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSyncingModalOpen, setIsSyncingModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingRepo, setEditingRepo] = useState<Repository | null>(null);
  const [showToken, setShowToken] = useState(false);
  const [githubUrl, setGithubUrl] = useState('');

  const {
    register: registerCreate,
    handleSubmit: handleSubmitCreate,
    formState: { errors: errorsCreate },
    reset: resetCreate,
    setValue: setValueCreate,
  } = useForm<RepositoryFormData>();

  const {
    register: registerEdit,
    handleSubmit: handleSubmitEdit,
    formState: { errors: errorsEdit },
    reset: resetEdit,
  } = useForm<RepositoryFormData>();

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
    setIsSyncingModalOpen(true);
    try {
      const request: CreateRepositoryRequest = {
        owner: data.owner,
        repo: data.repo,
        branch: data.branch,
        root_spec_path: data.root_spec_path || 'spec.md',
        github_token: data.github_token || undefined,
      };
      await createRepository(request);
      resetCreate();
      setGithubUrl('');
      setIsCreateModalOpen(false);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || t('repositories.createFailed'));
    } finally {
      setIsSyncingModalOpen(false);
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
      await updateRepository(editingRepo.id, request);
      setIsEditModalOpen(false);
      setEditingRepo(null);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || t('repositories.updateFailed'));
    }
  };

  const handleDelete = async (repo: Repository) => {
    if (!confirm(`${t('repositories.confirmDelete')} "${repo.owner}/${repo.repo}"?`)) return;
    try {
      await deleteRepository(repo.id);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || t('repositories.deleteFailed'));
    }
  };

  const handleParseGitHubUrl = () => {
    const parsed = parseGitHubUrl(githubUrl);
    if (!parsed) {
      alert(t('repositories.invalidGitHubUrl'));
      return;
    }

    // Set form values
    setValueCreate('owner', parsed.owner);
    setValueCreate('repo', parsed.repo);
    
    // Only set branch if it was detected
    if (parsed.branch) {
      setValueCreate('branch', parsed.branch);
    }
    
    // Only set root_spec_path if it was detected
    if (parsed.rootSpecPath) {
      setValueCreate('root_spec_path', parsed.rootSpecPath);
    }
  };

  const columns: Column<Repository>[] = [
    { key: 'owner', header: t('repositories.owner') },
    { key: 'repo', header: t('repositories.repo') },
    { key: 'branch', header: t('repositories.branch') },
    { key: 'root_spec_path', header: t('repositories.rootSpecPath') },
    {
      key: 'has_github_token',
      header: t('repositories.githubToken'),
      render: (item) => (item.has_github_token ? t('repositories.configured') : t('repositories.notConfigured')),
    },
    {
      key: 'created_at',
      header: t('repositories.createdAt'),
      render: (item) => formatDate(item.created_at),
    },
  ];

  if (loading) {
    return <div className="text-center py-8 text-gray-500 dark:text-gray-400">{t('common.loading')}</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{t('repositories.title')}</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>{t('repositories.add')}</Button>
      </div>

      <Table
        data={repositories}
        columns={columns}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => {
          setIsCreateModalOpen(false);
          setGithubUrl('');
        }}
        title={t('repositories.create')}
        closeOnOverlayClick={false}
      >
        <form onSubmit={handleSubmitCreate(handleCreate)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t('repositories.githubUrl')}
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="flex-1 px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              <Button
                type="button"
                variant="secondary"
                size="sm"
                onClick={handleParseGitHubUrl}
              >
                {t('repositories.parse')}
              </Button>
            </div>
          </div>
          <Input
            label={t('repositories.owner')}
            {...registerCreate('owner', { required: t('repositories.ownerRequired') })}
            error={errorsCreate.owner?.message}
          />
          <Input
            label={t('repositories.repo')}
            {...registerCreate('repo', { required: t('repositories.repoRequired') })}
            error={errorsCreate.repo?.message}
          />
          <Input
            label={t('repositories.branch')}
            {...registerCreate('branch', { required: t('repositories.branchRequired') })}
            error={errorsCreate.branch?.message}
          />
          <Input
            label={t('repositories.rootSpecPath')}
            {...registerCreate('root_spec_path')}
            placeholder="spec.md"
            error={errorsCreate.root_spec_path?.message}
          />
          <Input
            label={t('repositories.githubTokenOptional')}
            type={showToken ? 'text' : 'password'}
            {...registerCreate('github_token')}
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            error={errorsCreate.github_token?.message}
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            >
              {showToken ? t('repositories.hideToken') : t('repositories.showToken')} Token
            </button>
          </div>
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreateModalOpen(false)}
            >
              {t('common.cancel')}
            </Button>
            <Button type="submit" variant="primary">
              {t('common.create')}
            </Button>
          </div>
        </form>
      </Modal>

      <Modal
        isOpen={isSyncingModalOpen}
        onClose={() => {}}
        title=""
        closeOnOverlayClick={false}
        showCloseButton={false}
      >
        <div className="flex flex-col items-center justify-center py-6 gap-3">
          <svg
            className="animate-spin h-10 w-10 text-primary-600 dark:text-primary-400"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-label="Loading"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-gray-600 dark:text-gray-400">{t('repositories.syncing')}</p>
        </div>
      </Modal>

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingRepo(null);
        }}
        title={t('repositories.edit')}
      >
        <form onSubmit={handleSubmitEdit(handleUpdate)} className="space-y-4">
          <Input
            label={t('repositories.owner')}
            {...registerEdit('owner', { required: t('repositories.ownerRequired') })}
            error={errorsEdit.owner?.message}
          />
          <Input
            label={t('repositories.repo')}
            {...registerEdit('repo', { required: t('repositories.repoRequired') })}
            error={errorsEdit.repo?.message}
          />
          <Input
            label={t('repositories.branch')}
            {...registerEdit('branch', { required: t('repositories.branchRequired') })}
            error={errorsEdit.branch?.message}
          />
          <Input
            label={t('repositories.rootSpecPath')}
            {...registerEdit('root_spec_path')}
            error={errorsEdit.root_spec_path?.message}
          />
          <Input
            label={t('repositories.githubTokenUpdate')}
            type={showToken ? 'text' : 'password'}
            {...registerEdit('github_token')}
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
            error={errorsEdit.github_token?.message}
          />
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => setShowToken(!showToken)}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
            >
              {showToken ? t('repositories.hideToken') : t('repositories.showToken')} Token
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
              {t('common.cancel')}
            </Button>
            <Button type="submit" variant="primary">
              {t('common.save')}
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
