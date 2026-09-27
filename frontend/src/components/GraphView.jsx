const TYPE_COLOR = {
  Email: "#60a5fa",
  Domain: "#38bdf8",
  IP: "#c084fc",
  URL: "#fb923c",
};

export default function GraphView({ graph }) {
  if (!graph || !graph.nodes?.length) {
    return (
      <p className="text-soc-muted text-sm">
        No graph data — Neo4j may be unreachable, or this case has no linked infrastructure.
      </p>
    );
  }

  const center = graph.nodes.find((n) => n.type === "Email") || graph.nodes[0];
  const others = graph.nodes.filter((n) => n.id !== center.id);

  const W = 640, H = 420, cx = W / 2, cy = H / 2, radius = 160;
  const positions = { [center.id]: { x: cx, y: cy } };
  others.forEach((n, i) => {
    const angle = (2 * Math.PI * i) / Math.max(others.length, 1);
    positions[n.id] = { x: cx + radius * Math.cos(angle), y: cy + radius * Math.sin(angle) };
  });

  return (
    <svg width="100%" viewBox={`0 0 ${W} ${H}`} className="bg-soc-bg rounded-lg border border-soc-border">
      {graph.edges.map((e, i) => {
        const s = positions[e.source], t = positions[e.target];
        if (!s || !t) return null;
        return (
          <g key={i}>
            <line x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="#2a3644" strokeWidth="1.5" />
            <text
              x={(s.x + t.x) / 2} y={(s.y + t.y) / 2 - 4}
              fontSize="9" fill="#5b6b7d" textAnchor="middle"
            >
              {e.type.replace(/_/g, " ").toLowerCase()}
            </text>
          </g>
        );
      })}
      {graph.nodes.map((n) => {
        const p = positions[n.id];
        if (!p) return null;
        const color = TYPE_COLOR[n.type] || "#7c8a9c";
        const isCenter = n.id === center.id;
        return (
          <g key={n.id}>
            <circle cx={p.x} cy={p.y} r={isCenter ? 26 : 18} fill={`${color}22`} stroke={color} strokeWidth="2" />
            <text x={p.x} y={p.y + 34} fontSize="10" fill="#d7e1ea" textAnchor="middle">
              {String(n.label || "").slice(0, 22)}
            </text>
            <text x={p.x} y={p.y + 4} fontSize="9" fill={color} textAnchor="middle" fontWeight="600">
              {n.type[0]}
            </text>
          </g>
        );
      })}
    </svg>
  );
}
