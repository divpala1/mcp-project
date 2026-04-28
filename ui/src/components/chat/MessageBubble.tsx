import { AlertCircle, Bot, User } from 'lucide-react';
import type { Message } from '../../types';
import ToolCallCard from './ToolCallCard';
import MarkdownContent from './MarkdownContent';

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const hasContent = message.content.length > 0;

  return (
    <div className={`flex gap-3 animate-fade-in ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Avatar — assistant */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-violet-600/12 border border-violet-600/20 flex items-center justify-center mt-0.5 shadow-glow-sm">
          <Bot size={14} className="text-violet-400" />
        </div>
      )}

      <div className={`flex flex-col gap-1.5 max-w-[78%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Content blocks (text and tool calls interleaved as they arrive) */}
        {message.content.map((block, i) => {
          if (block.type === 'tool_call') {
            return <ToolCallCard key={`${message.id}-tc-${i}`} toolCall={block.toolCall} />;
          }
          if (!block.text) return null;
          return (
            <div
              key={`${message.id}-text-${i}`}
              className={[
                'rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-card',
                isUser
                  ? 'bg-gradient-user text-white rounded-tr-sm'
                  : 'bg-canvas-card border border-canvas-border text-canvas-text rounded-tl-sm',
              ].join(' ')}
            >
              {isUser ? (
                <p className="whitespace-pre-wrap m-0">{block.text}</p>
              ) : (
                <MarkdownContent content={block.text} />
              )}
            </div>
          );
        })}

        {/* Typing indicator while streaming with no content yet */}
        {message.isStreaming && !hasContent && (
          <div className="bg-canvas-card border border-canvas-border rounded-2xl rounded-tl-sm px-4 py-3.5 flex items-center gap-1.5 shadow-card">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-violet-500/60 animate-bounce"
                style={{ animationDelay: `${i * 150}ms` }}
              />
            ))}
          </div>
        )}

        {/* Error state */}
        {message.error && (
          <div className="flex items-start gap-2 text-xs text-red-400 bg-red-950/15 border border-red-900/25 rounded-xl px-3.5 py-2.5 max-w-full">
            <AlertCircle size={13} className="flex-shrink-0 mt-0.5" />
            <span className="break-all">{message.error}</span>
          </div>
        )}

        {/* Timestamp */}
        <time className="text-[10px] text-canvas-text-dim px-1 font-mono">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </time>
      </div>

      {/* Avatar — user */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-canvas-overlay border border-canvas-border flex items-center justify-center mt-0.5">
          <User size={14} className="text-canvas-text-subtle" />
        </div>
      )}
    </div>
  );
}
