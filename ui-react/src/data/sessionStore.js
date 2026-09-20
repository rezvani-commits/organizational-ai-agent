/**
 * data/sessionStore.js
 * --------------------
 * پوشه‌ی back (back.session_store و back.intent.dialogue_manager) در
 * پروژه‌ی اصلی جزو UI نبود و در دسترس نیست. این فایل همان رفتار مورد
 * انتظارِ chat.py را با localStorage شبیه‌سازی می‌کند تا سایدبار و
 * تاریخچه‌ی گفتگو در نسخه‌ی React هم کار کند:
 *
 *   create_session, list_sessions, set_session_title,
 *   touch_session, delete_session  ->  از back.session_store
 *   get_history / append_message   ->  از back.intent.dialogue_manager
 *
 * آینده: این فایل را با فراخوانی‌های واقعی به API بک‌اند جایگزین کنید.
 */

const SESSIONS_KEY = "app_sessions";
const MESSAGES_KEY_PREFIX = "app_session_messages:";

function readSessions() {
  try {
    const raw = localStorage.getItem(SESSIONS_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writeSessions(sessions) {
  localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
}

// =========================================================
// SESSIONS
// =========================================================

export function createSession(sessionId, username) {
  const sessions = readSessions();
  sessions[sessionId] = {
    id: sessionId,
    username,
    title: "گفتگوی جدید",
    updatedAt: Date.now(),
  };
  writeSessions(sessions);
}

export function listSessions(username) {
  const sessions = readSessions();
  return Object.values(sessions)
    .filter((s) => s.username === username)
    .sort((a, b) => b.updatedAt - a.updatedAt)
    .map((s) => ({ id: s.id, title: s.title }));
}

export function setSessionTitle(sessionId, title) {
  const sessions = readSessions();
  if (sessions[sessionId]) {
    // مثل دمو: عنوان کوتاه‌شده‌ی همان اولین سوال
    sessions[sessionId].title = title.length > 40 ? title.slice(0, 40) + "…" : title;
    writeSessions(sessions);
  }
}

export function touchSession(sessionId) {
  const sessions = readSessions();
  if (sessions[sessionId]) {
    sessions[sessionId].updatedAt = Date.now();
    writeSessions(sessions);
  }
}

export function deleteSession(sessionId) {
  const sessions = readSessions();
  delete sessions[sessionId];
  writeSessions(sessions);
  localStorage.removeItem(MESSAGES_KEY_PREFIX + sessionId);
}

// =========================================================
// MESSAGES (دیالوگ منیجر)
// =========================================================

export function getHistory(sessionId) {
  try {
    const raw = localStorage.getItem(MESSAGES_KEY_PREFIX + sessionId);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveHistory(sessionId, messages) {
  localStorage.setItem(MESSAGES_KEY_PREFIX + sessionId, JSON.stringify(messages));
}
