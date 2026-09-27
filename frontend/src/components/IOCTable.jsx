const TYPE_BADGE = {
  ip: "bg-purple-500/15 text-purple-300",
  domain: "bg-blue-500/15 text-blue-300",
  url: "bg-orange-500/15 text-orange-300",
};

export default function IOCTable({ iocs = [] }) {
  if (!iocs.length) {
    return <p className="text-soc-muted text-sm">No indicators of compromise extracted.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-soc-muted border-b border-soc-border">
            <th className="py-2 pr-4">Type</th>
            <th className="py-2 pr-4">Value</th>
            <th className="py-2 pr-4">Location</th>
            <th className="py-2 pr-4">ISP / Org</th>
            <th className="py-2 pr-4">Proxy/Hosting</th>
          </tr>
        </thead>
        <tbody>
          {iocs.map((ioc, idx) => (
            <tr key={idx} className="border-b border-soc-border/50">
              <td className="py-2 pr-4">
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${TYPE_BADGE[ioc.ioc_type] || ""}`}>
                  {ioc.ioc_type.toUpperCase()}
                </span>
              </td>
              <td className="py-2 pr-4 font-mono text-xs break-all max-w-xs">{ioc.value}</td>
              <td className="py-2 pr-4 text-soc-muted">
                {[ioc.city, ioc.region, ioc.country].filter(Boolean).join(", ") || "—"}
              </td>
              <td className="py-2 pr-4 text-soc-muted">{ioc.isp || ioc.org || "—"}</td>
              <td className="py-2 pr-4">
                {ioc.is_proxy ? (
                  <span className="text-red-400 text-xs font-medium">⚠ Yes</span>
                ) : ioc.ioc_type === "ip" ? (
                  <span className="text-soc-muted text-xs">No</span>
                ) : (
                  <span className="text-soc-muted text-xs">—</span>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
