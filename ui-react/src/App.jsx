import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import Loading from "./components/Loading";
import Login from "./pages/Login";
import Chat from "./pages/Chat";
import UserManagement from "./pages/UserManagement";



const PAGES = {
  LOGIN: "login",
  CHAT: "chat",
  USER_MANAGEMENT: "user_management",
};

function AppShell() {
  const { isAuthenticated } = useAuth();

  const [appReady, setAppReady] = useState(false);

  useEffect(() => {
    
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
