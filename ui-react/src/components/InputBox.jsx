import { useEffect, useRef, useState } from "react";

/**
 * components/InputBox.jsx
 * -------------------------
 * معادل components/input_box.py (render_input_box).
 *
 * @param {boolean} disabled - غیرفعال کردن در حین پردازش
 * @param {string|null} defaultValue - مقدار پیش‌فرض (سوال پیشنهادی انتخاب‌شده)
 * @param {(value: string) => void} onSubmit
 */
export default function InputBox({ disabled = false, defaultValue = null, onSubmit }) {
  const [value, setValue] = useState(defaultValue || "");
  const textareaRef = useRef(null);

  useEffect(() => {
    if (defaultValue) {
      setValue(defaultValue);
      textareaRef.current?.focus();
    }
  }, [defaultValue]);

  const placeholder = disabled ? "در حال پردازش..." : "سوال خود را بپرسید...";

  function handleSubmit() {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSubmit?.(trimmed);
    setValue("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="chat-input-bar">
      <div className="chat-input-box">
        <textarea
          ref={textareaRef}
          className="chat-input-textarea"
          placeholder={placeholder}
          value={value}
          disabled={disabled}
          rows={1}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
        />
        <button
          type="button"
          className="chat-input-send"
          disabled={disabled || !value.trim()}
          onClick={handleSubmit}
        >
          📤
        </button>
      </div>
    </div>
  );
}
