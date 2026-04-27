import { useState, useRef, useCallback } from 'react';
import { Send, Square } from 'lucide-react';

interface ChatInputProps {
  onSend: (prompt: string) => void;
  onCancel: () => void;
  isStreaming: boolean;
  disabled?: boolean;
}

export default function ChatInput({ onSend, onCancel, isStreaming, disabled }: ChatInputProps) {
  const [value, setValue] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isStreaming || disabled) return;
    onSend(trimmed);
    setValue('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';
  }, [value, isStreaming, disabled, onSend]);

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
    <div className="flex-shrink-0 px-5 pb-5 pt-2">
      <div className="flex items-end gap-2 bg-zinc-800/60 border border-zinc-700/60 rounded-2xl px-3.5 py-2.5 focus-within:border-zinc-600 transition-colors">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onInput={handleInput}
          placeholder={
            disabled
              ? 'Configure auth token in Settings…'
              : 'Message the agent… (Enter to send)'
          }
          disabled={disabled || isStreaming}
          rows={1}
          className="flex-1 bg-transparent text-sm text-zinc-100 placeholder-zinc-600 resize-none outline-none leading-relaxed disabled:opacity-40 min-h-[24px] max-h-[200px]"
        />
        <button
          onClick={isStreaming ? onCancel : handleSend}
          disabled={!isStreaming && !canSend}
          className={[
            'flex-shrink-0 w-7 h-7 rounded-lg flex items-center justify-center transition-all duration-100',
            isStreaming
              ? 'bg-red-600 hover:bg-red-500 text-white'
              : canSend
              ? 'bg-blue-600 hover:bg-blue-500 text-white'
              : 'bg-zinc-700/60 text-zinc-600 cursor-not-allowed',
          ].join(' ')}
          title={isStreaming ? 'Cancel' : 'Send'}
        >
          {isStreaming ? (
            <Square size={12} fill="currentColor" />
          ) : (
            <Send size={13} />
          )}
        </button>
      </div>
      <p className="text-[10px] text-zinc-700 mt-1.5 px-1">
        Enter to send · Shift+Enter for newline
      </p>
    </div>
  );
}
