import { Check, Copy } from "lucide-react";
import { useState } from "react";

export function CopyButton({
  value,
  label = "Копировать",
}: {
  value: string;
  label?: string;
}) {
  const [copied, setCopied] = useState(false);
  async function copy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  }
  return (
    <button type="button" className="copy-button" onClick={copy}>
      {copied ? <Check size={16} /> : <Copy size={16} />}
      {copied ? "Скопировано" : label}
    </button>
  );
}
