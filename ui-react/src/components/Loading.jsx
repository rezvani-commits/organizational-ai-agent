/**
 * components/Loading.jsx
 * -----------------------
 * معادل components/loading.py (show_loading_page).
 *
 * یک صفحه‌ی تمام‌صفحه‌ی لودینگ که تا وقتی initFn (کار سنگین راه‌اندازی)
 * تمام نشده نمایش داده می‌شود.
 */

import { BrandIcon } from "./icons";

export default function Loading({
  title = "در حال آماده‌سازی نیرویار",
  subtitle = "لطفاً چند لحظه صبر کنید...",
}) {
  return (
    <div className="loading-page">
      <div className="loading-container">
        <div className="loading-logo">
          <BrandIcon size={34} />
        </div>
        <div className="loading-title">{title}</div>
        <div className="loading-subtitle">{subtitle}</div>
        <div className="spinner" />
      </div>
    </div>
  );
}
