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
      <div className="flex-shrink-0 flex items-center justify-between px-5 py-3 border-b border-zinc-800 bg-zinc-900/40">
        <div>
          <h1 className="text-sm font-semibold text-zinc-200">Chat</h1>
          <p className="text-[11px] mt-0.5">
            {isStreaming ? (
              <span className="text-blue-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse inline-block" />
                Agent is responding…
              </span>
            ) : (
              <span className="text-zinc-600">Ready</span>
            )}
          </p>
        </div>

        {messages.length > 0 && (
          <button
            onClick={clearMessages}
            className="flex items-center gap-1.5 text-xs text-zinc-600 hover:text-zinc-300 px-2 py-1.5 rounded-lg hover:bg-zinc-800 transition-colors"
          >
            <Trash2 size={13} />
            Clear
          </button>
        )}
      </div>

      {/* Auth warning */}
      {!hasToken && (
        <div className="flex-shrink-0 mx-5 mt-3 flex items-start gap-2.5 bg-amber-950/30 border border-amber-900/40 rounded-xl px-3.5 py-2.5 text-xs text-amber-500">
          <AlertCircle size={14} className="flex-shrink-0 mt-0.5" />
          <span>
            No auth token configured.{' '}
            <button
              onClick={() => setActiveSection('settings')}
              className="underline hover:text-amber-300 transition-colors"
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
