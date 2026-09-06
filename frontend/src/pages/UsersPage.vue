<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Right } from '@element-plus/icons-vue'
import PageHeading from '../components/PageHeading.vue'
import DataState from '../components/DataState.vue'
import EventBadge from '../components/EventBadge.vue'
import { useResource } from '../composables/useResource'
import { api } from '../api'
import type { UserEvents } from '../types'
import { number, money, utc, positiveInt, validId, DEMO } from '../utils'
const route = useRoute(),
  router = useRouter()
const userId = computed(() => (typeof route.query.user_id === 'string' ? route.query.user_id : ''))
const page = computed(() => positiveInt(route.query.page, 1))
const size = computed(() => positiveInt(route.query.page_size, 20, 100))
const type = computed(() =>
  ['view', 'cart', 'purchase'].includes(String(route.query.event_type))
    ? String(route.query.event_type)
    : '',
)
const input = ref(userId.value),
  inputError = ref('')
const { data, loading, error, load, clear } = useResource<UserEvents>()
const reload = () =>
  validId(userId.value)
    ? load((signal) => api.userEvents(userId.value, page.value, size.value, type.value, signal))
    : clear()
watch(
  [userId, page, size, type],
  () => {
    input.value = userId.value
    inputError.value = userId.value && !validId(userId.value) ? '请输入有效的数字用户 ID' : ''
    void reload()
  },
  { immediate: true },
)
function navigate(id = userId.value, nextPage = 1, nextSize = size.value, nextType = type.value) {
  void router.push({
    path: '/users',
    query: {
      user_id: id,
      page: nextPage,
      page_size: nextSize,
      ...(nextType ? { event_type: nextType } : {}),
    },
  })
}
function search() {
  inputError.value = validId(input.value.trim()) ? '' : '请输入有效的数字用户 ID'
  if (!inputError.value) {
    if (input.value.trim() === userId.value && page.value === 1) void reload()
    else navigate(input.value.trim())
  }
}
</script>
<template>
  <PageHeading
    title="用户行为"
    eyebrow="USER JOURNEY"
    description="沿着用户的足迹，串联每一次浏览、加购与购买。"
    ><span class="header-chip">BEHAVIOR EXPLORER</span></PageHeading
  >
  <section class="panel">
    <div class="query-toolbar">
      <form class="inline-form" @submit.prevent="search">
        <el-input
          v-model="input"
          aria-label="用户 ID"
          placeholder="输入用户 ID"
          :prefix-icon="Search"
          clearable
        /><el-button type="primary" native-type="submit">查询用户</el-button>
      </form>
      <el-button text @click="navigate(DEMO.user)">使用演示用户 <Right /></el-button>
    </div>
    <p v-if="inputError" class="input-error" role="alert">{{ inputError }}</p>
    <div v-if="validId(userId)" class="table-heading user-table-heading">
      <h2>
        行为流水 <span class="inline-tag mono">{{ userId }}</span>
      </h2>
      <el-radio-group
        :model-value="type"
        aria-label="行为类型"
        @change="navigate(userId, 1, size, String($event))"
        ><el-radio-button value="">全部</el-radio-button
        ><el-radio-button value="view">浏览</el-radio-button
        ><el-radio-button value="cart">加购</el-radio-button
        ><el-radio-button value="purchase">购买</el-radio-button></el-radio-group
      >
    </div>
    <DataState
      :loading="loading"
      :error="error"
      :empty="!validId(userId) || data?.items.length === 0"
      :emptyTitle="!validId(userId) ? '从一个用户开始探索' : '当前页没有行为记录'"
      :emptyDescription="
        !validId(userId)
          ? '输入用户 ID，或使用演示用户查看完整行为流水。'
          : '返回第一页，查看符合条件的行为。'
      "
      notFoundText="用户不存在或没有符合条件的行为"
      @retry="reload"
      ><template #empty-action
        ><el-button v-if="data?.items.length === 0" @click="navigate()"
          >返回第一页</el-button
        ></template
      >
      <el-table v-if="data" :data="data.items" row-key="event_id"
        ><el-table-column label="发生时间 · UTC" width="195"
          ><template #default="{ row }"
            ><span class="mono time-cell">{{ utc(row.event_time) }}</span></template
          ></el-table-column
        ><el-table-column label="行为" width="105"
          ><template #default="{ row }"
            ><EventBadge :type="row.event_type" /></template></el-table-column
        ><el-table-column label="商品 ID" min-width="125"
          ><template #default="{ row }"
            ><RouterLink :to="`/products/${row.product_id}`" class="table-link mono">{{
              row.product_id
            }}</RouterLink></template
          ></el-table-column
        ><el-table-column label="品牌 / 类别" min-width="245"
          ><template #default="{ row }"
            ><div class="two-line-cell">
              <span>{{ row.brand_name || '未提供品牌' }}</span
              ><small>{{ row.category_code || '未提供类别名称' }}</small>
            </div></template
          ></el-table-column
        ><el-table-column label="行为时价格" width="135" align="right"
          ><template #default="{ row }"
            ><span class="mono">{{ money(row.price) }}</span></template
          ></el-table-column
        ><el-table-column label="Session" min-width="180"
          ><template #default="{ row }"
            ><RouterLink
              v-if="row.session_id"
              :to="`/sessions/${row.session_id}`"
              class="text-link"
              :title="row.session_id"
              >{{ row.session_id.slice(0, 8) }}… <Right /></RouterLink
            ><span v-else class="muted">未关联</span></template
          ></el-table-column
        ></el-table
      >
    </DataState>
    <div v-if="data && data.total" class="pagination-row">
      <span>共 {{ number(data.total) }} 条 · 第 {{ page }} 页</span
      ><el-pagination
        :current-page="page"
        :page-size="size"
        :page-sizes="[10, 20, 50, 100]"
        :total="data.total"
        layout="sizes, prev, pager, next"
        @current-change="navigate(userId, $event)"
        @size-change="navigate(userId, 1, $event)"
      />
    </div>
  </section>
  <p class="page-note">行为按时间倒序展示。价格为事件发生时的价格，币种待确认。</p>
</template>
