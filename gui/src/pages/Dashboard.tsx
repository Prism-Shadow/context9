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
        <div className="text-gray-500 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  return (
    <div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">Dashboard</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-none border border-transparent dark:border-gray-700 p-6">
          <h2 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">Total API Keys</h2>
          <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">{stats.apiKeysCount}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-none border border-transparent dark:border-gray-700 p-6">
          <h2 className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-2">Total Repositories</h2>
          <p className="text-3xl font-bold text-primary-600 dark:text-primary-400">{stats.repositoriesCount}</p>
        </div>
      </div>
    </div>
  );
};
