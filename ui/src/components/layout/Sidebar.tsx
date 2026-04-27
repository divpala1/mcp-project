import { Bot, MessageSquare, Settings, FileText, Plug } from 'lucide-react';
import type { ReactNode } from 'react';
import { useStore } from '../../store';
import type { NavSection } from '../../types';

interface NavItemProps {
  icon: ReactNode;
  label: string;
  active?: boolean;
  disabled?: boolean;
  soon?: boolean;
  onClick?: () => void;
}

function NavItem({ icon, label, active, disabled, soon, onClick }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={[
        'relative w-full flex items-center gap-2.5 px-2.5 py-2 rounded-lg text-sm font-medium transition-all duration-150',
        active
          ? 'bg-violet-600/12 text-canvas-text-bright'
          : disabled
          ? 'text-canvas-text-dim cursor-not-allowed opacity-50'
          : 'text-canvas-text-muted hover:bg-canvas-overlay hover:text-canvas-text',
      ].join(' ')}
    >
      {/* Active left-edge indicator */}
      {active && (
        <span className="absolute left-0 inset-y-1.5 w-[3px] bg-violet-500 rounded-r-full" />
      )}

      {/* Icon container */}
      <span
        className={[
          'flex-shrink-0 w-6 h-6 rounded-md flex items-center justify-center transition-all duration-150',
          active
            ? 'bg-violet-600/20 text-violet-400'
            : disabled
            ? 'text-canvas-text-dim'
            : 'text-canvas-text-muted group-hover:text-canvas-text-subtle',
        ].join(' ')}
      >
        {icon}
      </span>

      <span className="flex-1 text-left leading-none">{label}</span>

      {soon && (
        <span className="text-[9px] font-semibold text-canvas-text-dim bg-canvas-card border border-canvas-border px-1.5 py-0.5 rounded-md tracking-wide uppercase">
          soon
        </span>
      )}
    </button>
  );
}

export default function Sidebar() {
  const { activeSection, setActiveSection } = useStore();
  const go = (s: NavSection) => () => setActiveSection(s);

  return (
    <aside className="w-52 flex-shrink-0 bg-canvas-muted border-r border-canvas-border flex flex-col h-full select-none">
      {/* Brand */}
      <div className="px-3.5 py-4 border-b border-canvas-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-brand flex items-center justify-center flex-shrink-0 shadow-glow-sm">
            <Bot size={15} className="text-white" />
          </div>
          <div>
            <div className="text-sm font-semibold text-canvas-text-bright leading-none tracking-tight">
              MCP Agent
            </div>
            <div className="text-[10px] text-canvas-text-dim mt-0.5 font-mono">
              Developer Console
            </div>
          </div>
        </div>
      </div>

      {/* Primary nav */}
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        <NavItem
          icon={<MessageSquare size={13} />}
          label="Chat"
          active={activeSection === 'chat'}
          onClick={go('chat')}
        />

        <div className="my-3 mx-1 border-t border-canvas-border" />

        <p className="px-2.5 pb-1 text-[9px] font-bold text-canvas-text-dim uppercase tracking-widest">
          Tools
        </p>

        <NavItem icon={<FileText size={13} />} label="Prompts" disabled soon />
        <NavItem icon={<Plug size={13} />} label="MCP Connectors" disabled soon />
      </nav>

      {/* Footer */}
      <div className="p-2 border-t border-canvas-border space-y-0.5">
        <NavItem
          icon={<Settings size={13} />}
          label="Settings"
          active={activeSection === 'settings'}
          onClick={go('settings')}
        />
        <p className="px-2.5 pt-2 text-[10px] text-canvas-text-dim font-mono">v0.1.0</p>
      </div>
    </aside>
  );
}
