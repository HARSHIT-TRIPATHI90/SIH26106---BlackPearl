import { useState, useRef } from "react";

export default function UploadBox({ onAnalyze, loading }) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleFile = (file) => {
    if (!file) return;
    if (!file.name.endsWith(".eml") && !file.name.endsWith(".txt")) {
      alert("Upload a raw .eml file (View Source / Show Original from your mail client).");
      return;
    }
    onAnalyze(file);
  };

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragOver(false);
        handleFile(e.dataTransfer.files[0]);
      }}
      onClick={() => !loading && inputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors
        ${dragOver ? "border-blue-400 bg-blue-400/5" : "border-soc-border bg-soc-panel"}
        ${loading ? "opacity-60 pointer-events-none" : "hover:border-blue-400/60"}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".eml,.txt"
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />
      {loading ? (
        <div>
          <div className="animate-spin h-8 w-8 border-2 border-blue-400 border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-soc-muted">Parsing headers → Gemini analysis → geolocation → risk scoring…</p>
        </div>
      ) : (
        <div>
          <p className="text-lg font-medium mb-1">Drop a .eml file here, or click to browse</p>
          <p className="text-soc-muted text-sm">Raw email source (headers included) — not a .msg or forwarded copy</p>
        </div>
      )}
    </div>
  );
}
