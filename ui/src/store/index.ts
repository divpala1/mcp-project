import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ContentBlock, Message, MessageRole, NavSection, Settings, ToolCall } from '../types';

function uid(): string {
  return Math.random().toString(36).slice(2, 11);
}

function makeMessage(role: MessageRole): Message {
  return { id: uid(), role, content: [], isStreaming: role === 'assistant', timestamp: new Date() };
}

interface Store {
  // --- Navigation ---
  activeSection: NavSection;
  setActiveSection: (section: NavSection) => void;

  // --- Chat ---
  messages: Message[];
  addUserMessage: (text: string) => string;
  addAssistantMessage: () => string;
  appendToken: (id: string, text: string) => void;
  addToolCall: (messageId: string, toolCall: ToolCall) => void;
  updateToolCall: (messageId: string, toolCallId: string, output: unknown, status: ToolCall['status']) => void;
  finishMessage: (id: string, error?: string) => void;
  clearMessages: () => void;

  // --- Settings (persisted to localStorage) ---
  settings: Settings;
  updateSettings: (patch: Partial<Settings>) => void;
}

export const useStore = create<Store>()(
  persist(
    (set) => ({
      activeSection: 'chat',
      setActiveSection: (activeSection) => set({ activeSection }),

      messages: [],

      addUserMessage: (text) => {
        const msg: Message = { ...makeMessage('user'), content: [{ type: 'text', text }], isStreaming: false };
        set((s) => ({ messages: [...s.messages, msg] }));
        return msg.id;
      },

      addAssistantMessage: () => {
        const msg = makeMessage('assistant');
        set((s) => ({ messages: [...s.messages, msg] }));
        return msg.id;
      },

      appendToken: (id, text) =>
        set((s) => ({
          messages: s.messages.map((m) => {
            if (m.id !== id) return m;
            const content = [...m.content];
            const last = content[content.length - 1];
            if (last?.type === 'text') {
              content[content.length - 1] = { type: 'text', text: last.text + text };
            } else {
              content.push({ type: 'text', text });
            }
            return { ...m, content };
          }),
        })),

      addToolCall: (messageId, toolCall) =>
        set((s) => ({
          messages: s.messages.map((m) =>
            m.id !== messageId
              ? m
              : { ...m, content: [...m.content, { type: 'tool_call' as const, toolCall }] }
          ),
        })),

      updateToolCall: (messageId, toolCallId, output, status) =>
        set((s) => ({
          messages: s.messages.map((m) => {
            if (m.id !== messageId) return m;
            return {
              ...m,
              content: m.content.map((block): ContentBlock => {
                if (block.type !== 'tool_call' || block.toolCall.id !== toolCallId) return block;
                return { ...block, toolCall: { ...block.toolCall, output, status } };
              }),
            };
          }),
        })),

      finishMessage: (id, error) =>
        set((s) => ({
          messages: s.messages.map((m) =>
            m.id === id ? { ...m, isStreaming: false, ...(error ? { error } : {}) } : m
          ),
        })),

      clearMessages: () => set({ messages: [] }),

      settings: { authToken: '', apiBaseUrl: '' },
      updateSettings: (patch) => set((s) => ({ settings: { ...s.settings, ...patch } })),
    }),
    {
      name: 'mcp-agent-ui',
      // Only persist settings — messages are ephemeral.
      partialize: (s) => ({ settings: s.settings }),
    }
  )
);
