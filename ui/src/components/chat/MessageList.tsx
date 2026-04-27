import { useEffect, useRef } from 'react';
import type { Message } from '../../types';
import MessageBubble from './MessageBubble';

export default function MessageList({ messages }: { messages: Message[] }) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center gap-2">
        <div className="w-10 h-10 rounded-2xl bg-zinc-800 flex items-center justify-center text-zinc-600 text-lg font-mono mb-1">
          ⬡
        </div>
        <p className="text-sm font-medium text-zinc-500">Send a message to start</p>
        <p className="text-xs text-zinc-700 max-w-xs">
          The agent will connect to your configured MCP servers and respond in real time.
        </p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 py-5 space-y-5">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
