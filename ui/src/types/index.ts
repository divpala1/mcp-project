export type NavSection = 'chat' | 'settings';

export type MessageRole = 'user' | 'assistant';

export interface ToolCall {
  id: string;
  name: string;
  args: Record<string, unknown>;
  output?: unknown;
  status: 'running' | 'done' | 'error';
}

// Content blocks preserve the ordering of text and tool calls within a single
// assistant turn (LLM may interleave reasoning text with tool invocations).
export type ContentBlock =
  | { type: 'text'; text: string }
  | { type: 'tool_call'; toolCall: ToolCall };

export interface Message {
  id: string;
  role: MessageRole;
  content: ContentBlock[];
  isStreaming: boolean;
  timestamp: Date;
  error?: string;
}

export interface Settings {
  authToken: string;
  apiBaseUrl: string;
}

// SSE event shapes emitted by the agent API (agent/api.py → agent/core.py).
export type AgentEvent =
  | { type: 'token'; text: string }
  | { type: 'tool_start'; name: string; args: Record<string, unknown> }
  | { type: 'tool_end'; name: string; output: unknown }
  | { type: 'error'; message: string }
  | { type: 'end' };
