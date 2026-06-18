import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const MODELS = [
  { value: "auto", label: "Auto (Router decides)" },
  { value: "phi3", label: "Phi-3 Mini (Fast)" },
  { value: "mistral", label: "Mistral 7B (Balanced)" },
  { value: "llama3", label: "Llama 3 8B (Complex)" },
  { value: "openai", label: "OpenAI (Cloud fallback)" },
];

interface Props {
  value: string;
  onChange: (v: string) => void;
}

export function ModelSelector({ value, onChange }: Props) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-48 h-8 text-xs">
        <SelectValue placeholder="Select model" />
      </SelectTrigger>
      <SelectContent>
        {MODELS.map((m) => (
          <SelectItem key={m.value} value={m.value} className="text-xs">
            {m.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
