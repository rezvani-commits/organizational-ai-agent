import { useState } from "react";
import { useAuth } from "../auth/AuthContext";
import { BrandIcon } from "../components/icons";

/**
 * pages/Login.jsx
 * -----------------
 *
 * @param {() => void} onLoggedIn - فراخوانی می‌شود تا به صفحه‌ی چت سوییچ شود
 */
export default function Login({ onLoggedIn }) {
  const { login } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setSubmitting(true);

    const ok = await login(username, password);

    setSubmitting(false);

    if (ok) {
      onLoggedIn?.();
    } else {
      setError("نام کاربری یا رمز عبور اشتباه است.");
    }
  }

  return (
    <div className="login-page">
      <div className="login-columns">
        <div className="login-center">
          <div className="login-card">
            <div className="login-header">
              <div className="login-logo">
                <BrandIcon size={36} />
              </div>
              <div className="login-title">نیرویار</div>
              <div className="login-subtitle">برای ادامه وارد حساب کاربری خود شوید</div>
            </div>

            <form className="login-form" onSubmit={handleSubmit}>
              <div className="form-field">
                <label htmlFor="username">نام کاربری</label>
                <input
                  id="username"
                  type="text"
                  autoComplete="off"
                  placeholder="نام کاربری خود را وارد کنید"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>

              <div className="form-field">
                <label htmlFor="password">رمز عبور</label>
                <input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  placeholder="رمز عبور خود را وارد کنید"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              <button type="submit" className="login-submit-btn" disabled={submitting}>
                {submitting ? "..." : "ورود"}
              </button>
            </form>

            {error && <div className="stAlert-error login-error">{error}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
