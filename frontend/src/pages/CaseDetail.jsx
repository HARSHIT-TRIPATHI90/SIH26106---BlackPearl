import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getCase, getCaseGraph, getRelatedCases, getEvidenceTrail } from "../api.js";
import RiskGauge from "../components/RiskGauge.jsx";
import IOCTable from "../components/IOCTable.jsx";
import GraphView from "../components/GraphView.jsx";

const AUTH_COLOR = { pass: "text-green-400", fail: "text-red-400", softfail: "text-orange-400", none: "text-soc-muted", neutral: "text-soc-muted" };

function AuthPill({ label, value }) {
  return (
    <div className="bg-soc-bg border border-soc-border rounded-lg px-3 py-2 text-center">
      <p className="text-xs text-soc-muted">{label}</p>
      <p className={`font-bold uppercase ${AUTH_COLOR[value] || "text-soc-muted"}`}>{value || "none"}</p>
    </div>
  );
}

export default function CaseDetail() {
  const { id } = useParams();
  const [c, setCase] = useState(null);
  const [graph, setGraph] = useState(null);
  const [related, setRelated] = useState([]);
  const [trail, setTrail] = useState([]);
  const [tab, setTab] = useState("overview");
  const [err, setErr] = useState(null);

  useEffect(() => {
    getCase(id).then(setCase).catch((e) => setErr(e.message));
    getCaseGraph(id).then(setGraph).catch(() => setGraph(null));
    getRelatedCases(id).then(setRelated).catch(() => setRelated([]));
    getEvidenceTrail(id).then(setTrail).catch(() => setTrail([]));
  }, [id]);

  if (err) return <div className="p-8 text-red-400">{err}</div>;
  if (!c) return <div className="p-8 text-soc-muted">Loading case…</div>;

  return (
    <div className="max-w-6xl mx-auto px-6 py-8">
      <Link to="/" className="text-soc-muted text-sm hover:text-soc-text">&larr; Back to dashboard</Link>

      <header className="mt-3 mb-6 flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold">{c.subject || "(no subject)"}</h1>
          <p className="text-soc-muted text-sm mt-1">
            From <span className="text-soc-text">{c.sender}</span> → {c.to_addr}
          </p>
          <p className="text-soc-muted text-xs mt-1">Case ID: {c.id}</p>
        </div>
        <RiskGauge score={c.risk_score} level={c.risk_level} />
      </header>

      <nav className="flex gap-1 mb-6 border-b border-soc-border">
        {["overview", "headers", "ai", "iocs", "graph", "evidence"].map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm capitalize border-b-2 transition-colors
              ${tab === t ? "border-blue-400 text-soc-text" : "border-transparent text-soc-muted hover:text-soc-text"}`}
          >
            {t}
          </button>
        ))}
      </nav>

      {tab === "overview" && (
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-soc-panel border border-soc-border rounded-xl p-4">
            <h3 className="font-semibold mb-2">AI Verdict</h3>
            <p className="text-2xl font-bold capitalize mb-1">{c.ai_verdict}</p>
            <p className="text-soc-muted text-sm">Confidence: {(c.ai_confidence * 100).toFixed(0)}%</p>
          </div>
          <div className="bg-soc-panel border border-soc-border rounded-xl p-4">
            <h3 className="font-semibold mb-2">Risk Breakdown</h3>
            <ul className="text-sm space-y-1">
              {c.risk_breakdown && Object.entries(c.risk_breakdown).map(([k, v]) => (
                <li key={k} className="flex justify-between">
                  <span className="text-soc-muted">{k.replace(/_/g, " ")}</span>
                  <span>+{v}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="col-span-2 bg-soc-panel border border-soc-border rounded-xl p-4">
            <h3 className="font-semibold mb-2">Header Anomalies</h3>
            {c.auth_anomalies?.length ? (
              <ul className="text-sm space-y-1 list-disc list-inside text-soc-text">
                {c.auth_anomalies.map((a, i) => <li key={i}>{a}</li>)}
              </ul>
            ) : (
              <p className="text-soc-muted text-sm">None detected.</p>
            )}
          </div>
          {related.length > 0 && (
            <div className="col-span-2 bg-soc-panel border border-soc-border rounded-xl p-4">
              <h3 className="font-semibold mb-2">Related Campaign Cases (shared infrastructure)</h3>
              <ul className="text-sm space-y-2">
                {related.map((r) => (
                  <li key={r.case_id} className="flex justify-between">
                    <Link to={`/cases/${r.case_id}`} className="text-blue-400 hover:underline truncate max-w-xs">
                      {r.subject}
                    </Link>
                    <span className="text-soc-muted text-xs">shared {r.shared_type}: {r.shared_value}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {tab === "headers" && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-3">
            <AuthPill label="SPF" value={c.spf_result} />
            <AuthPill label="DKIM" value={c.dkim_result} />
            <AuthPill label="DMARC" value={c.dmarc_result} />
          </div>
          <div className="bg-soc-panel border border-soc-border rounded-xl p-4">
            <h3 className="font-semibold mb-3">Relay Path (origin → destination)</h3>
            <div className="space-y-2">
              {c.relay_path?.map((hop, i) => (
                <div key={i} className="flex items-center gap-2 text-sm font-mono">
                  <span className="text-soc-muted w-6">{i + 1}.</span>
                  <span>{hop.from || "?"}</span>
                  <span className="text-soc-muted">→</span>
                  <span>{hop.by || "?"}</span>
                  {hop.ip && <span className="text-purple-300 ml-2">[{hop.ip}]</span>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === "ai" && (
        <div className="bg-soc-panel border border-soc-border rounded-xl p-4 space-y-4">
          <div>
            <h3 className="font-semibold mb-1">Gemini Reasoning</h3>
            <p className="text-sm text-soc-text">{c.ai_reasoning}</p>
          </div>
          <div>
            <h3 className="font-semibold mb-1">Indicators Flagged</h3>
            <div className="flex flex-wrap gap-2">
              {c.ai_indicators?.map((ind, i) => (
                <span key={i} className="px-2 py-1 bg-blue-500/10 text-blue-300 rounded text-xs">{ind}</span>
              ))}
            </div>
          </div>
        </div>
      )}

      {tab === "iocs" && (
        <div className="bg-soc-panel border border-soc-border rounded-xl p-4">
          <IOCTable iocs={c.iocs} />
        </div>
      )}

      {tab === "graph" && (
        <div className="bg-soc-panel border border-soc-border rounded-xl p-4">
          <GraphView graph={graph} />
        </div>
      )}

      {tab === "evidence" && (
        <div className="bg-soc-panel border border-soc-border rounded-xl p-4">
          <h3 className="font-semibold mb-3">Tamper-Evident Ledger Trail</h3>
          <p className="text-soc-muted text-xs mb-3">
            SHA-256 hash chain — each entry commits to the hash of the previous one.
            Altering any past record breaks every hash after it. Not a distributed blockchain; an honest append-only ledger.
          </p>
          {trail.map((t) => (
            <div key={t.seq} className="border-t border-soc-border py-2 text-xs font-mono">
              <p>seq {t.seq} · {t.event_type} · {t.timestamp}</p>
              <p className="text-soc-muted truncate">hash: {t.record_hash}</p>
              <p className="text-soc-muted truncate">prev: {t.prev_hash}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
