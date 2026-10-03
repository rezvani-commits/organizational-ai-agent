import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import ChangePasswordDialog from "./ChangePasswordDialog";
import { DeleteIcon, BrandIcon } from "./icons";

/**
 * components/Sidebar.jsx
 * -------------------------
 *
 * @param {Array<{id: string, title: string}>} sessions
 * @param {string} currentSessionId
 * @param {(sessionId: string) => void} onSelectSession
 * @param {() => void} onNewSession
 * @param {(sessionId: string) => void} onDeleteSession
 * @param {() => void} onNavigateUserManagement
 * @param {"chat"|"admin"} variant - "chat": سایدبار کامل با گفتگوی جدید و تاریخچه.
 * @param {() => void} onBack - در حالت admin، کلیک روی دکمه‌ی بازگشت
 */
export default function Sidebar({
  sessions = [],
  currentSessionId = null,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onNavigateUserManagement,
  variant = "chat",
  onBack,
}) {
  const { user, logout, isManager } = useAuth();
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [toast, setToast] = useState("");

  if (!user) return null;

  function handleLogout() {
    logout();
    setUserMenuOpen(false);
  }

  function handlePasswordChangeSuccess() {
    setShowChangePassword(false);
    setToast("رمز عبور با موفقیت تغییر کرد.");
    setTimeout(() => setToast(""), 3000);
  }

  return (
    <>
      {toast && <div className="password-success-toast">{toast}</div>}

      <aside className="app-sidebar">
        {/* BRAND */}
        <div className="sidebar-brand">
          <span className="sidebar-brand-icon">
            <BrandIcon size={16} />
          </span>
          <span className="sidebar-brand-name">نیرویار</span>
        </div>

        {variant === "admin" ? (
          /* حالت مینیمال: فقط دکمه‌ی بازگشت به گفتگو */
          <button type="button" className="sidebar-back-btn" onClick={onBack}>
            ← بازگشت به گفتگو
          </button>
        ) : (
          <>
            {/* NEW CHAT BUTTON */}
            <button type="button" className="sidebar-new-chat-btn" onClick={onNewSession}>
              ➕ گفتگوی جدید
            </button>

            <hr />

            {/* SESSIONS TITLE */}
            <div className="sidebar-history-title">💬 گفتگوهای اخیر</div>

            {/* LIST OF SESSIONS */}
            <div className="session-list">
              {sessions.length === 0 ? (
                <div className="sidebar-info">📭 هیچ گفتگویی وجود ندارد.</div>
              ) : (
                sessions.map((session) => {
                  const isActive = session.id === currentSessionId;
                  return (
                    <div className="session-row" key={session.id}>
                      {isActive ? (
                        <div className="chat-item active-session">▶️ {session.title}</div>
                      ) : (
                        <button
                          type="button"
                          className="chat-item chat-item-button"
                          onClick={() => onSelectSession?.(session.id)}
                        >
                          💬 {session.title}
                        </button>
                      )}
                      <button
                        type="button"
                        className="session-delete-btn"
                        title="حذف گفتگو"
                        onClick={() => onDeleteSession?.(session.id)}
                      >
                        <DeleteIcon size={15} />
                      </button>
                    </div>
                  );
                })
              )}
            </div>
          </>
        )}

        {/* USER SECTION */}
        <div className="sidebar-user-section">
          <hr />

          <button
            type="button"
            className="sidebar-user-button"
            onClick={() => setUserMenuOpen((v) => !v)}
          >
            👤 {user.name || ""}
          </button>

          <div className="sidebar-user-department">
            {user.role || ""} · {user.department || ""}
          </div>

          {userMenuOpen && (
            <div className="sidebar-user-menu">
              <button
                type="button"
                className="sidebar-menu-btn"
                onClick={() => setShowChangePassword(true)}
              >
                🔑 تغییر رمز عبور
              </button>

              {isManager() && variant !== "admin" && (
                <button
                  type="button"
                  className="sidebar-menu-btn"
                  onClick={onNavigateUserManagement}
                >
                  👥 مدیریت کاربران
                </button>
              )}

              <button
                type="button"
                className="sidebar-menu-btn sidebar-logout-btn"
                onClick={handleLogout}
              >
                🚪 خروج
              </button>
            </div>
          )}
        </div>
      </aside>

      {showChangePassword && (
        <ChangePasswordDialog
          username={user.username}
          onClose={() => setShowChangePassword(false)}
          onSuccess={handlePasswordChangeSuccess}
        />
      )}
    </>
  );
}
