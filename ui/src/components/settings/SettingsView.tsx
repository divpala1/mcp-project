import { useState } from 'react';
import type { ReactNode } from 'react';
import { Eye, EyeOff, Save, CheckCircle, AlertCircle } from 'lucide-react';
import { useStore } from '../../store';
import type { ModelParams } from '../../types';

function Field({ label, hint, children, error }: { label: string; hint?: string; children: ReactNode; error?: string }) {
  return (
    <div>
      <label className="block text-xs font-medium text-canvas-text-subtle mb-1.5">{label}</label>
      {children}
      {error ? (
        <p className="text-[11px] text-red-400 mt-1.5 leading-relaxed flex items-start gap-1">
          <AlertCircle size={11} className="flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </p>
      ) : hint ? (
        <p className="text-[11px] text-canvas-text-dim mt-1.5 leading-relaxed">{hint}</p>
      ) : null}
    </div>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mb-6">
      <h2 className="text-[9px] font-bold text-canvas-text-dim uppercase tracking-widest mb-2.5">
        {title}
      </h2>
      <div className="bg-canvas-card border border-canvas-border rounded-xl p-4 space-y-4 shadow-card">
        {children}
      </div>
    </section>
  );
}

// String form-state → ModelParams object. Empty string means "leave unset"
// (the server falls back to its deployment default). Returns the params
// object plus per-field validation errors. We keep parsing centralized here
// so the Save handler stays simple.
function parseModelParams(form: ModelParamsForm): { params: ModelParams; errors: ModelParamsErrors } {
  const errors: ModelParamsErrors = {};
  const params: ModelParams = {};

  if (form.temperature.trim()) {
    const n = Number(form.temperature);
    if (!Number.isFinite(n) || n < 0 || n > 2) {
      errors.temperature = 'Must be a number between 0 and 2.';
    } else {
      params.temperature = n;
    }
  }

  if (form.top_p.trim()) {
    const n = Number(form.top_p);
    if (!Number.isFinite(n) || n <= 0 || n > 1) {
      errors.top_p = 'Must be a number between 0 (exclusive) and 1.';
    } else {
      params.top_p = n;
    }
  }

  if (form.max_tokens.trim()) {
    const n = Number(form.max_tokens);
    if (!Number.isInteger(n) || n < 1) {
      errors.max_tokens = 'Must be a positive integer.';
    } else {
      params.max_tokens = n;
    }
  }

  if (form.extra.trim()) {
    try {
      const parsed = JSON.parse(form.extra);
      if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
        errors.extra = 'Must be a JSON object.';
      } else {
        params.extra = parsed as Record<string, unknown>;
      }
    } catch (e) {
      errors.extra = `Invalid JSON: ${(e as Error).message}`;
    }
  }

  return { params, errors };
}

// Form state mirrors ModelParams but uses strings so empty/unset is
// distinguishable from 0 (which is a valid temperature).
interface ModelParamsForm {
  temperature: string;
  top_p: string;
  max_tokens: string;
  extra: string;
}

type ModelParamsErrors = Partial<Record<keyof ModelParamsForm, string>>;

function modelParamsToForm(mp: ModelParams): ModelParamsForm {
  return {
    temperature: mp.temperature !== undefined ? String(mp.temperature) : '',
    top_p: mp.top_p !== undefined ? String(mp.top_p) : '',
    max_tokens: mp.max_tokens !== undefined ? String(mp.max_tokens) : '',
    extra: mp.extra && Object.keys(mp.extra).length > 0 ? JSON.stringify(mp.extra, null, 2) : '',
  };
}

// Stable key order so we can compare two ModelParams objects via JSON string
// without false "changed" diffs caused by key ordering.
function canonicalizeParams(mp: ModelParams): string {
  const ordered: Record<string, unknown> = {};
  for (const k of ['temperature', 'top_p', 'max_tokens', 'extra'] as const) {
    if (mp[k] !== undefined) ordered[k] = mp[k];
  }
  return JSON.stringify(ordered);
}

