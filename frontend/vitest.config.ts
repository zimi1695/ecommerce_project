import { defineConfig } from 'vitest/config'
export default defineConfig({
  define: { 'import.meta.env.VITE_API_BASE_URL': JSON.stringify('http://localhost/api') },
  test: { include: ['tests/unit/**/*.test.ts'], environment: 'node' },
})
