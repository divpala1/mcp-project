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
      className="text-canvas-text-dim hover:text-canvas-text-subtle transition-colors rounded-md p-1 hover:bg-canvas-overlay"
      title="Copy"
    >
      {copied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
    </button>
  );
}

function JsonBlock({ label, value }: { label: string; value: string }) {
  return (
    <div className="px-3 py-3 border-t border-canvas-border">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[9px] font-bold text-canvas-text-dim uppercase tracking-widest font-sans">
          {label}
        </span>
        <CopyButton text={value} />
      </div>
      <pre className="text-[11px] text-canvas-text-muted leading-relaxed overflow-x-auto whitespace-pre-wrap break-words max-h-44 font-mono">
        {value}
      </pre>
    </div>
  );
}

const STATUS_CONFIG = {
  running: {
    icon: <Loader2 size={11} className="text-violet-400 animate-spin" />,
    badge: 'text-violet-300 bg-violet-500/10 border-violet-500/25',
    bar:   'bg-violet-600',
    label: 'Running',
  },
  done: {
    icon: <CheckCircle2 size={11} className="text-emerald-400" />,
    badge: 'text-emerald-300 bg-emerald-500/10 border-emerald-500/25',
    bar:   'bg-emerald-600',
    label: 'Done',
  },
  error: {
    icon: <XCircle size={11} className="text-red-400" />,
    badge: 'text-red-300 bg-red-500/10 border-red-500/25',
    bar:   'bg-red-600',
    label: 'Error',
  },
} as const;

export default function ToolCallCard({ toolCall }: { toolCall: ToolCall }) {
  const [expanded, setExpanded] = useState(false);
  const status = STATUS_CONFIG[toolCall.status];

  const argsJson = JSON.stringify(toolCall.args, null, 2);
  const outputStr =
    toolCall.output === undefined
      ? ''
      : typeof toolCall.output === 'string'
      ? toolCall.output
      : JSON.stringify(toolCall.output, null, 2);

  return (
    <div className="w-full bg-canvas-muted border border-canvas-border rounded-xl overflow-hidden font-mono text-xs shadow-card">
      {/* Top status bar */}
      <div className={`h-[2px] ${status.bar} transition-colors duration-300`} />

      <button
        className="w-full flex items-center gap-2.5 px-3 py-2.5 hover:bg-canvas-overlay/60 transition-colors duration-150"
        onClick={() => setExpanded((v) => !v)}
      >
        {/* Tool icon */}
        <span className="w-5 h-5 rounded bg-canvas-card border border-canvas-border flex items-center justify-center flex-shrink-0">
          <Wrench size={10} className="text-canvas-text-muted" />
        </span>

        {/* Tool name */}
        <span className="text-canvas-text font-medium flex-1 text-left truncate text-[12px]">
          {toolCall.name}
        </span>

        {/* Status badge */}
        <span
          className={[
            'hidden sm:inline text-[9px] font-bold font-sans uppercase tracking-wider px-1.5 py-0.5 rounded border',
            status.badge,
          ].join(' ')}
        >
          {status.label}
        </span>

        {status.icon}

        {expanded ? (
          <ChevronDown size={12} className="text-canvas-text-dim flex-shrink-0" />
        ) : (
          <ChevronRight size={12} className="text-canvas-text-dim flex-shrink-0" />
        )}
      </button>

      {expanded && (
        <div className="animate-fade-in">
          <JsonBlock label="Input" value={argsJson} />
          {outputStr && <JsonBlock label="Output" value={outputStr} />}
        </div>
      )}
    </div>
  );
}
