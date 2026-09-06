<script setup lang="ts">
import { computed, onMounted } from 'vue'
import {
  Refresh,
  Right,
  User,
  Goods,
  DataLine,
  ShoppingCart,
  Connection as ConnectionIcon,
} from '@element-plus/icons-vue'
import PageHeading from '../components/PageHeading.vue'
import MetricCard from '../components/MetricCard.vue'
import DataState from '../components/DataState.vue'
import ChartPanel from '../components/ChartPanel.vue'
import { useResource } from '../composables/useResource'
import { api } from '../api'
import type { Overview, Ranking } from '../types'
import { number, percent, DEMO } from '../utils'
const { data, loading, error, load } = useResource<Overview>()
const ranks = useResource<Ranking>()
const reload = () => load(api.overview)
onMounted(() => {
  void reload()
  void ranks.load((signal) => api.ranking('products', 5, signal))
})
const distribution = computed(() => {
  const d = data.value
  return {
    color: ['#78e4d0', '#7c9dff', '#f6c780'],
    tooltip: { trigger: 'item' },
    series: [
      {
        type: 'pie',
        radius: ['62%', '82%'],
        center: ['50%', '50%'],
        avoidLabelOverlap: true,
        itemStyle: { borderColor: '#191f2b', borderWidth: 5, borderRadius: 7 },
        label: { show: false },
        data: [
          { name: '浏览', value: d?.total_views ?? 0 },
          { name: '加购', value: d?.total_carts ?? 0 },
          { name: '购买', value: d?.total_purchases ?? 0 },
        ],
      },
    ],
  }
})
const behavior = computed(() =>
  data.value
    ? [
        { label: '浏览', value: data.value.total_views, color: '#78e4d0', en: 'VIEW' },
        { label: '加购', value: data.value.total_carts, color: '#7c9dff', en: 'CART' },
        { label: '购买', value: data.value.total_purchases, color: '#f6c780', en: 'PURCHASE' },
      ]
    : [],
)
</script>
<template>
  <PageHeading
    title="数据总览"
    eyebrow="THE BIG PICTURE"
    description="看见每一次互动，理解每一步转化。"
    ><el-button :icon="Refresh" :loading="loading" @click="reload">刷新数据</el-button></PageHeading
  >
  <DataState :loading="loading" :error="error" @retry="reload">
    <template v-if="data">
      <div class="metrics-grid">
        <MetricCard
          label="行为事件总量"
          :value="number(data.total_events)"
          detail="浏览 · 加购 · 购买"
          :icon="DataLine"
        />
        <MetricCard
          label="独立用户"
          :value="number(data.total_users)"
          detail="已入库用户数量"
          :icon="User"
          accent="#9dafff"
        />
        <MetricCard
          label="商品总量"
          :value="number(data.total_products)"
          :detail="`${number(data.total_categories)} 个类别`"
          :icon="Goods"
          accent="#f6c780"
        />
        <MetricCard
          label="购买事件"
          :value="number(data.total_purchases)"
          detail="购买行为次数"
          :icon="ShoppingCart"
          accent="#df9fdf"
        />
      </div>
      <section class="dashboard-middle">
        <div class="panel behavior-panel">
          <div class="panel-heading">
            <div>
              <h2>行为分布</h2>
              <p>每一种互动，都是理解用户的线索</p>
            </div>
            <span class="subtle-label">EVENT MIX</span>
          </div>
          <div class="distribution-content">
            <div class="donut-wrap">
              <ChartPanel
                :option="distribution"
                label="浏览、加购与购买事件数量占比"
                :height="280"
              />
              <div class="donut-center">
                <span>行为事件</span><strong>{{ number(data.total_events) }}</strong
                ><small>TOTAL EVENTS</small>
              </div>
            </div>
            <div class="behavior-legend">
              <div v-for="item in behavior" :key="item.en" class="legend-row">
                <div class="legend-label">
                  <i :style="{ background: item.color }" /><span
                    >{{ item.label }}<small>{{ item.en }}</small></span
                  ><strong>{{
                    percent(data.total_events ? item.value / data.total_events : 0)
                  }}</strong>
                </div>
                <p>{{ number(item.value) }} <span>次事件</span></p>
              </div>
            </div>
          </div>
        </div>
        <div class="insight-panel">
          <span class="insight-kicker">EXPLORE THE CONNECTIONS</span>
          <div class="orbit-art" aria-hidden="true">
            <div />
            <div />
            <div />
            <span class="orbit-dot one" /><span class="orbit-dot two" /><ConnectionIcon />
          </div>
          <h2>从一次浏览，<br />到更多行为洞察。</h2>
          <p>以 Session 为线索，探索浏览、加购与购买之间的关联。</p>
          <RouterLink to="/analytics" class="insight-link">探索转化与排行 <Right /></RouterLink>
          <div class="insight-foot"><span />SESSION-BASED ANALYSIS</div>
        </div>
      </section>
      <section class="dashboard-bottom">
        <div class="panel">
          <div class="panel-heading">
            <div>
              <h2>热门商品 <span class="inline-tag">TOP 5</span></h2>
              <p>按行为事件数量排序</p>
            </div>
            <RouterLink to="/analytics" class="text-link">查看排行 <Right /></RouterLink>
          </div>
          <DataState
            :loading="ranks.loading.value"
            :error="ranks.error.value"
            :empty="ranks.data.value?.items.length === 0"
            @retry="ranks.load((signal) => api.ranking('products', 5, signal))"
          >
            <div
              class="mini-rank"
              v-for="(item, index) in ranks.data.value?.items"
              :key="item.product_id"
            >
              <span class="rank-no" :class="{ first: index === 0 }">{{
                String(index + 1).padStart(2, '0')
              }}</span>
              <div class="mini-rank-info">
                <RouterLink :to="`/products/${item.product_id}`"
                  >商品 {{ item.product_id }}</RouterLink
                >
                <div class="bar-track">
                  <i
                    :style="{
                      width: `${(item.event_count / (ranks.data.value?.items[0]?.event_count || 1)) * 100}%`,
                    }"
                  />
                </div>
              </div>
              <strong>{{ number(item.event_count) }}<small>次事件</small></strong>
            </div>
          </DataState>
        </div>
        <div class="panel quick-panel">
          <div class="panel-heading">
            <div>
              <h2>探索工作空间</h2>
              <p>从一个对象开始，连接完整行为</p>
            </div>
          </div>
          <RouterLink to="/products" class="quick-link"
            ><span class="quick-icon"><Goods /></span
            ><span
              ><strong>商品探索</strong
              ><small
                >{{ number(data.total_brands) }} 个品牌 ·
                {{ number(data.total_categories) }} 个类别</small
              ></span
            ><Right /></RouterLink
          ><RouterLink :to="`/users?user_id=${DEMO.user}`" class="quick-link"
            ><span class="quick-icon violet"><User /></span
            ><span><strong>用户行为</strong><small>按用户 ID 追踪互动记录</small></span
            ><Right /></RouterLink
          ><RouterLink :to="`/sessions/${DEMO.session}`" class="quick-link"
            ><span class="quick-icon amber"><DataLine /></span
            ><span><strong>Session 轨迹</strong><small>沿时间线查看行为详情</small></span
            ><Right
          /></RouterLink>
        </div>
      </section>
    </template>
  </DataState>
</template>
