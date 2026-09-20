/**
 * components/Status.jsx
 * -----------------------
 * معادل components/status.py (render_status_live / render_status_final).
 *
 * در نسخه‌ی پایتون این وضعیت با یک ترد پس‌زمینه + polling روی
 * status_store به‌روزرسانی می‌شد. در React نیازی به polling نیست -
 * همان state پردازشِ چت (processingStep) به‌طور طبیعی این کامپوننت را
 * دوباره رندر می‌کند.
 */

const RAG_LOOP_STEPS = ["جستجو در اسناد", "آماده‌سازی اطلاعات مرتبط", "تولید پاسخ", "ارزیابی پاسخ"];

export function StatusLive({ currentLabel, isError = false, errorMessage = "" }) {
  if (isError) {
    return (
      <div className="chat-status chat-status-error">
        <div className="chat-status-title">
          <span className="status-error-icon">⚠</span>
          <span>خطا در پردازش{errorMessage ? `: ${errorMessage}` : ""}</span>
        </div>
      </div>
    );
  }

  const showFullChecklist = RAG_LOOP_STEPS.includes(currentLabel);
  const currentIndex = showFullChecklist ? RAG_LOOP_STEPS.indexOf(currentLabel) : -1;

  return (
    <div className="chat-status">
      <div className="chat-status-title">
        <span className="status-spinner" />
        <span>در حال پردازش...</span>
      </div>

      <div className="chat-status-steps">
        {!showFullChecklist ? (
          <div className="chat-status-step" style={{ color: "#FFFFFF" }}>
            <span className="status-spinner-small" />
            <span>{currentLabel || "در حال پردازش"}</span>
          </div>
        ) : (
          RAG_LOOP_STEPS.map((step, index) => {
            let icon;
            let color;
            if (index < currentIndex) {
              icon = <span className="status-check">✓</span>;
              color = "#AFAFAF";
            } else if (index === currentIndex) {
              icon = <span className="status-spinner-small" />;
              color = "#FFFFFF";
            } else {
              icon = <span className="status-pending" />;
              color = "#666666";
            }
            return (
              <div className="chat-status-step" style={{ color }} key={step}>
                {icon}
                <span>{step}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export function StatusFinal() {
  return (
    <div className="chat-status chat-status-final">
      <div className="chat-status-title">
        <span className="status-check">✓</span>
        <span>پردازش کامل شد</span>
      </div>
    </div>
  );
}
