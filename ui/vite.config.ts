import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Proxy /agent/* to the agent FastAPI server so the browser avoids CORS issues.
    // Change the target here if the agent runs on a different port.
    proxy: {
      '/agent': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
      },
    },
  },
});
