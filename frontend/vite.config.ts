import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const mock = env.VITE_USE_MOCK ?? String(mode === 'development' || mode === 'demo')
  return {
    plugins: [vue()],
    base: './',
    define: { 'import.meta.env.VITE_USE_MOCK': JSON.stringify(mock) },
    server: {
      proxy: {
        '/api': { target: env.API_PROXY_TARGET || 'http://127.0.0.1:8000', changeOrigin: true },
      },
    },
    build: {
      rolldownOptions: {
        output: {
          codeSplitting: {
            groups: [
              { name: 'renderer', test: /[\\/]zrender[\\/]/, priority: 30 },
              { name: 'vue', test: /[\\/](?:@vue|vue|vue-router)[\\/]/, priority: 20 },
              { name: 'ui', test: /[\\/]element-plus[\\/]/, priority: 10 },
              { name: 'charts', test: /[\\/]echarts[\\/]/ },
            ],
          },
        },
      },
    },
  }
})
