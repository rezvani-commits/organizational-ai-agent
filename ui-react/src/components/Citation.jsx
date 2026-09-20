import { useState } from "react";

/**
 * components/Citation.jsx
 * -------------------------
 * معادل components/citation.py (render_citations).
 *
 * هر منبع یک دکمه‌ی کوچک است که با کلیک، یک پاپ‌آور با جزئیات
 * (نام سند، موقعیت، پیش‌نمایش متن) باز می‌کند.
 */

function CitationPopover({ source }) {
  const [open, setOpen] = useState(false);
  const name = source.name || "بدون عنوان";
  const page = source.page ?? "-";
  const content = (source.content || "").trim();

  return (
    <div className="citation-popover-wrapper">
      <button
        type="button"
        className="citation-item citation-button"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="citation-icon">📄</span>
        <span className="citation-name">{name}</span>
        <span className="citation-page">({page})</span>
      </button>

      {open && (
        <div className="citation-popover">
          <div>
            <strong>سند:</strong> {name}
          </div>
          <div>
            <strong>موقعیت:</strong> {page}
          </div>
          {content ? (
            <div className="citation-popover-content">{content}</div>
          ) : (
            <div className="citation-popover-empty">
              متنی برای پیش‌نمایش این منبع در دسترس نیست.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function Citations({ sources }) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="citations-section">
      <div className="citations-title">📚 منابع و مستندات بازیابی‌شده</div>
      <div className="citations-list">
        {sources.map((source, idx) => (
          <CitationPopover key={idx} source={source} />
        ))}
      </div>
    </div>
  );
}
