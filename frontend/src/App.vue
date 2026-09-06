<script setup lang="ts">
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import {
  DataAnalysis,
  Grid,
  Goods,
  User,
  Connection,
  TrendCharts,
  Fold,
  ArrowRight,
  Moon,
  Close,
} from '@element-plus/icons-vue'
import { isMock } from './api/client'
import { ElConfigProvider } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
const route = useRoute()
const mobileOpen = ref(false)
const media = window.matchMedia('(max-width: 980px)')
const narrow = ref(media.matches)
const onResize = () => {
  narrow.value = media.matches
  if (!media.matches) mobileOpen.value = false
}
const focusMain = () => document.getElementById('main-content')?.focus()
const onKey = (event: KeyboardEvent) => {
  if (event.key === 'Escape' && mobileOpen.value) {
    mobileOpen.value = false
    document.querySelector<HTMLButtonElement>('.menu-button')?.focus()
  }
}
onMounted(() => {
  media.addEventListener('change', onResize)
  window.addEventListener('keydown', onKey)
})
onBeforeUnmount(() => {
  media.removeEventListener('change', onResize)
  window.removeEventListener('keydown', onKey)
})
watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
  },
)
const navigation = [
  { path: '/dashboard', label: '数据总览', en: 'Overview', icon: Grid, group: '工作空间' },
  { path: '/products', label: '商品探索', en: 'Products', icon: Goods, group: '行为洞察' },
  { path: '/users', label: '用户行为', en: 'Users', icon: User },
  { path: '/sessions', label: 'Session 轨迹', en: 'Sessions', icon: Connection },
  {
    path: '/analytics',
    label: '转化与排行',
    en: 'Analytics',
    icon: TrendCharts,
    group: '数据分析',
  },
]
</script>

<template>
  <ElConfigProvider :locale="zhCn">
    <a href="#main-content" class="skip-link" @click.prevent="focusMain">跳到主要内容</a>
    <button v-if="mobileOpen" class="nav-scrim" aria-label="关闭导航" @click="mobileOpen = false" />
    <aside
      id="main-navigation"
      class="sidebar"
      :class="{ 'is-open': mobileOpen }"
      :inert="narrow && !mobileOpen"
    >
      <RouterLink to="/dashboard" class="brand"
        ><span class="brand-symbol"><DataAnalysis /></span
        ><span>观数<span class="brand-en">COMMERCE INSIGHTS</span></span></RouterLink
      >
      <button class="icon-button mobile-close" aria-label="关闭导航" @click="mobileOpen = false">
        <Close />
      </button>
      <div class="workspace">
        <span class="workspace-dot" /><span
          >电商用户行为分析<small>2019 NOV · 数据工作空间</small></span
        ><span class="workspace-tag">01</span>
      </div>
      <nav aria-label="主导航">
        <template v-for="item in navigation" :key="item.path">
          <p v-if="item.group" class="nav-group">{{ item.group }}</p>
          <RouterLink
            :to="item.path"
            class="nav-item"
            :class="{ active: route.path.startsWith(item.path) }"
            :aria-current="route.path.startsWith(item.path) ? 'page' : undefined"
          >
            <component :is="item.icon" /><span>{{ item.label }}</span
            ><span class="nav-indicator" />
          </RouterLink>
        </template>
      </nav>
      <div class="sidebar-bottom">
        <div class="source-icon"><Connection /></div>
        <strong>让每一次行为，都有迹可循。</strong>
        <p>从商品到用户，从浏览到购买。<br />探索数据背后的行为关联。</p>
        <span class="source-label">MULTI-CATEGORY E-COMMERCE</span>
      </div>
      <div class="sidebar-foot">
        <span class="mini-dot" />{{ isMock ? '独立演示模式' : '真实接口模式' }}<span>v1.0</span>
      </div>
    </aside>
    <div class="app-body">
      <header class="topbar">
        <div class="breadcrumb">
          <button
            class="icon-button menu-button"
            aria-label="展开导航"
            aria-controls="main-navigation"
            :aria-expanded="mobileOpen"
            @click="mobileOpen = !mobileOpen"
          >
            <Fold /></button
          ><span>工作空间</span><ArrowRight /><strong>{{ route.meta.title }}</strong>
        </div>
        <div class="topbar-status">
          <span class="data-badge" :class="{ live: !isMock }"
            ><span class="mini-dot" />{{ isMock ? '演示数据' : '真实接口' }}</span
          ><span class="topbar-divider" /><Moon class="theme-icon" /><span class="utc-badge"
            >UTC</span
          >
        </div>
      </header>
      <main id="main-content" tabindex="-1"><RouterView /></main>
      <footer class="page-footer">
        <span>观数 / 电商用户行为分析系统</span
        ><span
          >{{ isMock ? '模拟数据仅用于功能演示' : '数据来自已配置的后端服务' }}<i />时间统一为
          UTC</span
        >
      </footer>
    </div>
  </ElConfigProvider>
</template>