export default function SettingsView() {
  const { settings, updateSettings } = useStore();
  const [authToken, setAuthToken] = useState(settings.authToken);
  const [apiBaseUrl, setApiBaseUrl] = useState(settings.apiBaseUrl);
  const [paramsForm, setParamsForm] = useState<ModelParamsForm>(() =>
    modelParamsToForm(settings.modelParams ?? {})
  );
  const [showToken, setShowToken] = useState(false);
  const [saved, setSaved] = useState(false);

  const { params: parsedParams, errors: paramErrors } = parseModelParams(paramsForm);
  const hasParamErrors = Object.keys(paramErrors).length > 0;

  const hasChanges =
    authToken !== settings.authToken ||
    apiBaseUrl !== settings.apiBaseUrl ||
    canonicalizeParams(parsedParams) !== canonicalizeParams(settings.modelParams ?? {});

  const handleSave = () => {
    if (hasParamErrors) return;
    updateSettings({ authToken, apiBaseUrl, modelParams: parsedParams });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const updateParamField = (key: keyof ModelParamsForm, value: string) => {
    setParamsForm((f) => ({ ...f, [key]: value }));
  };

  const inputClass =
    'flex-1 bg-transparent text-sm text-canvas-text placeholder-canvas-text-dim outline-none font-mono';

  const wrapperClass = (hasError = false) =>
    [
      'flex items-center gap-2 bg-canvas-overlay border rounded-lg px-3 py-2.5 transition-colors duration-150',
      hasError
        ? 'border-red-500/40 focus-within:border-red-500/60'
        : 'border-canvas-border focus-within:border-canvas-border-strong',
    ].join(' ');

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-xl mx-auto px-6 py-8">
        <div className="mb-7">
          <h1 className="text-base font-semibold text-canvas-text-bright tracking-tight mb-0.5">
            Settings
          </h1>
          <p className="text-xs text-canvas-text-dim">
            Authentication, connection, and per-request model parameters.
          </p>
        </div>

        <Card title="Authentication">
          <Field
            label="Bearer Token"
            hint="Sent as the Authorization header to the agent API and forwarded to MCP servers. Must match an entry in AUTH_TOKENS_JSON on the server."
          >
            <div className={wrapperClass()}>
              <input
                type={showToken ? 'text' : 'password'}
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                placeholder="tok_div"
                className={inputClass}
                autoComplete="off"
              />
              <button
                onClick={() => setShowToken((v) => !v)}
                className="text-canvas-text-dim hover:text-canvas-text-subtle transition-colors flex-shrink-0"
                title={showToken ? 'Hide token' : 'Show token'}
              >
                {showToken ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </Field>
        </Card>

        <Card title="Connection">
          <Field
            label="Agent API Base URL"
            hint="Leave empty to proxy through Vite (default: http://127.0.0.1:8002). Set this when the agent runs on a custom host or port."
          >
            <div className={wrapperClass()}>
              <input
                type="text"
                value={apiBaseUrl}
                onChange={(e) => setApiBaseUrl(e.target.value)}
                placeholder="http://127.0.0.1:8002  (leave empty for Vite proxy)"
                className={inputClass}
              />
            </div>
          </Field>
        </Card>

        <Card title="Model parameters">
          <p className="text-[11px] text-canvas-text-dim leading-relaxed -mt-1">
            Per-request overrides sent with every chat. Leave a field empty to
            use the server's deployment default (see agent/config.py).
          </p>

          <Field
            label="Temperature"
            hint="0 = deterministic, higher = more creative. Anthropic max is 1; OpenAI/Groq accept up to 2. Forced to 1 when extended thinking is on."
            error={paramErrors.temperature}
          >
            <div className={wrapperClass(!!paramErrors.temperature)}>
              <input
                type="number"
                inputMode="decimal"
                step="0.05"
                min="0"
                max="2"
                value={paramsForm.temperature}
                onChange={(e) => updateParamField('temperature', e.target.value)}
                placeholder="default"
                className={inputClass}
              />
            </div>
          </Field>

          <Field
            label="Top P"
            hint="Nucleus sampling threshold. Range 0–1. Most providers ignore this when temperature is 0."
            error={paramErrors.top_p}
          >
            <div className={wrapperClass(!!paramErrors.top_p)}>
              <input
                type="number"
                inputMode="decimal"
                step="0.05"
                min="0"
                max="1"
                value={paramsForm.top_p}
                onChange={(e) => updateParamField('top_p', e.target.value)}
                placeholder="default"
                className={inputClass}
              />
            </div>
          </Field>

          <Field
            label="Max tokens"
            hint="Cap on output tokens. Translated to num_predict for Ollama. Auto-raised when extended thinking is on."
            error={paramErrors.max_tokens}
          >
            <div className={wrapperClass(!!paramErrors.max_tokens)}>
              <input
                type="number"
                inputMode="numeric"
                step="1"
                min="1"
                value={paramsForm.max_tokens}
                onChange={(e) => updateParamField('max_tokens', e.target.value)}
                placeholder="provider default"
                className={inputClass}
              />
            </div>
          </Field>

          <Field
            label="Extra (advanced)"
            hint='JSON object passed verbatim to the provider client. Use for niche knobs, e.g. {"presence_penalty": 0.3, "top_k": 40}. Wins over the fields above if it sets the same key.'
            error={paramErrors.extra}
          >
            <div
              className={[
                'bg-canvas-overlay border rounded-lg px-3 py-2.5 transition-colors duration-150',
                paramErrors.extra
                  ? 'border-red-500/40 focus-within:border-red-500/60'
                  : 'border-canvas-border focus-within:border-canvas-border-strong',
              ].join(' ')}
            >
              <textarea
                value={paramsForm.extra}
                onChange={(e) => updateParamField('extra', e.target.value)}
                placeholder='{"presence_penalty": 0.2}'
                rows={3}
                className="w-full bg-transparent text-sm text-canvas-text placeholder-canvas-text-dim outline-none font-mono resize-y leading-relaxed"
                spellCheck={false}
              />
            </div>
          </Field>
        </Card>

        <div className="flex items-center gap-3 pt-1">
          <button
            onClick={handleSave}
            disabled={(!hasChanges && !saved) || hasParamErrors}
            className={[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150',
              saved
                ? 'bg-emerald-700/70 text-emerald-100 border border-emerald-600/30'
                : hasChanges && !hasParamErrors
                ? 'bg-violet-600 hover:bg-violet-500 text-white shadow-glow-sm'
                : 'bg-canvas-overlay text-canvas-text-dim cursor-not-allowed border border-canvas-border',
            ].join(' ')}
          >
            {saved ? (
              <>
                <CheckCircle size={14} />
                Saved
              </>
            ) : (
              <>
                <Save size={14} />
                Save changes
              </>
            )}
          </button>

          {hasChanges && !saved && !hasParamErrors && (
            <span className="text-xs text-canvas-text-dim">Unsaved changes</span>
          )}
          {hasParamErrors && (
            <span className="text-xs text-red-400">Fix the errors above to save.</span>
          )}
        </div>
      </div>
    </div>
  );
}
