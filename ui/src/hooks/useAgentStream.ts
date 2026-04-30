import { useCallback, useRef } from 'react';
import { useStore } from '../store';
import type { AgentEvent, ModelParams } from '../types';

// Drop empty `extra`, return undefined when nothing is set so we don't
// send a no-op `model_params: {}` over the wire. The server's pydantic
// model accepts both, but omitting keeps the request body cleaner and
// makes Langfuse traces show "default params" instead of "{}".
function pruneModelParams(mp: ModelParams | undefined): ModelParams | undefined {
  if (!mp) return undefined;
  const out: ModelParams = {};
  if (mp.temperature !== undefined) out.temperature = mp.temperature;
  if (mp.top_p !== undefined) out.top_p = mp.top_p;
  if (mp.max_tokens !== undefined) out.max_tokens = mp.max_tokens;
  if (mp.extra && Object.keys(mp.extra).length > 0) out.extra = mp.extra;
  return Object.keys(out).length > 0 ? out : undefined;
}

// Parses the SSE stream from the agent API.
// We use fetch + ReadableStream instead of EventSource because EventSource
// only supports GET requests — this endpoint requires POST with a body.
export function useAgentStream() {
  const abortRef = useRef<AbortController | null>(null);
  const isStreaming = useStore((s) => s.messages.some((m) => m.isStreaming));

  const sendMessage = useCallback(async (prompt: string, enableThinking: boolean = false) => {
    // Access store actions via getState() so the callback has no stale-closure issues.
    const store = useStore.getState();
    const { authToken, apiBaseUrl, modelParams } = store.settings;

    if (!authToken.trim()) {
      const id = store.addAssistantMessage();
      store.finishMessage(id, 'No auth token configured. Go to Settings to add one.');
      return;
    }

    store.addUserMessage(prompt);
    const assistantId = store.addAssistantMessage();

    abortRef.current = new AbortController();
    const url = apiBaseUrl.trim() ? `${apiBaseUrl.trim()}/agent/chat` : '/agent/chat';

    // Build the request body. `model_params` is only included when the user
    // has set at least one override — otherwise the server applies its
    // deployment defaults (cleaner traces, smaller payload).
    const prunedParams = pruneModelParams(modelParams);
    const body: Record<string, unknown> = { prompt, enable_thinking: enableThinking };
    if (prunedParams) body.model_params = prunedParams;

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authToken}`,
        },
        body: JSON.stringify(body),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        const detail = await response.text().catch(() => response.statusText);
        useStore.getState().finishMessage(assistantId, `HTTP ${response.status}: ${detail}`);
        return;
      }

      if (!response.body) {
        useStore.getState().finishMessage(assistantId, 'No response body from server.');
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      // Track tool call IDs by tool name (the server uses name in tool_end, not an id).
      const toolIdByName = new Map<string, string>();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() ?? '';

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const raw = line.slice(6).trim();
          if (!raw) continue;

          let event: AgentEvent;
          try {
            event = JSON.parse(raw) as AgentEvent;
          } catch {
            continue;
          }

          const s = useStore.getState();

          switch (event.type) {
            case 'token':
              s.appendToken(assistantId, event.text);
              break;

            case 'tool_start': {
              const toolId = Math.random().toString(36).slice(2, 9);
              toolIdByName.set(event.name, toolId);
              s.addToolCall(assistantId, {
                id: toolId,
                name: event.name,
                args: event.args,
                status: 'running',
              });
              break;
            }

            case 'tool_end': {
              const toolId = toolIdByName.get(event.name);
              if (toolId) {
                s.updateToolCall(assistantId, toolId, event.output, 'done');
                toolIdByName.delete(event.name);
              }
              break;
            }

            case 'error':
              s.finishMessage(assistantId, event.message);
              break;

            case 'end':
              s.finishMessage(assistantId);
              break;
          }
        }
      }

      // Guard: mark done if server closed without sending 'end'.
      useStore.getState().finishMessage(assistantId);
    } catch (err) {
      const msg = (err as Error).name === 'AbortError' ? 'Cancelled.' : (err as Error).message;
      useStore.getState().finishMessage(assistantId, msg);
    } finally {
      abortRef.current = null;
    }
  }, []);

  const cancel = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  return { sendMessage, cancel, isStreaming };
}
