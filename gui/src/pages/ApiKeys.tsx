import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
  getApiKeys,
  createApiKey,
  deleteApiKey,
  updateApiKey,
} from '../services/apiKeys';
import { Table, Column } from '../components/common/Table';
import { Modal } from '../components/common/Modal';
import { Button } from '../components/common/Button';
import { Input } from '../components/common/Input';
import { formatDate, copyToClipboard } from '../utils/helpers';
import type { ApiKey } from '../utils/types';

interface ApiKeyFormData {
  name: string;
}

export const ApiKeys: React.FC = () => {
  const navigate = useNavigate();
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([]);
  const [loading, setLoading] = useState(true);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingKey, setEditingKey] = useState<ApiKey | null>(null);
  const [newKey, setNewKey] = useState<string>('');
  const [showNewKey, setShowNewKey] = useState(false);

  const {
    register: registerCreate,
    handleSubmit: handleSubmitCreate,
    formState: { errors: errorsCreate },
    reset: resetCreate,
  } = useForm<ApiKeyFormData>();

  const {
    register: registerEdit,
    handleSubmit: handleSubmitEdit,
    formState: { errors: errorsEdit },
    reset: resetEdit,
  } = useForm<ApiKeyFormData>();

  useEffect(() => {
    loadApiKeys();
  }, []);

  const loadApiKeys = async () => {
    try {
      setLoading(true);
      const response = await getApiKeys();
      setApiKeys(response.items);
    } catch (error) {
      console.error('Failed to load API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = async (data: ApiKeyFormData) => {
    try {
      const response = await createApiKey(data);
      setNewKey(response.key_value);
      setShowNewKey(true);
      resetCreate();
      setIsCreateModalOpen(false);
      await loadApiKeys();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to create');
    }
  };

  const handleEdit = (key: ApiKey) => {
    setEditingKey(key);
    resetEdit({ name: key.name });
    setIsEditModalOpen(true);
  };

  const handleUpdate = async (data: ApiKeyFormData) => {
    if (!editingKey) return;
    try {
      await updateApiKey(editingKey.id, data);
      setIsEditModalOpen(false);
      setEditingKey(null);
      await loadApiKeys();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update');
    }
  };

  const handleDelete = async (key: ApiKey) => {
    if (!confirm(`Are you sure you want to delete API Key "${key.name}"?`)) return;
    try {
      await deleteApiKey(key.id);
      await loadApiKeys();
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to delete');
    }
  };

  const handleManagePermissions = (key: ApiKey) => {
    navigate(`/api-keys/${key.id}`);
  };

  const columns: Column<ApiKey>[] = [
    { key: 'name', header: 'Name' },
    {
      key: 'created_at',
      header: 'Created At',
      render: (item) => formatDate(item.created_at),
    },
    {
      key: 'repository_count',
      header: 'Repositories',
      render: (item) => item.repository_count || 0,
    },
  ];

  if (loading) {
    return <div className="text-center py-8 text-gray-500 dark:text-gray-400">Loading...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">API Keys Management</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>Create API Key</Button>
      </div>

      {showNewKey && newKey && (
        <div className="mb-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-1">
                New API Key created, please save it securely (shown only once):
              </p>
              <code className="text-sm text-yellow-900 dark:text-yellow-100 bg-yellow-100 dark:bg-yellow-900/40 px-2 py-1 rounded">
                {newKey}
              </code>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  copyToClipboard(newKey);
                  alert('Copied to clipboard');
                }}
              >
                Copy
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setShowNewKey(false);
                  setNewKey('');
                }}
              >
                Close
              </Button>
            </div>
          </div>
        </div>
      )}

      <Table
        data={apiKeys}
        columns={columns}
        onEdit={handleEdit}
        onDelete={handleDelete}
        actions={(item) => (
          <button
            onClick={() => handleManagePermissions(item)}
            className="text-primary-500 dark:text-primary-200 hover:text-primary-600 dark:hover:text-primary-100"
          >
            Manage Permissions
          </button>
        )}
      />

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create API Key"
        closeOnOverlayClick={false}
      >
        <form onSubmit={handleSubmitCreate(handleCreate)} className="space-y-4">
          <Input
            label="Name"
            {...registerCreate('name', { required: 'Name is required' })}
            error={errorsCreate.name?.message}
          />
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
        isOpen={isEditModalOpen}
        onClose={() => {
          setIsEditModalOpen(false);
          setEditingKey(null);
        }}
        title="Edit API Key"
      >
        <form onSubmit={handleSubmitEdit(handleUpdate)} className="space-y-4">
          <Input
            label="Name"
            {...registerEdit('name', { required: 'Name is required' })}
            error={errorsEdit.name?.message}
          />
          <div className="flex gap-2 justify-end">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setIsEditModalOpen(false);
                setEditingKey(null);
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
