import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import UploadBox from "../components/UploadBox.jsx";
import CaseList from "../components/CaseList.jsx";
import { analyzeEmail, analyzeSample, listSamples, listCases } from "../api.js";

const BADGE_STYLES = {
  red: "bg-red-500/10 text-red-400 border-red-500/30",
  purple: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  green: "bg-green-500/10 text-green-400 border-green-500/30",
};

export default function Dashboard() {
  const [cases, setCases] = useState([]);
  const [samples, setSamples] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingSample, setLoadingSample] = useState(null);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const refresh = () => listCases().then(setCases).catch(() => {});

  useEffect(() => {
    refresh();
    listSamples().then(setSamples).catch(() => {});
  }, []);

  const handleAnalyze = async (file) => {
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeEmail(file);
      navigate(`/cases/${result.id}`);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSampleClick = async (sample) => {
    setLoadingSample(sample.filename);
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeSample(sample.filename);
      navigate(`/cases/${result.id}`);
    } catch (e) {
      setError(e?.response?.data?.detail || e.message || "Sample analysis failed.");
    } finally {
      setLoading(false);
      setLoadingSample(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-6 py-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <span className="text-2xl">🏴‍☠️</span>
            <h1 className="text-2xl font-bold tracking-tight">Black Pearl</h1>
          </div>
          <p className="text-soc-muted text-sm mt-1">
            AI-Powered Email Threat Forensics, Geolocation & Evidence Integrity Platform
          </p>
        </div>
      </header>

      {/* 1-Click Test Samples Section */}
      {samples.length > 0 && (
        <section className="mb-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold uppercase tracking-wider text-soc-muted flex items-center gap-2">
              <span>⚡</span> Quick Test with Preloaded Samples
            </h2>
            <span className="text-xs text-soc-muted">Click any sample to analyze instantly</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {samples.map((s) => {
              const isCurrentLoading = loadingSample === s.filename;
              return (
                <div
                  key={s.filename}
                  className="bg-soc-panel border border-soc-border hover:border-blue-400/50 rounded-xl p-4 flex flex-col justify-between transition-all duration-150 relative group"
                >
                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <span
                        className={`text-[11px] font-semibold px-2 py-0.5 rounded border ${
                          BADGE_STYLES[s.badge_color] || BADGE_STYLES.purple
                        }`}
                      >
                        {s.threat_type}
                      </span>
                      <span className="text-xs font-mono text-soc-muted opacity-60">
                        .eml
                      </span>
                    </div>
                    <h3 className="font-semibold text-sm text-soc-text mb-1 group-hover:text-blue-300 transition-colors">
                      {s.title}
                    </h3>
                    <p className="text-xs text-soc-muted leading-relaxed mb-3">
                      {s.description}
                    </p>
                  </div>

                  <button
                    disabled={loading}
                    onClick={() => handleSampleClick(s)}
                    className="w-full mt-2 py-2 px-3 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 rounded-lg text-xs font-medium flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
                  >
                    {isCurrentLoading ? (
                      <>
                        <div className="animate-spin h-3.5 w-3.5 border-2 border-blue-400 border-t-transparent rounded-full" />
                        <span>Analyzing with AI...</span>
                      </>
                    ) : (
                      <>
                        <span>▶</span>
                        <span>Analyze Sample</span>
                      </>
                    )}
                  </button>
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* Manual Upload Section */}
      <section className="mb-6">
        <div className="mb-2">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-soc-muted mb-2 flex items-center gap-2">
            <span>📁</span> Or Upload Custom Email (.eml)
          </h2>
        </div>
        <UploadBox onAnalyze={handleAnalyze} loading={loading && !loadingSample} />
      </section>

      {error && (
        <div className="mt-4 p-3.5 rounded-xl bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-200 text-xs">✕</button>
        </div>
      )}

      {/* Case History */}
      <section className="mt-10">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Analyzed Cases</h2>
          <button
            onClick={refresh}
            className="text-xs text-soc-muted hover:text-soc-text px-2.5 py-1 rounded bg-soc-panel border border-soc-border"
          >
            ↻ Refresh Cases
          </button>
        </div>
        <div className="bg-soc-panel border border-soc-border rounded-xl p-2">
          <CaseList cases={cases} />
        </div>
      </section>
    </div>
  );
}
