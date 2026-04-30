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

// Mirrors agent.llm.ModelParams on the server. All fields optional —
// missing values fall back to the deployment defaults from agent/config.py.
// `extra` is a free-form passthrough for provider-specific kwargs (e.g.
// `presence_penalty` for OpenAI, `top_k` for Anthropic).
export interface ModelParams {
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
  extra?: Record<string, unknown>;
}

export interface Settings {
  authToken: string;
  apiBaseUrl: string;
  // User-chosen per-request defaults applied to every chat send. Empty
  // object = "send no overrides", so the server applies its own defaults.
  modelParams: ModelParams;
}

// SSE event shapes emitted by the agent API (agent/api.py → agent/core.py).
export type AgentEvent =
  | { type: 'token'; text: string }
  | { type: 'tool_start'; name: string; args: Record<string, unknown> }
  | { type: 'tool_end'; name: string; output: unknown }
  | { type: 'error'; message: string }
  | { type: 'end' };
