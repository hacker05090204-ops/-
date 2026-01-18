import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
// Phase-29: Added proxy configuration for backend API
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
        proxy: {
            // Phase-29: Proxy API calls to backend server
            '/api': {
                target: 'http://localhost:8029',
                changeOrigin: true,
            },
            // Phase-29: Proxy evidence file requests
            '/evidence': {
                target: 'http://localhost:8029',
                changeOrigin: true,
            },
        },
    },
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './tests/setup.ts',
    },
})
