import { AlertCircle, Trash2 } from 'lucide-react';
import { useStore } from '../../store';
import { useAgentStream } from '../../hooks/useAgentStream';
import MessageList from './MessageList';
import ChatInput from './ChatInput';

export default function ChatView() {
  const { sendMessage, cancel, isStreaming } = useAgentStream();
  const messages = useStore((s) => s.messages);
  const clearMessages = useStore((s) => s.clearMessages);
  const setActiveSection = useStore((s) => s.setActiveSection);
  const hasToken = Boolean(useStore((s) => s.settings.authToken.trim()));

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex-shrink-0 flex items-center justify-between px-5 py-3.5 border-b border-canvas-border bg-canvas-muted/60">
        <div className="flex items-center gap-2.5">
          {/* Status dot */}
          <span
            className={[
              'w-2 h-2 rounded-full flex-shrink-0',
              isStreaming
                ? 'bg-violet-400 animate-pulse shadow-glow-sm'
                : 'bg-canvas-border-strong',
            ].join(' ')}
          />
          <div>
            <h1 className="text-sm font-semibold text-canvas-text-bright leading-none">Chat</h1>
            <p
              className={[
                'text-[11px] mt-0.5 transition-colors duration-300',
                isStreaming ? 'text-violet-400' : 'text-canvas-text-dim',
              ].join(' ')}
            >
              {isStreaming ? 'Agent is responding…' : 'Ready'}
            </p>
          </div>
        </div>

        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="flex items-center gap-1.5 text-xs text-canvas-text-dim hover:text-canvas-text-subtle px-2.5 py-1.5 rounded-lg hover:bg-canvas-overlay transition-all duration-150"
          >
            <Trash2 size={12} />
            Clear
          </button>
        )}
      </div>

      {/* Auth warning */}
      {!hasToken && (
        <div className="flex-shrink-0 mx-5 mt-3 flex items-start gap-2.5 bg-amber-950/10 border border-amber-900/20 rounded-xl px-3.5 py-2.5 text-xs text-amber-500/80 animate-fade-in">
          <AlertCircle size={13} className="flex-shrink-0 mt-0.5 text-amber-500" />
          <span>
            No auth token configured.{' '}
            <button
              onClick={() => setActiveSection('settings')}
              className="underline underline-offset-2 hover:text-amber-400 transition-colors"
            >
              Open Settings
            </button>{' '}
            to add one.
          </span>
        </div>
      )}

      <MessageList messages={messages} />

      <ChatInput
        onSend={sendMessage}
        onCancel={cancel}
        isStreaming={isStreaming}
        disabled={!hasToken}
      />
    </div>
  );
}
