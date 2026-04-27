import { useState } from 'react';
import {
  Wrench,
  ChevronRight,
  ChevronDown,
  Loader2,
  CheckCircle2,
  XCircle,
  Copy,
  Check,
} from 'lucide-react';
import type { ToolCall } from '../../types';

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="text-zinc-700 hover:text-zinc-400 transition-colors rounded p-0.5"
      title="Copy"
    >
      {copied ? <Check size={11} className="text-green-400" /> : <Copy size={11} />}
    </button>
  );
}

function JsonBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-3 py-2.5 border-t border-zinc-800/80">
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] font-semibold text-zinc-600 uppercase tracking-wider font-sans">
          {label}
        </span>
        <CopyButton text={value} />
      </div>
      <pre className="text-[11px] text-zinc-400 leading-relaxed overflow-x-auto whitespace-pre-wrap break-words max-h-40">
        {value}
      </pre>
    </div>
  );
}

export default function ToolCallCard({ toolCall }: { toolCall: ToolCall }) {
  const [expanded, setExpanded] = useState(false);

  const statusIcon = {
    running: <Loader2 size={12} className="text-blue-400 animate-spin" />,
    done: <CheckCircle2 size={12} className="text-emerald-400" />,
    error: <XCircle size={12} className="text-red-400" />,
  }[toolCall.status];

  const argsJson = JSON.stringify(toolCall.args, null, 2);
  const outputStr =
    toolCall.output === undefined
      ? ''
      : typeof toolCall.output === 'string'
      ? toolCall.output
      : JSON.stringify(toolCall.output, null, 2);

  return (
    <div className="w-full bg-zinc-900 border border-zinc-700/50 rounded-xl overflow-hidden font-mono text-xs">
      <button
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-zinc-800/40 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <Wrench size={12} className="text-zinc-600 flex-shrink-0" />
        <span className="text-zinc-300 font-medium flex-1 text-left truncate">{toolCall.name}</span>
        {statusIcon}
        {expanded ? (
          <ChevronDown size={12} className="text-zinc-700" />
        ) : (
          <ChevronRight size={12} className="text-zinc-700" />
        )}
      </button>

      {expanded && (
        <>
          <JsonBlock label="Input" value={argsJson} />
          {outputStr && <JsonBlock label="Output" value={outputStr} />}
        </>
      )}
    </div>
  );
}
