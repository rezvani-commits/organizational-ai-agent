/**
 * auth/auth.js
 * ------------
 * نسخه‌ی متصل به بک‌اند واقعی: دیگه هش/چک رمز تو مرورگر انجام نمی‌شه،
 * فقط username/password به /login فرستاده می‌شه و پایتون (bcrypt) چک
 * می‌کنه.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

// =========================================================
// COMPATIBILITY STUB
// =========================================================
// UserManagement.jsx هنوز به localStorage/users.js وصله (قرار شد بعداً
// به بک‌اند وصلش کنیم)، و از این تابع برای ساخت کاربر جدید استفاده
// می‌کنه. وقتی پنل مدیریت رو به /users واقعی وصل کردیم، این تابع و
// استفاده‌اش تو UserManagement.jsx حذف می‌شن (چون هش کردن رمز اونجا
// سمت پایتون با bcrypt انجام می‌شه، نه اینجا).
const ITERATIONS = 600_000;

function bytesToHex(bytes) {
  return Array.from(bytes).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export async function hashPassword(password) {
  if (!password) return null;
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey("raw", enc.encode(password), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits(
    { name: "PBKDF2", salt, iterations: ITERATIONS, hash: "SHA-256" },
    keyMaterial,
    256
  );
  return `pbkdf2_sha256$${ITERATIONS}$${bytesToHex(salt)}$${bytesToHex(new Uint8Array(bits))}`;
}

/**
 * @returns {Promise<object|null>} شیء کاربر در صورت موفقیت، یا null.
 */
export async function login(username, password) {
  username = (username || "").trim();
  if (!username || !password) return null;

  try {
    const res = await fetch(`${API_BASE}/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });

    if (!res.ok) return null;

    const data = await res.json();
    if (!data.success || !data.user) return null;

    return data.user; // { username, name, department, role, level, active }
  } catch {
    return null;
  }
}

export async function changePassword(username, currentPassword, newPassword) {
  if (!currentPassword) return { success: false, message: "رمز عبور فعلی را وارد کنید." };
  if (!newPassword) return { success: false, message: "رمز عبور جدید را وارد کنید." };
  if (newPassword.length < 6) {
    return { success: false, message: "رمز عبور جدید باید حداقل ۶ کاراکتر باشد." };
  }

  try {
    const res = await fetch(`${API_BASE}/users/${encodeURIComponent(username)}/change-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ old_password: currentPassword, new_password: newPassword }),
    });

    const data = await res.json().catch(() => ({}));

    if (!res.ok) {
      return { success: false, message: data.detail || "خطا در تغییر رمز عبور." };
    }
    return { success: true, message: data.message || "رمز عبور با موفقیت تغییر کرد." };
  } catch {
    return { success: false, message: "خطا در ارتباط با سرور." };
  }
}

// =========================================================
// PERMISSION CHECK (بدون تغییر - فقط منطق ساده‌ی مقایسه‌ی عدد)
// =========================================================

export function hasPermission(currentLevel, requiredLevel) {
  if (currentLevel == null) return false;
  return currentLevel >= requiredLevel;
}

export function isManager(currentLevel) {
  return hasPermission(currentLevel, 3);
}