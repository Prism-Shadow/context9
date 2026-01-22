import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
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
import { formatDate } from '../utils/helpers';
import type { Repository, CreateRepositoryRequest, UpdateRepositoryRequest } from '../utils/types';

interface RepositoryFormData {
  owner: string;
  repo: string;
  branch: string;
  root_spec_path: string;
  github_token?: string;
}

export const Repositories: React.FC = () => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isSyncingModalOpen, setIsSyncingModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingRepo, setEditingRepo] = useState<Repository | null>(null);
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
      setIsCreateModalOpen(false);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create');
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
      alert(error.response?.data?.detail || 'Failed to update');
    }
  };

  const handleDelete = async (repo: Repository) => {
    if (!confirm(`Are you sure you want to delete repository "${repo.owner}/${repo.repo}"?`)) return;
    try {
      await deleteRepository(repo.id);
      await loadRepositories();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete');
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
      render: (item) => (item.has_github_token ? 'Configured' : 'Not Configured'),
    },
    {
      key: 'created_at',
      header: 'Created At',
      render: (item) => formatDate(item.created_at),
    },
  ];

  if (loading) {
    return <div className="text-center py-8 text-gray-500 dark:text-gray-400">Loading...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Repository Management</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>Add Repository</Button>
      </div>

      <Table
        data={repositories}
        columns={columns}
        onEdit={handleEdit}
        onDelete={handleDelete}
      />

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create Repository"
        closeOnOverlayClick={false}
      >
        <form onSubmit={handleSubmitCreate(handleCreate)} className="space-y-4">
          <Input
            label="Owner"
            {...registerCreate('owner', { required: 'Owner is required' })}
            error={errorsCreate.owner?.message}
          />
          <Input
            label="Repo"
            {...registerCreate('repo', { required: 'Repo is required' })}
            error={errorsCreate.repo?.message}
          />
          <Input
            label="Branch"
            {...registerCreate('branch', { required: 'Branch is required' })}
            error={errorsCreate.branch?.message}
          />
          <Input
            label="Root Spec Path"
            {...registerCreate('root_spec_path')}
            placeholder="spec.md"
            error={errorsCreate.root_spec_path?.message}
          />
          <Input
            label="GitHub Token (Optional)"
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
              {showToken ? 'Hide' : 'Show'} Token
            </button>
          </div>
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreateModalOpen(false)}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Create
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
          <p className="text-gray-600 dark:text-gray-400">Syncing...</p>
        </div>
      </Modal>

      <Modal
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingRepo(null);
        }}
        title="Edit Repository"
      >
        <form onSubmit={handleSubmitEdit(handleUpdate)} className="space-y-4">
          <Input
            label="Owner"
            {...registerEdit('owner', { required: 'Owner is required' })}
            error={errorsEdit.owner?.message}
          />
          <Input
            label="Repo"
            {...registerEdit('repo', { required: 'Repo is required' })}
            error={errorsEdit.repo?.message}
          />
          <Input
            label="Branch"
            {...registerEdit('branch', { required: 'Branch is required' })}
            error={errorsEdit.branch?.message}
          />
          <Input
            label="Root Spec Path"
            {...registerEdit('root_spec_path')}
            error={errorsEdit.root_spec_path?.message}
          />
          <Input
            label="GitHub Token (Optional, leave empty to not update)"
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
              {showToken ? 'Hide' : 'Show'} Token
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
              Cancel
            </Button>
            <Button type="submit" variant="primary">
              Save
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
