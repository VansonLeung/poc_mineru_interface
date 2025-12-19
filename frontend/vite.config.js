import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Allow /web/* to serve the same SPA as / during dev/preview.
const webPathRewrite = {
  name: 'web-path-rewrite',
  configureServer(server) {
    server.middlewares.use((req, _res, next) => {
      if (req.url && req.url.startsWith('/web/')) {
        req.url = req.url.replace(/^\/web/, '') || '/';
      }
      next();
    });
  },
  configurePreviewServer(server) {
    server.middlewares.use((req, _res, next) => {
      if (req.url && req.url.startsWith('/web/')) {
        req.url = req.url.replace(/^\/web/, '') || '/';
      }
      next();
    });
  },
};

export default defineConfig({
  plugins: [react(), webPathRewrite],
  server: {
    port: 28108,
    host: '0.0.0.0',
    allowedHosts: true,
  },
});
