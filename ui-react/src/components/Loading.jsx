

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
