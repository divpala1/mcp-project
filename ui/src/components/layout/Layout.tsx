import type { ReactNode } from 'react';
import Sidebar from './Sidebar';

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen overflow-hidden bg-canvas-base">
      <Sidebar />
      <main className="flex-1 overflow-hidden bg-canvas-surface">{children}</main>
    </div>
  );
}
