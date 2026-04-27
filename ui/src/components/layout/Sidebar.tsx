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
        'w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors duration-100',
        active
          ? 'bg-zinc-800 text-zinc-100'
          : disabled
          ? 'text-zinc-600 cursor-not-allowed'
          : 'text-zinc-400 hover:bg-zinc-800/60 hover:text-zinc-200',
      ].join(' ')}
    >
      <span className={`flex-shrink-0 ${active ? 'text-blue-400' : ''}`}>{icon}</span>
      <span className="flex-1 text-left leading-none">{label}</span>
      {soon && (
        <span className="text-[10px] font-medium text-zinc-700 bg-zinc-800 px-1.5 py-0.5 rounded">
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
    <aside className="w-52 flex-shrink-0 bg-zinc-900 border-r border-zinc-800 flex flex-col h-full select-none">
      {/* Brand */}
      <div className="px-4 py-4 border-b border-zinc-800 flex items-center gap-2.5">
        <div className="w-7 h-7 rounded-lg bg-blue-600 flex items-center justify-center flex-shrink-0">
          <Bot size={14} className="text-white" />
        </div>
        <div>
          <div className="text-sm font-semibold text-zinc-100 leading-none">MCP Agent</div>
          <div className="text-[10px] text-zinc-500 mt-0.5">Developer Console</div>
        </div>
      </div>

      {/* Primary nav */}
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        <NavItem
          icon={<MessageSquare size={15} />}
          label="Chat"
          active={activeSection === 'chat'}
          onClick={go('chat')}
        />

        <div className="my-2 mx-1 border-t border-zinc-800" />

        <p className="px-3 py-1 text-[10px] font-semibold text-zinc-600 uppercase tracking-wider">
          Tools
        </p>

        {/* Stub items — uncomment section prop & onClick when implemented */}
        <NavItem icon={<FileText size={15} />} label="Prompts" disabled soon />
        <NavItem icon={<Plug size={15} />} label="MCP Connectors" disabled soon />
      </nav>

      {/* Footer */}
      <div className="p-2 border-t border-zinc-800 space-y-0.5">
        <NavItem
          icon={<Settings size={15} />}
          label="Settings"
          active={activeSection === 'settings'}
          onClick={go('settings')}
        />
        <p className="px-3 pt-1 text-[10px] text-zinc-700">v0.1.0</p>
      </div>
    </aside>
  );
}
