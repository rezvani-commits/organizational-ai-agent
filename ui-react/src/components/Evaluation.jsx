

function extractScore(value) {
  if (value == null) return null;
  if (typeof value === "object") value = value.score;
  if (value == null) return null;
  const num = Number(value);
  return Number.isNaN(num) ? null : num;
}

function toPercent(value) {
  const score = extractScore(value);
  if (score == null) return null;
  return Math.max(0, Math.min(100, Math.round(score * 10)));
}

function fmt(value) {
  return value != null ? `${value}%` : "—";
}

export default function Evaluation({ scores }) {
  if (!scores) return null;

  const relevance = toPercent(scores.relevance);
  const completeness = toPercent(scores.completeness);
  const faithfulness = toPercent(scores.faithfulness);
  const overall = toPercent(scores.overall);

  if (relevance == null && completeness == null && faithfulness == null && overall == null) {
    return null;
  }

  const metrics = [
    { label: "ارتباط", value: relevance },
    { label: "کامل بودن", value: completeness },
    { label: "صحت", value: faithfulness },
    { label: "امتیاز کلی", value: overall },
  ];

  return (
    <div className="evaluation-section">
      <div className="evaluation-title">📊 ارزیابی کیفیت پاسخ</div>
      <div className="evaluation-items">
        {metrics.map((m) => (
          <div className="evaluation-item" key={m.label}>
            {m.label}: <strong>{fmt(m.value)}</strong>
          </div>
        ))}
      </div>
    </div>
  );
}
