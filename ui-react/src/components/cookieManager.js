/**
 * components/cookieManager.js
 * ----------------------------
 * معادل components/cookie_manager.py.
 *
 * در نسخه‌ی پایتون از extra_streamlit_components.CookieManager استفاده
 * می‌شد تا شناسه‌ی سشن فعلی (current_session_id) بین رفرش‌های صفحه حفظ
 * شود. اینجا از کوکی‌های واقعیِ مرورگر استفاده می‌کنیم تا همان رفتار
 * حفظ شود.
 */

function setCookie(name, value, days = 365) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/`;
}

function getCookie(name) {
  const match = document.cookie
    .split("; ")
    .find((row) => row.startsWith(name + "="));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

function deleteCookie(name) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/`;
}

export const cookieManager = {
  get: getCookie,
  set: setCookie,
  delete: deleteCookie,
};
