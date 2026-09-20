import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import Loading from "./components/Loading";
import Login from "./pages/Login";
import Chat from "./pages/Chat";
import UserManagement from "./pages/UserManagement";

/**
 * App.jsx
 * ---------
 * معادل app.py.
 *
 * st.navigation(pages) با یک state ساده‌ی currentPage جایگزین شده
 * (بدون نیاز به react-router، چون این پروژه فقط سه صفحه دارد - دقیقاً
 * مثل ساختار اصلی).
 */

const PAGES = {
  LOGIN: "login",
  CHAT: "chat",
  USER_MANAGEMENT: "user_management",
};

function AppShell() {
  const { isAuthenticated } = useAuth();

  // =========================================================
  // LOADING PAGE (فقط یک بار، در ابتدای اجرای برنامه)
  // =========================================================
  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    // اینجا معادل initialize_backend() در app_pages/chat.py است -
    // جایی که مدل RAG واقعی راه‌اندازی می‌شود. چون پروژه فقط فرانت‌اند
    // است، فقط یک تأخیر کوتاه شبیه‌سازی می‌کنیم.
    const timer = setTimeout(() => setAppReady(true), 600);
    return () => clearTimeout(timer);
  }, []);

  // =========================================================
  // NAVIGATION
  // =========================================================
  const [page, setPage] = useState(PAGES.LOGIN);

  useEffect(() => {
    if (isAuthenticated && page === PAGES.LOGIN) {
      setPage(PAGES.CHAT);
    }
    if (!isAuthenticated) {
      setPage(PAGES.LOGIN);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  if (!appReady) {
    return <Loading />;
  }

  if (!isAuthenticated || page === PAGES.LOGIN) {
    return <Login onLoggedIn={() => setPage(PAGES.CHAT)} />;
  }

  if (page === PAGES.USER_MANAGEMENT) {
    return <UserManagement onNavigateChat={() => setPage(PAGES.CHAT)} />;
  }

  return <Chat onNavigateUserManagement={() => setPage(PAGES.USER_MANAGEMENT)} />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppShell />
    </AuthProvider>
  );
}
