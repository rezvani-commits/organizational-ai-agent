import { useState } from "react";
import { changePassword } from "../auth/auth";


export default function ChangePasswordDialog({ username, onClose, onSuccess }) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    setError("");

    if (newPassword !== confirmPassword) {
      setError("تکرار رمز عبور با رمز عبور جدید مطابقت ندارد.");
      return;
    }

    setSaving(true);
    const { success, message } = await changePassword(username, currentPassword, newPassword);
    setSaving(false);

    if (success) {
      onSuccess?.();
    } else {
      setError(message);
    }
  }

  return (
    <div className="dialog-overlay" onClick={onClose}>
      <div
        className="dialog-box"
        role="dialog"
        aria-modal="true"
        onClick={(e) => e.stopPropagation()}
      >
        <h2>تغییر رمز عبور</h2>

        <label>رمز عبور فعلی</label>
        <input
          type="password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />

        <label>رمز عبور جدید</label>
        <input
          type="password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />

        <label>تکرار رمز عبور جدید</label>
        <input
          type="password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />

        {error && <div className="stAlert-error">{error}</div>}

        <div className="dialog-buttons">
          <button type="button" className="dialog-btn-save" disabled={saving} onClick={handleSave}>
            ذخیره
          </button>
          <button type="button" className="dialog-btn-cancel" onClick={onClose}>
            انصراف
          </button>
        </div>
      </div>
    </div>
  );
}
