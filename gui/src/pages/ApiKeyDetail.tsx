import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getApiKeyDetail,
  updateApiKeyRepositories,
} from '../services/apiKeys';
import { getRepositories } from '../services/repositories';
import { Button } from '../components/common/Button';
import type { ApiKeyDetail, Repository } from '../utils/types';

export const ApiKeyDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [apiKey, setApiKey] = useState<ApiKeyDetail | null>(null);
  const [allRepositories, setAllRepositories] = useState<Repository[]>([]);
  const [selectedRepoIds, setSelectedRepoIds] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [apiKeyRes, reposRes] = await Promise.all([
        getApiKeyDetail(Number(id)),
        getRepositories(),
      ]);
      setApiKey(apiKeyRes);
      setAllRepositories(reposRes.items);
      setSelectedRepoIds(apiKeyRes.repositories.map((r) => r.id));
    } catch (error) {
      console.error('Failed to load data:', error);
      alert('Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleRepository = (repoId: number) => {
    setSelectedRepoIds((prev) =>
      prev.includes(repoId)
        ? prev.filter((id) => id !== repoId)
        : [...prev, repoId]
    );
  };

  const handleSave = async () => {
    if (!id) return;
    try {
      setSaving(true);
      await updateApiKeyRepositories(Number(id), selectedRepoIds);
      alert('Permissions updated successfully');
      navigate('/api-keys');
    } catch (error: any) {
      alert(error.response?.data?.detail || 'Failed to update');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading...</div>;
  }

  if (!apiKey) {
    return <div className="text-center py-8">API Key does not exist</div>;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <button
            onClick={() => navigate('/api-keys')}
            className="text-sm text-gray-600 hover:text-gray-900 mb-2"
          >
            ← Back to List
          </button>
          <h1 className="text-2xl font-bold text-gray-900">API Key: {apiKey.name}</h1>
        </div>
        <Button onClick={handleSave} disabled={saving}>
          {saving ? 'Saving...' : 'Save Permissions'}
        </Button>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h2>
        <dl className="grid grid-cols-1 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500">Name</dt>
            <dd className="mt-1 text-sm text-gray-900">{apiKey.name}</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Created At</dt>
            <dd className="mt-1 text-sm text-gray-900">
              {new Date(apiKey.created_at).toLocaleString('en-US')}
            </dd>
          </div>
        </dl>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-medium text-gray-900 mb-4">Repository Permissions</h2>
        <p className="text-sm text-gray-600 mb-4">
          Select repositories that this API Key can access:
        </p>
        <div className="space-y-2">
          {allRepositories.map((repo) => (
            <label
              key={repo.id}
              className="flex items-center p-3 border rounded-lg hover:bg-gray-50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedRepoIds.includes(repo.id)}
                onChange={() => handleToggleRepository(repo.id)}
                className="mr-3 h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <div className="flex-1">
                <div className="font-medium text-gray-900">
                  {repo.owner}/{repo.repo}
                </div>
                <div className="text-sm text-gray-500">
                  Branch: {repo.branch} | Path: {repo.root_spec_path}
                </div>
              </div>
            </label>
          ))}
          {allRepositories.length === 0 && (
            <p className="text-sm text-gray-500 text-center py-4">
              No repositories available, please create a repository first
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
