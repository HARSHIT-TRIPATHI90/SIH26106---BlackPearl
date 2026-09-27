const LEVEL_COLORS = {
  low: "#22c55e",
  medium: "#eab308",
  high: "#f97316",
  critical: "#ef4444",
};

export default function RiskGauge({ score = 0, level = "low" }) {
  const color = LEVEL_COLORS[level] || "#7c8a9c";
  const circumference = 2 * Math.PI * 54;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="flex flex-col items-center justify-center p-4">
      <svg width="140" height="140" viewBox="0 0 140 140">
        <circle cx="70" cy="70" r="54" fill="none" stroke="#232d3a" strokeWidth="12" />
        <circle
          cx="70" cy="70" r="54" fill="none" stroke={color} strokeWidth="12"
          strokeDasharray={circumference} strokeDashoffset={offset}
          strokeLinecap="round" transform="rotate(-90 70 70)"
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
        <text x="70" y="65" textAnchor="middle" fontSize="28" fontWeight="700" fill="#d7e1ea">
          {score}
        </text>
        <text x="70" y="85" textAnchor="middle" fontSize="11" fill="#7c8a9c">
          / 100
        </text>
      </svg>
      <div
        className="mt-2 px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide"
        style={{ backgroundColor: `${color}22`, color }}
      >
        {level}
      </div>
    </div>
  );
}
