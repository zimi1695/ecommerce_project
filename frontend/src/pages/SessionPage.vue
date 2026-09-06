<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Right, Clock, Connection } from '@element-plus/icons-vue'
import PageHeading from '../components/PageHeading.vue'
import DataState from '../components/DataState.vue'
import EventBadge from '../components/EventBadge.vue'
import { api } from '../api'
import { useResource } from '../composables/useResource'
import type { SessionDetail } from '../types'
import { DEMO, utc, money, number } from '../utils'
const route = useRoute(),
  router = useRouter()
const id = computed(() => String(route.params.sessionId || ''))
const input = ref(id.value),
  inputError = ref(''),
  eventPage = ref(1)
const { data, loading, error, load, clear } = useResource<SessionDetail>()
const reload = () => (id.value ? load((signal) => api.session(id.value, signal)) : clear())
watch(
  id,
  () => {
    input.value = id.value
    eventPage.value = 1
    inputError.value = ''
    void reload()
  },
  { immediate: true },
)
const visibleEvents = computed(
  () => data.value?.events.slice((eventPage.value - 1) * 50, eventPage.value * 50) || [],
)
const userCount = computed(() => new Set(data.value?.events.map((e) => e.user_id)).size)
function search() {
  inputError.value = input.value.trim() ? '' : '请输入 Session ID'
  if (!inputError.value) {
    if (input.value.trim() === id.value) void reload()
    else void router.push({ path: `/sessions/${encodeURIComponent(input.value.trim())}` })
  }
}
</script>
<template>
  <PageHeading
    title="Session 轨迹"
    eyebrow="SESSION TIMELINE"
    description="将离散的事件连接成时间线，还原每一段访问轨迹。"
    ><span class="header-chip">FOLLOW THE JOURNEY</span></PageHeading
  >
  <section class="panel session-search">
    <div class="query-toolbar">
      <form class="inline-form session-form" @submit.prevent="search">
        <el-input
          v-model="input"
          aria-label="Session ID"
          placeholder="输入完整 Session ID"
          :prefix-icon="Search"
          clearable
        /><el-button type="primary" native-type="submit">查询轨迹</el-button>
      </form>
      <el-button text @click="router.push(`/sessions/${DEMO.session}`)"
        >使用演示 Session <Right
      /></el-button>
    </div>
    <p v-if="inputError" class="input-error" role="alert">{{ inputError }}</p>
  </section>
  <DataState
    :loading="loading"
    :error="error"
    :empty="!id"
    emptyTitle="沿着 Session，发现行为关联"
    emptyDescription="输入完整 Session ID，或使用演示 Session 开始探索。"
    notFoundText="未找到该 Session"
    @retry="reload"
    ><template v-if="data">
      <section class="panel session-summary">
        <div class="session-title">
          <span class="quick-icon"><Connection /></span>
          <div>
            <p class="eyebrow">SESSION ID</p>
            <h2 class="mono">{{ data.session_id }}</h2>
          </div>
          <span class="header-chip">{{ number(data.event_count) }} 次事件</span>
        </div>
        <div class="session-meta">
          <div>
            <Clock /><span
              >开始时间<strong>{{ utc(data.start_time) }} <small>UTC</small></strong></span
            >
          </div>
          <div>
            <Clock /><span
              >结束时间<strong>{{ utc(data.end_time) }} <small>UTC</small></strong></span
            >
          </div>
          <div>
            <Connection /><span
              >关联用户<strong>{{ userCount }} <small>位用户</small></strong></span
            >
          </div>
        </div>
      </section>
      <section class="panel">
        <div class="panel-heading">
          <div>
            <h2>行为时间线</h2>
            <p>按时间正序展示 · 每条事件保留独立用户归属</p>
          </div>
          <span class="subtle-label">CHRONOLOGICAL VIEW</span>
        </div>
        <DataState :empty="data.events.length === 0" emptyTitle="该 Session 暂无行为明细">
          <ol class="timeline">
            <li v-for="event in visibleEvents" :key="event.event_id" :class="event.event_type">
              <div class="timeline-dot" />
              <div class="timeline-time">
                <time>{{ utc(event.event_time) }}</time
                ><small>UTC · #{{ event.event_id }}</small>
              </div>
              <div class="timeline-card">
                <div class="timeline-card-top">
                  <EventBadge :type="event.event_type" /><RouterLink
                    :to="`/products/${event.product_id}`"
                    class="table-link"
                    >商品 {{ event.product_id }} <Right /></RouterLink
                  ><strong class="mono">{{ money(event.price) }}</strong>
                </div>
                <div class="timeline-card-bottom">
                  <span
                    >{{ event.brand_name || '未提供品牌' }} ·
                    {{ event.category_code || '未提供类别名称' }}</span
                  ><RouterLink
                    :to="{ path: '/users', query: { user_id: event.user_id } }"
                    class="text-link"
                    >用户 {{ event.user_id }}</RouterLink
                  >
                </div>
              </div>
            </li>
          </ol>
          <div v-if="data.events.length > 50" class="pagination-row">
            <span>为便于浏览，每页展示 50 条事件</span
            ><el-pagination
              v-model:current-page="eventPage"
              :page-size="50"
              :total="data.events.length"
              layout="prev, pager, next"
            />
          </div>
        </DataState>
      </section> </template
  ></DataState>
</template>
