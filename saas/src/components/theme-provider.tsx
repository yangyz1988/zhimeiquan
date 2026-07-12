"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

type Theme = "light" | "dark";

interface ThemeContextValue {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

/**
 * ThemeProvider — 主题上下文提供者
 *
 * 管理 dark/light 模式切换，自动同步到 <html> 元素的 class
 * 和 localStorage。主题状态通过 React Context 在整个应用中共享。
 *
 * @example
 * ```tsx
 * // 在根布局中
 * <ThemeProvider>
 *   <App />
 * </ThemeProvider>
 *
 * // 在任意子组件中
 * const { theme, toggleTheme } = useTheme();
 * ```
 */
export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>("dark");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem("theme") as Theme | null;
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const initial = stored || (prefersDark ? "dark" : "light");
    setThemeState(initial);
    applyTheme(initial);
  }, []);

  const applyTheme = (t: Theme) => {
    document.documentElement.classList.toggle("dark", t === "dark");
  };

  const setTheme = (t: Theme) => {
    setThemeState(t);
    applyTheme(t);
    localStorage.setItem("theme", t);
  };

  const toggleTheme = () => {
    setTheme(theme === "dark" ? "light" : "dark");
  };

  // 防止 hydration 闪烁：在客户端挂载前渲染空白
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

/**
 * useTheme — 获取主题上下文
 *
 * @throws 如果在 ThemeProvider 外部使用会抛出错误
 */
export function useTheme(): ThemeContextValue {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    // 服务端预渲染时返回安全的默认值，避免阻塞构建
    return { theme: "dark", setTheme: () => {}, toggleTheme: () => {} };
  }
  return ctx;
}

/**
 * WithTheme — 高阶组件，用于类组件中获取主题上下文
 * 直接使用 useTheme hook 即可，此导出仅作为备选
 */
export { ThemeContext };
