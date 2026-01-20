import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export type Theme = 'light' | 'dark' | 'system';

interface ThemeContextValue {
  theme: Theme;
  isDark: boolean;
  setTheme: (theme: Theme) => void;
  cycleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | null>(null);

function getStoredTheme(): Theme {
  if (typeof localStorage === 'undefined') return 'light';
  const t = localStorage.getItem('theme');
  return t === 'dark' ? 'dark' : t === 'system' ? 'system' : 'light';
}

function applyTheme(isDark: boolean) {
  document.documentElement.classList.toggle('dark', isDark);
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(getStoredTheme);
  const [systemPrefersDark, setSystemPrefersDark] = useState(() =>
    typeof window !== 'undefined' && localStorage.getItem('theme') === 'system'
      ? window.matchMedia('(prefers-color-scheme: dark)').matches
      : false
  );

  const isDark = theme === 'dark' ? true : theme === 'light' ? false : systemPrefersDark;

  useEffect(() => {
    applyTheme(isDark);
  }, [isDark]);

  useEffect(() => {
    if (theme !== 'system') return;
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    setSystemPrefersDark(mq.matches);
    const onChange = () => setSystemPrefersDark(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, [theme]);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
    localStorage.setItem('theme', t);
  }, []);

  const cycleTheme = useCallback(() => {
    const next: Theme = theme === 'light' ? 'dark' : theme === 'dark' ? 'system' : 'light';
    setTheme(next);
  }, [theme, setTheme]);

  return (
    <ThemeContext.Provider value={{ theme, isDark, setTheme, cycleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error('useTheme must be used within ThemeProvider');
  return ctx;
}
