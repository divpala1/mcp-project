import { AlertCircle, Bot, User } from 'lucide-react';
import type { Message } from '../../types';
import ToolCallCard from './ToolCallCard';

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const hasContent = message.content.length > 0;

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {/* Avatar — assistant only */}
      {!isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-blue-600/15 border border-blue-600/25 flex items-center justify-center mt-0.5">
          <Bot size={13} className="text-blue-400" />
        </div>
      )}

      <div className={`flex flex-col gap-2 max-w-[76%] ${isUser ? 'items-end' : 'items-start'}`}>
        {/* Content blocks in order (text and tool calls interleaved as they arrived) */}
        {message.content.map((block, i) => {
          if (block.type === 'tool_call') {
            return <ToolCallCard key={`${message.id}-tc-${i}`} toolCall={block.toolCall} />;
          }
          if (!block.text) return null;
          return (
            <div
              key={`${message.id}-text-${i}`}
              className={[
                'rounded-2xl px-4 py-2.5 text-sm leading-relaxed',
                isUser
                  ? 'bg-blue-600 text-white rounded-tr-sm'
                  : 'bg-zinc-800/80 text-zinc-100 rounded-tl-sm',
              ].join(' ')}
            >
              <pre className="whitespace-pre-wrap font-sans m-0">{block.text}</pre>
            </div>
          );
        })}

        {/* Typing indicator while streaming with no content yet */}
        {message.isStreaming && !hasContent && (
          <div className="bg-zinc-800/80 rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
            {[0, 1, 2].map((i) => (
              <span
                key={i}
                className="w-1.5 h-1.5 rounded-full bg-zinc-500 animate-bounce"
                style={{ animationDelay: `${i * 120}ms` }}
              />
            ))}
          </div>
        )}

        {/* Error */}
        {message.error && (
          <div className="flex items-start gap-2 text-xs text-red-400 bg-red-950/25 border border-red-900/35 rounded-xl px-3 py-2.5 max-w-full">
            <AlertCircle size={13} className="flex-shrink-0 mt-0.5" />
            <span className="break-all">{message.error}</span>
          </div>
        )}

        {/* Timestamp */}
        <time className="text-[10px] text-zinc-700 px-1">
          {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </time>
      </div>

      {/* Avatar — user only */}
      {isUser && (
        <div className="flex-shrink-0 w-7 h-7 rounded-full bg-zinc-700 flex items-center justify-center mt-0.5">
          <User size={13} className="text-zinc-300" />
        </div>
      )}
    </div>
  );
}
