/**
 * auth/users.js
 * -------------
 * نسخه‌ی متصل به بک‌اند واقعی: دیگه از localStorage استفاده نمی‌شه،
 * همه‌چیز از /users روی FastAPI می‌آد. هش کردن رمز هم دیگه اینجا
 * انجام نمی‌شه - رمز خام به بک‌اند فرستاده می‌شه و پایتون (bcrypt)
 * هشش می‌کنه.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function _handle(res) {
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    return { success: false, message: data.detail || "خطا در ارتباط با سرور." };
  }
  return { success: true, message: data.message || "", data };
}

// =========================================================
// GET USERS
// =========================================================

export async function getUsers() {
  try {
    const res = await fetch(`${API_BASE}/users`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

// =========================================================
// CREATE USER
// =========================================================

/**
 * @param {{username, name, department, role, level, password}} params
 * توجه: اینجا password خام است، نه passwordHash - بک‌اند خودش هش می‌کند.
 */
export async function createUser({ username, name, department, role, level, password }) {
  try {
    const res = await fetch(`${API_BASE}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, name, department, role, level, password }),
    });
    return await _handle(res);
  } catch {
    return { success: false, message: "خطا در ارتباط با سرور." };
  }
}

// =========================================================
// UPDATE USER
// =========================================================

export async function updateUser({ username, name, department, role, level }) {
  try {
    const res = await fetch(`${API_BASE}/users/${encodeURIComponent(username)}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, department, role, level }),
    });
    return await _handle(res);
  } catch {
    return { success: false, message: "خطا در ارتباط با سرور." };
  }
}

// =========================================================
// ACTIVATE / DEACTIVATE USER
// =========================================================

export async function setUserActive(username, active) {
  try {
    const res = await fetch(`${API_BASE}/users/${encodeURIComponent(username)}/active`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ active }),
    });
    return await _handle(res);
  } catch {
    return { success: false, message: "خطا در ارتباط با سرور." };
  }
}