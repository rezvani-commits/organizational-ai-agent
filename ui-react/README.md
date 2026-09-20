# نیرویار — نسخه‌ی React

این پروژه، تبدیل مستقیم پوشه‌ی UI استریم‌لیتِ شما به React (با Vite) است، با
حفظ دقیق همان ساختار پوشه‌ها و همان نام فایل‌ها تا مقایسه و نگهداری راحت باشد.

## نصب و اجرا

```bash
npm install
npm run dev
```

سپس آدرسی که Vite چاپ می‌کند (معمولاً http://localhost:5173) را باز کنید.

**کاربران آزمایشی (seed شده در localStorage در اولین اجرا):**
- `admin` / `1234`  (سطح ۳ - مدیر سیستم)
- `سارا` / `12345678` (سطح ۳ - مدیر سیستم)

## نگاشت فایل‌ها (Streamlit → React)

| Streamlit (اصلی)                       | React (این پروژه)                          |
|-----------------------------------------|---------------------------------------------|
| `app.py`                                | `src/App.jsx`                                |
| `app_pages/login.py`                    | `src/pages/Login.jsx`                        |
| `app_pages/chat.py`                     | `src/pages/Chat.jsx`                         |
| `app_pages/user_management.py`          | `src/pages/UserManagement.jsx`               |
| `auth/auth.py`                          | `src/auth/auth.js` + `src/auth/AuthContext.jsx` |
| `auth/users.py`                         | `src/auth/users.js`                          |
| `components/sidebar.py`                 | `src/components/Sidebar.jsx`                 |
| `components/chat_message.py`            | `src/components/ChatMessage.jsx`             |
| `components/citation.py`                | `src/components/Citation.jsx`                |
| `components/evaluation.py`              | `src/components/Evaluation.jsx`              |
| `components/input_box.py`               | `src/components/InputBox.jsx`                |
| `components/status.py`                  | `src/components/Status.jsx`                  |
| `components/suggested_questions.py`     | `src/components/SuggestedQuestions.jsx`      |
| `components/change_password.py`         | `src/components/ChangePasswordDialog.jsx`    |
| `components/loading.py`                 | `src/components/Loading.jsx`                 |
| `components/cookie_manager.py`          | `src/components/cookieManager.js`            |
| `data/mock_data.py`                     | `src/data/mockData.js`                       |
| `data/users.json`                       | `src/data/users.json`                        |
| `styles/style.py`                       | `src/styles/style.css`                       |

## تفاوت‌های اساسی نسبت به نسخه‌ی استریم‌لیت (به‌خاطر محدودیت‌های مرورگر)

- **`back.*` (RAG واقعی، `session_store`, `DialogueManager`)** در پوشه‌ی
  اصلی موجود نبود (فقط UI ضمیمه شده بود)، پس این پروژه جایگزین‌های
  کلاینتی برای آن‌ها ساخته:
  - `src/data/mockData.js` → پاسخ آزمایشی به‌جای `RAGGraph.run()`
  - `src/data/sessionStore.js` → لیست/تاریخچه‌ی گفتگوها با `localStorage`
- **`data/users.json` روی دیسک** با `localStorage` جایگزین شده
  (`src/auth/users.js`)؛ چون در مرورگر امکان نوشتن مستقیم روی فایل
  وجود ندارد. برای اتصال به یک بک‌اند واقعی، توابع `getUsers` /
  `createUser` / `updateUser` را با فراخوانی API خودتان جایگزین کنید.
- هش کردن رمز عبور همان الگوریتم اصلی (PBKDF2-HMAC-SHA256، ۶۰۰٬۰۰۰
  تکرار) را با Web Crypto API پیاده‌سازی می‌کند، با همان فرمت رشته‌ای
  `pbkdf2_sha256$iterations$salt$hash`.
- `st.session_state` با React Context (`AuthContext`) + `sessionStorage`
  جایگزین شده؛ کوکی‌های `extra_streamlit_components` با کوکی‌های واقعی
  مرورگر (`src/components/cookieManager.js`).
- ناوبری بین سه صفحه (`st.navigation`) با یک state ساده در `App.jsx`
  انجام می‌شود.

## مراحل بعدی برای اتصال به بک‌اند واقعی

1. `src/data/mockData.js` → جایگزین با `fetch` به API واقعیِ RAG شما.
2. `src/data/sessionStore.js` → جایگزین با فراخوانی‌های واقعی به بک‌اند
   برای مدیریت سشن‌ها و تاریخچه‌ی گفتگو.
3. `src/auth/users.js` → جایگزین با API مدیریت کاربران (یا اتصال مستقیم
   به همان `data/users.json` از طریق یک سرویس بک‌اند).
