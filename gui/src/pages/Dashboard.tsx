import React, { useEffect, useState } from 'react';
import { getApiKeys } from '../services/apiKeys';
import { getRepositories } from '../services/repositories';

export const Dashboard: React.FC = () => {
  const [stats, setStats] = useState({
    apiKeysCount: 0,
    repositoriesCount: 0,
    loading: true,
  });

  useEffect(() => {
    const loadStats = async () => {
      try {
        const [apiKeysRes, reposRes] = await Promise.all([
          getApiKeys(),
          getRepositories(),
        ]);
        setStats({
          apiKeysCount: apiKeysRes.total,
          repositoriesCount: reposRes.total,
          loading: false,
        });
      } catch (error) {
        console.error('Failed to load stats:', error);
        setStats((prev) => ({ ...prev, loading: false }));
      }
    };

    loadStats();
  }, []);

  if (stats.loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">加载中...</div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">仪表盘</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-700 mb-2">API Keys 总数</h2>
          <p className="text-3xl font-bold text-primary-600">{stats.apiKeysCount}</p>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-medium text-gray-700 mb-2">仓库总数</h2>
          <p className="text-3xl font-bold text-primary-600">{stats.repositoriesCount}</p>
        </div>
      </div>
    </div>
  );
};
