import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    include: ['src/**/__tests__/**/*.test.ts'],
    globals: true,
    environment: 'node',
    // Disable browser-specific features that cause @vite/env issues
    pool: 'forks',
  },
});
