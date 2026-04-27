import { useState } from 'react';
import type { ReactNode } from 'react';
import { Eye, EyeOff, Save, CheckCircle } from 'lucide-react';
import { useStore } from '../../store';

function Field({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <label className="block text-xs font-medium text-zinc-400 mb-1.5">{label}</label>
      {children}
      {hint && <p className="text-[11px] text-zinc-600 mt-1.5 leading-relaxed">{hint}</p>}
    </div>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="mb-7">
      <h2 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2.5">
        {title}
      </h2>
      <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-4 space-y-4">
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

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-xl mx-auto px-6 py-8">
        <h1 className="text-base font-semibold text-zinc-200 mb-0.5">Settings</h1>
        <p className="text-xs text-zinc-600 mb-7">Authentication and connection configuration.</p>

        <Card title="Authentication">
          <Field
            label="Bearer Token"
            hint={
              `Sent as the Authorization header to the agent API and forwarded verbatim to ` +
              `MCP servers. Must match an entry in AUTH_TOKENS_JSON on the server.`
            }
          >
            <div className="flex items-center gap-2 bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 focus-within:border-zinc-600 transition-colors">
              <input
                type={showToken ? 'text' : 'password'}
                value={authToken}
                onChange={(e) => setAuthToken(e.target.value)}
                placeholder="tok_alice"
                className="flex-1 bg-transparent text-sm text-zinc-100 placeholder-zinc-600 outline-none font-mono"
                autoComplete="off"
              />
              <button
                onClick={() => setShowToken(!showToken)}
                className="text-zinc-600 hover:text-zinc-300 transition-colors"
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
            <input
              type="text"
              value={apiBaseUrl}
              onChange={(e) => setApiBaseUrl(e.target.value)}
              placeholder="http://127.0.0.1:8002  (leave empty for Vite proxy)"
              className="w-full bg-zinc-800 border border-zinc-700 rounded-lg px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-zinc-600 transition-colors font-mono"
            />
          </Field>
        </Card>

        {/* Future sections go here — e.g., LLM provider override, theme, etc. */}

        <div className="flex items-center gap-3">
          <button
            onClick={handleSave}
            disabled={!hasChanges && !saved}
            className={[
              'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-150',
              saved
                ? 'bg-emerald-700/80 text-white'
                : hasChanges
                ? 'bg-blue-600 hover:bg-blue-500 text-white'
                : 'bg-zinc-800 text-zinc-600 cursor-not-allowed',
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
            <span className="text-xs text-zinc-600">Unsaved changes.</span>
          )}
        </div>
      </div>
    </div>
  );
}
