import React from 'react';
import { NavLink } from 'react-router-dom';

export const Sidebar: React.FC = () => {
  const navItems = [
    { path: '/dashboard', label: 'Dashboard' },
    { path: '/api-keys', label: 'API Keys' },
    { path: '/repositories', label: 'Repositories' },
  ];

  return (
    <aside className="w-64 bg-white shadow-sm border-r border-gray-200 min-h-screen">
      <nav className="p-4">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.path}>
              <NavLink
                to={item.path}
                className={({ isActive }) =>
                  `block px-4 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-100 text-primary-700 font-medium'
                      : 'text-gray-700 hover:bg-gray-100'
                  }`
                }
              >
                {item.label}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
};
