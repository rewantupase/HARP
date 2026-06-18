interface RoutingInfo {
  tier: string;
  provider_name: string;
  reason: string;
  latency_ms?: number;
}

export function RoutingDiagnostics({ routing }: { routing: RoutingInfo }) {
  const tierColor: Record<string, string> = {
    simple: "bg-green-100 text-green-800",
    medium: "bg-yellow-100 text-yellow-800",
    complex: "bg-orange-100 text-orange-800",
    fallback: "bg-red-100 text-red-800",
  };
  return (
    <div className="flex items-center gap-2 text-xs text-muted-foreground mt-1">
      <span className={`px-1.5 py-0.5 rounded text-xs font-mono ${tierColor[routing.tier] ?? ""}`}>
        {routing.provider_name}
      </span>
      <span>{routing.reason}</span>
      {routing.latency_ms && <span>{routing.latency_ms}ms</span>}
    </div>
  );
}
