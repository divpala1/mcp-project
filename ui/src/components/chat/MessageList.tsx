import { useEffect, useRef } from 'react';
import { Bot } from 'lucide-react';
import type { Message } from '../../types';
import MessageBubble from './MessageBubble';

export default function MessageList({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center">
        {/* Stacked glow rings behind the icon */}
        <div className="relative mb-6 flex items-center justify-center">
          <div className="absolute w-28 h-28 rounded-full bg-violet-600/5 animate-pulse-slow" />
          <div className="absolute w-20 h-20 rounded-full bg-violet-600/8" />
          <div className="w-14 h-14 rounded-2xl bg-canvas-card border border-canvas-border shadow-elevated flex items-center justify-center relative z-10 shadow-glow-sm">
            <Bot size={22} className="text-violet-400 opacity-80" />
          </div>
        </div>

        <p className="text-sm font-semibold text-canvas-text mb-1.5 tracking-tight">
          Start a conversation
        </p>
        <p className="text-xs text-canvas-text-muted max-w-xs leading-relaxed">
          The agent will connect to your configured MCP servers and respond in real time.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 py-6 space-y-6">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
