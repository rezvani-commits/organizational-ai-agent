import { useEffect, useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { getUsers, createUser, updateUser, setUserActive } from "../auth/users";
import Sidebar from "../components/Sidebar";

function getLevelName(level) {
  const levels = { 1: "کاربر", 2: "مدیر", 3: "مدیر سیستم" };
  return levels[level] || `سطح ${level}`;
}

const EMPTY_NEW_USER = {
  username: "",
  name: "",
  department: "",
  role: "",
  level: 1,
  password: "",
};

/**
 * pages/UserManagement.jsx
 * ---------------------------
 * معادل app_pages/user_management.py - نسخه‌ی متصل به /users واقعی.
 *
 * @param {() => void} onNavigateChat - بازگشت به صفحه‌ی چت (دکمه‌ی سایدبار مینیمال)
 */
export default function UserManagement({ onNavigateChat }) {
  const { isManager } = useAuth();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showAddUser, setShowAddUser] = useState(false);
  const [newUser, setNewUser] = useState(EMPTY_NEW_USER);
  const [addError, setAddError] = useState("");
  const [addSuccess, setAddSuccess] = useState("");
  const [creating, setCreating] = useState(false);

  const [editingUsername, setEditingUsername] = useState(null);
  const [editForm, setEditForm] = useState(null);
  const [editError, setEditError] = useState("");
  const [saving, setSaving] = useState(false);

  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    if (isManager()) {
      refreshUsers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (!isManager()) {
    return (
      <div className="page-with-sidebar">
        <Sidebar variant="admin" onBack={onNavigateChat} />
        <main className="admin-main">
          <div className="stAlert-error">شما دسترسی لازم برای مشاهده این صفحه را ندارید.</div>
        </main>
      </div>
    );
  }

  async function refreshUsers() {
    setLoading(true);
    const data = await getUsers();
    setUsers(data);
    setLoading(false);
  }

  // =====================================================
  // ADD USER
  // =====================================================

  async function handleCreateUser(e) {
    e.preventDefault();
    setAddError("");
    setAddSuccess("");

    const username = newUser.username.trim();
    const name = newUser.name.trim();
    const department = newUser.department.trim();
    const role = newUser.role.trim();
    const { level, password } = newUser;

    if (!username) return setAddError("نام کاربری الزامی است.");
    if (username.length < 3) return setAddError("نام کاربری باید حداقل ۳ کاراکتر باشد.");
    if (!name) return setAddError("نام و نام خانوادگی الزامی است.");
    if (!department) return setAddError("واحد سازمانی الزامی است.");
    if (!role) return setAddError("سمت کاربر الزامی است.");
    if (!password) return setAddError("رمز عبور الزامی است.");
    if (password.length < 8) return setAddError("رمز عبور باید حداقل ۸ کاراکتر باشد.");

    setCreating(true);
    const { success, message } = await createUser({
      username,
      name,
      department,
      role,
      level: Number(level),
      password,
    });
    setCreating(false);

    if (success) {
      setAddSuccess(message || "کاربر با موفقیت ایجاد شد.");
      setShowAddUser(false);
      setNewUser(EMPTY_NEW_USER);
      refreshUsers();
    } else {
      setAddError(message || "ایجاد کاربر انجام نشد.");
    }
  }

  function handleCancelAdd() {
    setShowAddUser(false);
    setNewUser(EMPTY_NEW_USER);
    setAddError("");
  }

  // =====================================================
  // EDIT USER
  // =====================================================

  function startEdit(user) {
    setEditingUsername(user.username);
    setEditForm({
      name: user.name || "",
      department: user.department || "",
      role: user.role || "",
      level: user.level || 1,
    });
    setEditError("");
    setShowAddUser(false);
  }

  async function handleSaveEdit(e, username) {
    e.preventDefault();
    setEditError("");

    const name = editForm.name.trim();
    const department = editForm.department.trim();
    const role = editForm.role.trim();

    if (!name) return setEditError("نام و نام خانوادگی الزامی است.");
    if (!department) return setEditError("واحد سازمانی الزامی است.");
    if (!role) return setEditError("سمت کاربر الزامی است.");

    setSaving(true);
    const { success, message } = await updateUser({
      username,
      name,
      department,
      role,
      level: Number(editForm.level),
    });
    setSaving(false);

    if (success) {
      setEditingUsername(null);
      refreshUsers();
    } else {
      setEditError(message || "ویرایش کاربر انجام نشد.");
    }
  }

  async function handleToggleActive(username, active) {
    const { success } = await setUserActive(username, !active);
    if (success) refreshUsers();
  }

  // =====================================================
  // STATS + FILTER
  // =====================================================

  const totalUsers = users.length;
  const activeUsers = users.filter((u) => u.active ?? true).length;
  const inactiveUsers = totalUsers - activeUsers;
  const adminUsers = users.filter((u) => u.level === 3).length;

  const query = searchQuery.trim().toLowerCase();
  const filteredUsers = users.filter((u) => {
    if (!query) return true;
    const searchable = [u.username, u.name, u.department, u.role].join(" ").toLowerCase();
    return searchable.includes(query);
  });

  return (
    <div className="page-with-sidebar">
      <Sidebar variant="admin" onBack={onNavigateChat} />

      <main className="admin-page">
        <div className="admin-header-title">مدیریت کاربران</div>
        <div className="admin-header-subtitle">ایجاد، ویرایش و مدیریت کاربران سامانه</div>

        <div className="admin-top-row">
          <button
            type="button"
            className="admin-add-user-btn"
            onClick={() => {
              setShowAddUser((v) => !v);
              setEditingUsername(null);
              setAddSuccess("");
              setAddError("");
            }}
          >
            {showAddUser ? "بستن" : "افزودن کاربر"}
          </button>
        </div>

        {addSuccess && <div className="stAlert-success">{addSuccess}</div>}

        {showAddUser && (
          <div className="admin-add-form">
            <div className="admin-form-title">افزودن کاربر جدید</div>
            <div className="admin-form-subtitle">اطلاعات کاربر جدید را وارد کنید.</div>

            <form onSubmit={handleCreateUser}>
              <div className="admin-form-grid">
                <div className="admin-form-col">
                  <div className="form-field">
                    <label>نام کاربری</label>
                    <input
                      placeholder="مثلاً ali123"
                      value={newUser.username}
                      onChange={(e) => setNewUser({ ...newUser, username: e.target.value })}
                    />
                  </div>
                  <div className="form-field">
                    <label>نام و نام خانوادگی</label>
                    <input
                      placeholder="نام کاربر"
                      value={newUser.name}
                      onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                    />
                  </div>
                  <div className="form-field">
                    <label>واحد سازمانی</label>
                    <input
                      placeholder="مثلاً معاونت منابع انسانی"
                      value={newUser.department}
                      onChange={(e) => setNewUser({ ...newUser, department: e.target.value })}
                    />
                  </div>
                </div>

                <div className="admin-form-col">
                  <div className="form-field">
                    <label>سمت</label>
                    <input
                      placeholder="مثلاً کارشناس"
                      value={newUser.role}
                      onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                    />
                  </div>
                  <div className="form-field">
                    <label>سطح دسترسی</label>
                    <select
                      value={newUser.level}
                      onChange={(e) => setNewUser({ ...newUser, level: Number(e.target.value) })}
                    >
                      <option value={1}>{getLevelName(1)}</option>
                      <option value={2}>{getLevelName(2)}</option>
                      <option value={3}>{getLevelName(3)}</option>
                    </select>
                  </div>
                  <div className="form-field">
                    <label>رمز عبور</label>
                    <input
                      type="password"
                      placeholder="حداقل ۸ کاراکتر"
                      value={newUser.password}
                      onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {addError && <div className="stAlert-error">{addError}</div>}

              <div className="admin-form-buttons">
                <button type="submit" className="admin-primary-btn" disabled={creating}>
                  {creating ? "..." : "ایجاد کاربر"}
                </button>
                <button type="button" className="admin-secondary-btn" onClick={handleCancelAdd}>
                  انصراف
                </button>
              </div>
            </form>
          </div>
        )}

        {/* STATISTICS */}
        <div className="admin-stats">
          <StatCard label="کل کاربران" value={totalUsers} />
          <StatCard label="کاربران فعال" value={activeUsers} />
          <StatCard label="کاربران غیرفعال" value={inactiveUsers} />
          <StatCard label="مدیران سیستم" value={adminUsers} />
        </div>

        {/* USERS SECTION */}
        <div className="admin-user-section">
          <div className="admin-section-title">کاربران سامانه</div>
          <div className="admin-section-subtitle">مشاهده و مدیریت حساب‌های کاربری</div>

          <input
            className="admin-search-input"
            placeholder="نام، نام کاربری یا واحد سازمانی..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />

          <div className="admin-users-list">
            {loading ? (
              <div className="admin-empty-state">
                <div className="admin-empty-title">در حال بارگذاری...</div>
              </div>
            ) : filteredUsers.length === 0 ? (
              <div className="admin-empty-state">
                <div className="admin-empty-title">کاربری پیدا نشد</div>
                <div className="admin-empty-subtitle">نتیجه‌ای مطابق جستجوی شما وجود ندارد.</div>
              </div>
            ) : (
              filteredUsers.map((user) => (
                <UserCard
                  key={user.username}
                  user={user}
                  editing={editingUsername === user.username}
                  editForm={editForm}
                  editError={editError}
                  saving={saving}
                  onEditFormChange={setEditForm}
                  onStartEdit={() => startEdit(user)}
                  onCancelEdit={() => setEditingUsername(null)}
                  onSaveEdit={(e) => handleSaveEdit(e, user.username)}
                  onToggleActive={() => handleToggleActive(user.username, user.active ?? true)}
                />
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="admin-stat-card">
      <div className="admin-stat-label">{label}</div>
      <div className="admin-stat-value">{value}</div>
    </div>
  );
}

function UserCard({
  user,
  editing,
  editForm,
  editError,
  saving,
  onEditFormChange,
  onStartEdit,
  onCancelEdit,
  onSaveEdit,
  onToggleActive,
}) {
  const { username, name, department, role, level, active } = user;

  return (
    <div className="admin-user-card">
      <div className="admin-user-row">
        <div className="admin-user-info-group">
          <div className="admin-user-info">
            <div className="admin-user-name">{name || "بدون نام"}</div>
          </div>
          <div className="admin-user-info">
            <div className="admin-user-label">نام کاربری</div>
            <div className="admin-user-username">@{username}</div>
          </div>
          <div className="admin-user-info">
            <div className="admin-user-label">واحد سازمانی</div>
            <div className="admin-user-detail">{department || "بدون واحد"}</div>
          </div>
          <div className="admin-user-info">
            <div className="admin-user-label">سمت</div>
            <div className="admin-user-detail">{role || "بدون سمت"}</div>
          </div>
          <div className="admin-user-info">
            <div className="admin-user-label">سطح دسترسی</div>
            <div className="admin-user-level">{getLevelName(level)}</div>
          </div>
        </div>

        <div className={`admin-status ${active ? "admin-status-active" : "admin-status-inactive"}`}>
          {active ? "فعال" : "غیرفعال"}
        </div>

        <div className="admin-user-actions">
          <button type="button" className="admin-secondary-btn" onClick={onStartEdit}>
            ویرایش
          </button>
          <button type="button" className="admin-secondary-btn" onClick={onToggleActive}>
            {active ? "غیرفعال" : "فعال"}
          </button>
        </div>
      </div>

      {editing && editForm && (
        <div className="admin-edit-form">
          <div className="admin-form-title">ویرایش کاربر</div>
          <div className="admin-edit-username">@{username}</div>

          <form onSubmit={onSaveEdit}>
            <div className="admin-form-grid">
              <div className="admin-form-col">
                <div className="form-field">
                  <label>نام و نام خانوادگی</label>
                  <input
                    value={editForm.name}
                    onChange={(e) => onEditFormChange({ ...editForm, name: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>واحد سازمانی</label>
                  <input
                    value={editForm.department}
                    onChange={(e) =>
                      onEditFormChange({ ...editForm, department: e.target.value })
                    }
                  />
                </div>
              </div>
              <div className="admin-form-col">
                <div className="form-field">
                  <label>سمت</label>
                  <input
                    value={editForm.role}
                    onChange={(e) => onEditFormChange({ ...editForm, role: e.target.value })}
                  />
                </div>
                <div className="form-field">
                  <label>سطح دسترسی</label>
                  <select
                    value={editForm.level}
                    onChange={(e) =>
                      onEditFormChange({ ...editForm, level: Number(e.target.value) })
                    }
                  >
                    <option value={1}>{getLevelName(1)}</option>
                    <option value={2}>{getLevelName(2)}</option>
                    <option value={3}>{getLevelName(3)}</option>
                  </select>
                </div>
              </div>
            </div>

            {editError && <div className="stAlert-error">{editError}</div>}

            <div className="admin-form-buttons">
              <button type="submit" className="admin-primary-btn" disabled={saving}>
                {saving ? "..." : "ذخیره تغییرات"}
              </button>
              <button type="button" className="admin-secondary-btn" onClick={onCancelEdit}>
                انصراف
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}