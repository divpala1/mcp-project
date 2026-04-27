import { useState } from 'react';
import type { ReactNode } from 'react';
import { Eye, EyeOff, Save, CheckCircle } from 'lucide-react';
import { useStore } from '../../store';

function Field({ label, hint, children }: { label: string; hint?: string; children: ReactNode }) {
  return (
    <div>
      <label className="block text-xs font-medium text-canvas-text-subtle mb-1.5">{label}</label>
      {children}
      {hint && (
        <p className="text-[11px] text-canvas-text-dim mt-1.5 leading-relaxed">{hint}</p>
      )}
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

export default function SettingsView() {
  const { settings, updateSettings } = useStore();
  const [authToken, setAuthToken] = useState(settings.authToken);
  const [apiBaseUrl, setApiBaseUrl] = useState(settings.apiBaseUrl);
  const [showToken, setShowToken] = useState(false);
  const [saved, setSaved] = useState(false);

  const hasChanges = authToken !== settings.authToken || apiBaseUrl !== settings.apiBaseUrl;

  const handleSave = () => {
    updateSettings({ authToken, apiBaseUrl });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const inputClass =
    'flex-1 bg-transparent text-sm text-canvas-text placeholder-canvas-text-dim outline-none font-mono';

  const wrapperClass = [
    'flex items-center gap-2 bg-canvas-overlay border rounded-lg px-3 py-2.5 transition-colors duration-150',
    'border-canvas-border focus-within:border-canvas-border-strong',
  ].join(' ');

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-xl mx-auto px-6 py-8">
        <div className="mb-7">
          <h1 className="text-base font-semibold text-canvas-text-bright tracking-tight mb-0.5">
            Settings
          </h1>
          <p className="text-xs text-canvas-text-dim">
            Authentication and connection configuration.
          </p>
        </div>

        <Card title="Authentication">
          <Field
            label="Bearer Token"
            hint="Sent as the Authorization header to the agent API and forwarded to MCP servers. Must match an entry in AUTH_TOKENS_JSON on the server."
          >
            <div className={wrapperClass}>
              <input
                type={showToken ? 'text' : 'password'}
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                placeholder="tok_alice"
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
            <div className={wrapperClass}>
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

        <div className="flex items-center gap-3 pt-1">
          <button
            onClick={handleSave}
            disabled={!hasChanges && !saved}
            className={[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150',
              saved
                ? 'bg-emerald-700/70 text-emerald-100 border border-emerald-600/30'
                : hasChanges
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

          {hasChanges && !saved && (
            <span className="text-xs text-canvas-text-dim">Unsaved changes</span>
          )}
        </div>
      </div>
    </div>
  );
}
