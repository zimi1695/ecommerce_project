import { createRouter, createWebHashHistory } from 'vue-router'
export const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    { path: '/', redirect: '/dashboard' },
    {
      path: '/dashboard',
      component: () => import('./pages/DashboardPage.vue'),
      meta: { title: '数据总览', section: '概览' },
    },
    {
      path: '/products',
      component: () => import('./pages/ProductsPage.vue'),
      meta: { title: '商品探索', section: '行为洞察' },
    },
    {
      path: '/products/:productId',
      component: () => import('./pages/ProductDetailPage.vue'),
      meta: { title: '商品详情', section: '行为洞察' },
    },
    {
      path: '/users',
      component: () => import('./pages/UsersPage.vue'),
      meta: { title: '用户行为', section: '行为洞察' },
    },
    {
      path: '/sessions/:sessionId?',
      component: () => import('./pages/SessionPage.vue'),
      meta: { title: 'Session 轨迹', section: '行为洞察' },
    },
    {
      path: '/analytics',
      component: () => import('./pages/AnalyticsPage.vue'),
      meta: { title: '转化与排行', section: '分析' },
    },
    {
      path: '/:pathMatch(.*)*',
      component: () => import('./pages/NotFoundPage.vue'),
      meta: { title: '页面未找到', section: '导航' },
    },
  ],
  scrollBehavior: () => ({ top: 0 }),
})
router.afterEach((to) => {
  document.title = `${String(to.meta.title)} · 观数`
})
