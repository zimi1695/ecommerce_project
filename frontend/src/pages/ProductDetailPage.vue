<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Back } from '@element-plus/icons-vue'
import PageHeading from '../components/PageHeading.vue'
import DataState from '../components/DataState.vue'
import MetricCard from '../components/MetricCard.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { api } from '../api'
import { useResource } from '../composables/useResource'
import type { ProductDetail, ProductStatistics } from '../types'
import { number, money, positiveInt } from '../utils'
const route = useRoute()
const id = computed(() => String(route.params.productId))
const { data, loading, error, load } = useResource<ProductDetail>()
const stats = useResource<ProductStatistics>()
const reload = () => load((signal) => api.product(id.value, signal))
const loadStats = () => stats.load((signal) => api.statistics(id.value, signal))
watch(
  id,
  () => {
    void reload()
    void loadStats()
  },
  { immediate: true },
)
const chart = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 55, right: 24, bottom: 30, top: 20 },
  xAxis: {
    type: 'category',
    data: ['浏览', '加购', '购买'],
    axisLabel: { color: '#a9b3c7' },
    axisLine: { lineStyle: { color: '#333b4c' } },
  },
  yAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#2a3241' } },
    axisLabel: { color: '#8490a5' },
  },
  series: [
    {
      type: 'bar',
      barWidth: 50,
      itemStyle: { borderRadius: [5, 5, 0, 0] },
      data: [
        { value: stats.data.value?.view_count ?? 0, itemStyle: { color: '#78e4d0' } },
        { value: stats.data.value?.cart_count ?? 0, itemStyle: { color: '#7c9dff' } },
        { value: stats.data.value?.purchase_count ?? 0, itemStyle: { color: '#f6c780' } },
      ],
    },
  ],
}))
</script>
<template>
  <PageHeading
    title="商品详情"
    eyebrow="PRODUCT PROFILE"
    description="连接商品信息与行为表现，发现互动背后的价值。"
    ><RouterLink
      :to="{
        path: '/products',
        query: {
          page: positiveInt(route.query.from_page, 1),
          page_size: positiveInt(route.query.from_size, 20, 100),
        },
      }"
      class="button-link"
      ><Back />返回商品目录</RouterLink
    ></PageHeading
  >
  <DataState :loading="loading" :error="error" notFoundText="未找到该商品" @retry="reload"
    ><template v-if="data">
      <section class="panel product-profile">
        <span class="product-avatar">P</span>
        <div class="profile-primary">
          <p class="eyebrow">PRODUCT ID</p>
          <h2 class="mono">{{ data.product_id }}</h2>
          <p>{{ data.category_code || '未提供类别名称' }}</p>
        </div>
        <div class="profile-field">
          <span>类别 ID</span
          ><strong class="mono" data-testid="category-id">{{ data.category_id }}</strong>
        </div>
        <div class="profile-field">
          <span>关联品牌</span>
          <div class="brand-tags">
            <span v-for="brand in data.brands" :key="brand.brand_id" class="brand-tag">{{
              brand.brand_name
            }}</span
            ><span v-if="!data.brands.length">未提供品牌</span>
          </div>
        </div>
      </section>
      <DataState :loading="stats.loading.value" :error="stats.error.value" @retry="loadStats"
        ><template v-if="stats.data.value"
          ><div class="metrics-grid">
            <MetricCard
              label="浏览次数"
              :value="number(stats.data.value.view_count)"
              detail="VIEW EVENTS"
              index="01"
            /><MetricCard
              label="加购次数"
              :value="number(stats.data.value.cart_count)"
              detail="CART EVENTS"
              index="02"
              accent="#7c9dff"
            /><MetricCard
              label="购买次数"
              :value="number(stats.data.value.purchase_count)"
              detail="PURCHASE EVENTS"
              index="03"
              accent="#f6c780"
            /><MetricCard
              label="销售金额"
              :value="money(stats.data.value.sales_amount)"
              detail="购买事件价格合计 · 币种待确认"
              index="04"
              accent="#df9fdf"
            />
          </div>
          <section class="panel">
            <div class="panel-heading">
              <div>
                <h2>商品行为概览</h2>
                <p>共 {{ number(stats.data.value.event_count) }} 次行为事件</p>
              </div>
              <span class="subtle-label">EVENT BREAKDOWN</span>
            </div>
            <ChartPanel
              :option="chart"
              label="当前商品的浏览、加购与购买次数"
            /></section></template
      ></DataState> </template
  ></DataState>
</template>
