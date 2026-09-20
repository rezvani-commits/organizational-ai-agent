import { createContext, useContext, useState, useCallback } from "react";
import * as authApi from "./auth";

/**
 * AuthContext
 * -----------
 * معادل بخش‌های session_state.is_authenticated / session_state.user
 * در نسخه‌ی Streamlit. مقدار کاربر در sessionStorage نگه داشته می‌شود
 * تا با رفرش صفحه (مثل رفتار session_state استریم‌لیت در طول یک سشن)
 * از بین نرود.
 */

const AuthContext = createContext(null);

const SESSION_KEY = "app_current_user";

function loadStoredUser() {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [user, setUser] = useState(loadStoredUser);

  const isAuthenticated = !!user;

  const login = useCallback(async (username, password) => {
    const loggedInUser = await authApi.login(username, password);
    if (loggedInUser) {
      setUser(loggedInUser);
      sessionStorage.setItem(SESSION_KEY, JSON.stringify(loggedInUser));
      return true;
    }
    return false;
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    sessionStorage.removeItem(SESSION_KEY);
  }, []);

  const isManager = useCallback(() => {
    return authApi.isManager(user?.level ?? null);
  }, [user]);

  const value = {
    user,
    isAuthenticated,
    login,
    logout,
    isManager,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth باید داخل AuthProvider استفاده شود.");
  return ctx;
}
