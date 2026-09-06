import { createApp } from 'vue'
import {
  ElButton,
  ElInput,
  ElTable,
  ElTableColumn,
  ElPagination,
  ElRadioGroup,
  ElRadioButton,
  ElSelect,
  ElOption,
} from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import './style.css'
import App from './App.vue'
import { router } from './router'

async function bootstrap() {
  if (import.meta.env.VITE_USE_MOCK === 'true') {
    const { worker } = await import('./mocks/browser')
    await worker.start({
      serviceWorker: { url: `${import.meta.env.BASE_URL}mockServiceWorker.js` },
      onUnhandledRequest: 'bypass',
      quiet: true,
    })
  } else if ('serviceWorker' in navigator) {
    const registrations = await navigator.serviceWorker.getRegistrations()
    await Promise.all(
      registrations
        .filter((r) =>
          (r.active || r.waiting || r.installing)?.scriptURL.endsWith('/mockServiceWorker.js'),
        )
        .map((r) => r.unregister()),
    )
  }
  const app = createApp(App).use(router)
  for (const component of [
    ElButton,
    ElInput,
    ElTable,
    ElTableColumn,
    ElPagination,
    ElRadioGroup,
    ElRadioButton,
    ElSelect,
    ElOption,
  ])
    app.component(component.name!, component)
  app.mount('#app')
}
bootstrap().catch(() => {
  const app = document.getElementById('app')!
  app.innerHTML =
    '<main class="boot-error"><h1>页面暂时无法启动</h1><p>请确认通过本地开发服务或 HTTPS 打开页面，然后刷新重试。</p><button onclick="location.reload()">重新加载</button></main>'
})
