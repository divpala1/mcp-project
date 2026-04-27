import { useState, useRef, useCallback } from 'react';
import { Send, Square, Brain } from 'lucide-react';

interface ChatInputProps {
  onSend: (prompt: string, enableThinking: boolean) => void;
  onCancel: () => void;
  isStreaming: boolean;
  disabled?: boolean;
  enableThinking: boolean;
  onToggleThinking: () => void;
}

export default function ChatInput({ onSend, onCancel, isStreaming, disabled, enableThinking, onToggleThinking }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSend(trimmed, enableThinking);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }, [value, isStreaming, disabled, onSend, enableThinking]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 200)}px`;
  };

  const canSend = value.trim().length > 0 && !isStreaming && !disabled;

  return (
    <div className="flex-shrink-0 px-5 pb-5 pt-3">
      <div
        className={[
          'flex items-end gap-3 border rounded-2xl px-4 py-3 transition-all duration-200',
          'bg-canvas-card shadow-card',
          disabled
            ? 'border-canvas-border opacity-60'
            : 'border-canvas-border focus-within:border-violet-600/40 focus-within:shadow-glow-sm',
        ].join(' ')}
      >
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={disabled ? 'Configure auth token in Settings…' : 'Message the agent…'}
          disabled={disabled || isStreaming}
          rows={1}
          className="flex-1 bg-transparent text-sm text-canvas-text placeholder-canvas-text-dim resize-none outline-none leading-relaxed disabled:opacity-50 min-h-[22px] max-h-[200px]"
        />

        <button
          type="button"
          onClick={onToggleThinking}
          disabled={isStreaming}
          className={[
            'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-150',
            enableThinking
              ? 'bg-violet-600/20 text-violet-400 ring-1 ring-violet-600/40'
              : 'text-canvas-text-dim hover:text-canvas-text-subtle hover:bg-canvas-overlay',
            isStreaming ? 'opacity-40 cursor-not-allowed' : '',
          ].join(' ')}
          title={enableThinking ? 'Think mode on — click to disable' : 'Enable think mode for this message'}
        >
          <Brain size={14} />
        </button>

        <button
          onClick={isStreaming ? onCancel : handleSend}
          disabled={!isStreaming && !canSend}
          className={[
            'flex-shrink-0 w-8 h-8 rounded-xl flex items-center justify-center transition-all duration-150',
            isStreaming
              ? 'bg-red-600/90 hover:bg-red-500 text-white'
              : canSend
              ? 'bg-violet-600 hover:bg-violet-500 text-white shadow-glow-sm'
              : 'bg-canvas-overlay text-canvas-text-dim cursor-not-allowed',
          ].join(' ')}
          title={isStreaming ? 'Cancel' : 'Send (Enter)'}
        >
          {isStreaming ? <Square size={11} fill="currentColor" /> : <Send size={13} />}
        </button>
      </div>

      <p className="text-[10px] text-canvas-text-dim mt-1.5 px-1">
        <span className="font-mono">↵</span> to send ·{' '}
        <span className="font-mono">⇧↵</span> for newline ·{' '}
        <span className={enableThinking ? 'text-violet-400' : ''}>
          think {enableThinking ? 'on' : 'off'}
        </span>
      </p>
    </div>
  );
}
