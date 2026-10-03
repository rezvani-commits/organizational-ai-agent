import { useState, useEffect, useRef } from "react";


function CitationPopover({ source, isOpen, onToggle }) {
  const name = source.name || "بدون عنوان";
  const page = source.page ?? "-";
  const content = (source.content || "").trim();

  return (
    <div className="citation-popover-wrapper">
      <button
        type="button"
        className="citation-item citation-button"
        onClick={onToggle}
      >
        <span className="citation-icon">📄</span>
        <span className="citation-name">{name}</span>
        <span className="citation-page">({page})</span>
      </button>

      {isOpen && (
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
  const [openIdx, setOpenIdx] = useState(null);
  const sectionRef = useRef(null);

  useEffect(() => {
    if (openIdx === null) return;
    const handleClickOutside = (e) => {
      if (sectionRef.current && !sectionRef.current.contains(e.target)) {
        setOpenIdx(null);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [openIdx]);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="citations-section" ref={sectionRef}>
      <div className="citations-title">📚 منابع و مستندات بازیابی‌شده</div>
      <div className="citations-list">
        {sources.map((source, idx) => (
          <CitationPopover
            key={idx}
            source={source}
            isOpen={openIdx === idx}
            onToggle={() => setOpenIdx((cur) => (cur === idx ? null : idx))}
          />
        ))}
      </div>
    </div>
  );
}