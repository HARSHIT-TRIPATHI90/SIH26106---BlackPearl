import { Link } from "react-router-dom";

const LEVEL_COLORS = {
  low: "text-green-400 bg-green-400/10",
  medium: "text-yellow-400 bg-yellow-400/10",
  high: "text-orange-400 bg-orange-400/10",
  critical: "text-red-400 bg-red-400/10",
};

export default function CaseList({ cases = [] }) {
  if (!cases.length) {
    return <p className="text-soc-muted text-sm">No cases analyzed yet.</p>;
  }

  return (
    <div className="divide-y divide-soc-border">
      {cases.map((c) => (
        <Link
          key={c.id}
          to={`/cases/${c.id}`}
          className="flex items-center justify-between py-3 px-2 hover:bg-soc-panel/60 rounded transition-colors"
        >
          <div className="min-w-0">
            <p className="truncate font-medium">{c.subject || "(no subject)"}</p>
            <p className="text-xs text-soc-muted truncate">{c.sender} · {new Date(c.created_at).toLocaleString()}</p>
          </div>
          <div className="flex items-center gap-3 shrink-0 ml-4">
            <span className="text-xs uppercase text-soc-muted">{c.ai_verdict}</span>
            <span className={`px-2 py-1 rounded text-xs font-semibold ${LEVEL_COLORS[c.risk_level] || ""}`}>
              {c.risk_score ?? "—"}
            </span>
          </div>
        </Link>
      ))}
    </div>
  );
}
