import { useEffect, useState } from "react";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { api } from "@/lib/api";

interface Props {
  threadId: string;
  open: boolean;
  onClose: () => void;
}

export function MemoryViewer({ threadId, open, onClose }: Props) {
  const [messages, setMessages] = useState<any[]>([]);
  const [summary, setSummary] = useState<string>("");

  useEffect(() => {
    if (!open) return;
    api.get(`/memory/${threadId}`).then((r) => {
      setMessages(r.data.messages ?? []);
      setSummary(r.data.summary ?? "");
    });
  }, [open, threadId]);

  return (
    <Sheet open={open} onOpenChange={onClose}>
      <SheetContent side="right" className="w-[400px] overflow-y-auto">
        <SheetHeader>
          <SheetTitle>Conversation Memory</SheetTitle>
        </SheetHeader>
        {summary && (
          <div className="mt-4 p-3 bg-muted rounded text-sm">
            <div className="font-semibold mb-1 text-xs uppercase tracking-wide text-muted-foreground">Summary</div>
            {summary}
          </div>
        )}
        <div className="mt-4 space-y-2">
          {messages.map((m, i) => (
            <div key={i} className={`p-2 rounded text-xs ${m.role === "user" ? "bg-blue-50" : "bg-gray-50"}`}>
              <span className="font-semibold uppercase text-muted-foreground">{m.role}: </span>
              {m.content}
            </div>
          ))}
        </div>
      </SheetContent>
    </Sheet>
  );
}
