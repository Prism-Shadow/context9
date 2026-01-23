import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Key, FolderGit2, Scan } from 'lucide-react';
import { useLocale } from '../../contexts/LocaleContext';

const GITHUB_URL = 'https://github.com/Prism-Shadow/context9';

const GitHubIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="currentColor">
    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
  </svg>
);

export const Sidebar: React.FC = () => {
  const { t } = useLocale();
  const navItems = [
    { path: '/dashboard', label: t('sidebar.dashboard'), icon: LayoutDashboard },
    { path: '/api-keys', label: t('sidebar.apiKeys'), icon: Key },
    { path: '/repositories', label: t('sidebar.repositories'), icon: FolderGit2 },
    { path: '/inspector', label: t('sidebar.inspector'), icon: Scan },
  ];

  return (
    <aside className="fixed left-0 top-16 z-10 w-64 h-[calc(100vh-4rem)] flex flex-col bg-white dark:bg-gray-800 shadow-sm border-r border-gray-200 dark:border-gray-700">
      <nav className="p-4 flex-1 min-h-0 overflow-y-auto">
        <ul className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <li key={item.path}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `flex items-center gap-3 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-100 dark:bg-primary-600/30 text-primary-700 dark:text-primary-100 font-medium'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`
                  }
                >
                  <Icon className="w-5 h-5 flex-shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              </li>
            );
          })}
        </ul>
      </nav>
      <div className="p-4 flex justify-center items-center border-t border-gray-100 dark:border-gray-700 flex-shrink-0">
        <a
          href={GITHUB_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors inline-flex"
          aria-label="GitHub"
        >
          <GitHubIcon />
        </a>
      </div>
    </aside>
  );
};
