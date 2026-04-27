import Layout from './components/layout/Layout';
import ChatView from './components/chat/ChatView';
import SettingsView from './components/settings/SettingsView';
import { useStore } from './store';

export default function App() {
  const activeSection = useStore((s) => s.activeSection);

  return (
    <Layout>
      {activeSection === 'chat' && <ChatView />}
      {activeSection === 'settings' && <SettingsView />}
    </Layout>
  );
}
