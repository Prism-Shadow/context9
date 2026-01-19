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
      alert(error.response?.data?.detail || '创建失败');
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
      alert(error.response?.data?.detail || '更新失败');
    }
  };

  const handleDelete = async (key: ApiKey) => {
    if (!confirm(`确定要删除 API Key "${key.name}" 吗？`)) return;
    try {
      await deleteApiKey(key.id);
      await loadApiKeys();
    } catch (error: any) {
      alert(error.response?.data?.detail || '删除失败');
    }
  };

  const handleManagePermissions = (key: ApiKey) => {
    navigate(`/api-keys/${key.id}`);
  };

  const columns: Column<ApiKey>[] = [
    { key: 'name', header: '名称' },
    {
      key: 'created_at',
      header: '创建时间',
      render: (item) => formatDate(item.created_at),
    },
    {
      key: 'repository_count',
      header: '关联仓库数',
      render: (item) => item.repository_count || 0,
    },
  ];

  if (loading) {
    return <div className="text-center py-8">加载中...</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">API Keys 管理</h1>
        <Button onClick={() => setIsCreateModalOpen(true)}>创建 API Key</Button>
      </div>

      {showNewKey && newKey && (
        <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-yellow-800 mb-1">
                新 API Key 已创建，请妥善保存（仅显示一次）：
              </p>
              <code className="text-sm text-yellow-900 bg-yellow-100 px-2 py-1 rounded">
                {newKey}
              </code>
            </div>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  copyToClipboard(newKey);
                  alert('已复制到剪贴板');
                }}
              >
                复制
              </Button>
              <Button
                size="sm"
                variant="secondary"
                onClick={() => {
                  setShowNewKey(false);
                  setNewKey('');
                }}
              >
                关闭
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
            className="text-primary-600 hover:text-primary-900"
          >
            管理权限
          </button>
        )}
      />

      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="创建 API Key"
      >
        <form onSubmit={handleSubmitCreate(handleCreate)} className="space-y-4">
          <Input
            label="名称"
            {...registerCreate('name', { required: '名称是必填项' })}
            error={errorsCreate.name?.message}
          />
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
          setEditingKey(null);
        }}
        title="编辑 API Key"
      >
        <form onSubmit={handleSubmitEdit(handleUpdate)} className="space-y-4">
          <Input
            label="名称"
            {...registerEdit('name', { required: '名称是必填项' })}
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
              取消
            </Button>
            <Button type="submit" variant="primary">
              保存
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
