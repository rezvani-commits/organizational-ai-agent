import { useEffect, useRef, useState } from "react";

/**
 * components/InputBox.jsx
 * -------------------------
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
          aria-label="ارسال"
          title="ارسال"
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            style={{ transform: "scaleX(-1) translateY(3px)"}}
          >
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
