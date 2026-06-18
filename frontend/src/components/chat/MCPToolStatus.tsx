import { useEffect, useState } from "react";
import { api } from "@/lib/api";

const TOOLS = ["document_search", "document_upload", "chat_history_lookup", "document_metadata_lookup"];

export function MCPToolStatus() {
  const [health, setHealth] = useState<Record<string, boolean>>({});

  useEffect(() => {
    api.get("/health/mcp").then((r) => setHealth(r.data));
  }, []);

  return (
    <div className="text-xs space-y-1 p-2">
      <div className="font-semibold text-muted-foreground uppercase tracking-wide mb-2">MCP Tools</div>
      {TOOLS.map((t) => (
        <div key={t} className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${health[t] ? "bg-green-500" : "bg-gray-300"}`} />
          <span className="font-mono">{t}</span>
        </div>
      ))}
    </div>
  );
}
