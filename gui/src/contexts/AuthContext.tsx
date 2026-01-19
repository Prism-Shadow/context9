import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { login as loginApi, getCurrentAdmin, logout as logoutApi } from '../services/auth';
import { TOKEN_KEY } from '../utils/constants';
import type { Admin } from '../utils/types';

interface AuthContextType {
  user: Admin | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loading: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<Admin | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initAuth = async () => {
      const token = localStorage.getItem(TOKEN_KEY);
      if (token) {
        try {
          const admin = await getCurrentAdmin();
          setUser(admin);
        } catch (error) {
          localStorage.removeItem(TOKEN_KEY);
        }
      }
      setLoading(false);
    };

    initAuth();
  }, []);

  const login = async (username: string, password: string) => {
    const response = await loginApi({ username, password });
    localStorage.setItem(TOKEN_KEY, response.access_token);
    setUser(response.admin);
  };

  const logout = async () => {
    try {
      await logoutApi();
    } catch (error) {
      // 即使 API 调用失败，也清除本地状态
      console.error('Logout API error:', error);
    } finally {
      localStorage.removeItem(TOKEN_KEY);
      setUser(null);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        login,
        logout,
        loading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
