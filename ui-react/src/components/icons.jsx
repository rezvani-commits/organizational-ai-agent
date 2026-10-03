

let gradientIdCounter = 0;

export function BrandIcon({ size = 28 }) {
  const gradientId = `niroyar-spark-grad-${gradientIdCounter++}`;

  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={gradientId} x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#c084fc" />
          <stop offset="50%" stopColor="#8b5cf6" />
          <stop offset="100%" stopColor="#6366f1" />
        </linearGradient>
      </defs>

      {/* درخشش اصلی */}
      <path
        d="M12.5 2.5c.55 2.7 1.15 4.4 2.2 5.5s2.8 1.65 5.5 2.2c-2.7.55-4.4 1.15-5.5 2.2s-1.65 2.8-2.2 5.5c-.55-2.7-1.15-4.4-2.2-5.5S7.5 10.8 4.8 10.2c2.7-.55 4.4-1.15 5.5-2.2s1.65-2.8 2.2-5.5Z"
        fill={`url(#${gradientId})`}
      />

      {/* درخشش کوچک همراه */}
      <path
        d="M18.5 15.2c.28 1.15.58 1.85 1.05 2.3.47.45 1.2.73 2.35 1-1.15.28-1.88.55-2.35 1-.47.45-.77 1.15-1.05 2.3-.28-1.15-.58-1.85-1.05-2.3-.47-.45-1.2-.72-2.35-1 1.15-.28 1.88-.55 2.35-1 .47-.45.77-1.15 1.05-2.3Z"
        fill={`url(#${gradientId})`}
        opacity="0.85"
      />
    </svg>
  );
}

export function DeleteIcon({ size = 15 }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <path
        d="M4 7h16M9.5 7V5a1.5 1.5 0 0 1 1.5-1.5h2A1.5 1.5 0 0 1 14.5 5v2M6.5 7l.75 12.15A2 2 0 0 0 9.24 21h5.52a2 2 0 0 0 1.99-1.85L17.5 7"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M10 11v6M14 11v6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}
