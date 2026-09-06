<script setup lang="ts">
import { computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Refresh } from '@element-plus/icons-vue'
import PageHeading from '../components/PageHeading.vue'
import ChartPanel from '../components/ChartPanel.vue'
import DataState from '../components/DataState.vue'
import MetricCard from '../components/MetricCard.vue'
import { api } from '../api'
import { useResource } from '../composables/useResource'
import type { Ranking, RankingKind, Conversion, RankItem } from '../types'
import { number, money, percent } from '../utils'
const route = useRoute(),
  router = useRouter()
const kind = computed<RankingKind>(() =>
  ['products', 'brands', 'categories'].includes(String(route.query.kind))
    ? (route.query.kind as RankingKind)
    : 'products',
)
const limit = computed(() =>
  [5, 10, 20, 50].includes(Number(route.query.limit)) ? Number(route.query.limit) : 10,
)
const { data, loading, error, load } = useResource<Ranking>()
const conv = useResource<Conversion>()
const reloadRank = () => load((signal) => api.ranking(kind.value, limit.value, signal))
const reloadConversion = () => conv.load(api.conversion)
function reloadAll() {
  void reloadRank()
  void reloadConversion()
}
const switchRank = (k = kind.value, n = limit.value) =>
  router.push({ query: { kind: k, limit: n } })
watch([kind, limit], reloadRank, { immediate: true })
onMounted(reloadConversion)
const label = (item: RankItem) =>
  item.product_id
    ? `商品 ${item.product_id}`
    : item.brand_name || `${item.category_code || '未提供类别名称'} · ${item.category_id}`
const rankChart = computed(() => ({
  tooltip: { trigger: 'axis', confine: true },
  grid: { top: 8, left: 12, right: 55, bottom: 24, containLabel: true },
  xAxis: {
    type: 'value',
    splitLine: { lineStyle: { color: '#2a3241' } },
    axisLabel: { color: '#8490a5' },
  },
  yAxis: {
    type: 'category',
    inverse: true,
    data: data.value?.items.map(label) || [],
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: '#b8c3d6', width: 165, overflow: 'truncate' },
  },
  series: [
    {
      type: 'bar',
      barMaxWidth: 20,
      data:
        data.value?.items.map((item, index) => ({
          value: item.event_count,
          itemStyle: { color: index === 0 ? '#78e4d0' : '#5476ac', borderRadius: [0, 4, 4, 0] },
        })) || [],
      label: { show: true, position: 'right', color: '#b8c3d6' },
    },
  ],
}))
const conversionRows = computed(() =>
  conv.data.value
    ? [
        {
          label: '发生浏览的 Session',
          en: 'VIEW',
          count: conv.data.value.view_sessions,
          color: '#78e4d0',
        },
        {
          label: '发生加购的 Session',
          en: 'CART',
          count: conv.data.value.cart_sessions,
          color: '#7c9dff',
        },
        {
          label: '发生购买的 Session',
          en: 'PURCHASE',
          count: conv.data.value.purchase_sessions,
          color: '#f6c780',
        },
      ]
    : [],
)
</script>
<template>
  <PageHeading
    title="转化与排行"
    eyebrow="ANALYTICS STUDIO"
    description="比较商品热度，洞察同一 Session 内的行为关联。"
    ><el-button :icon="Refresh" @click="reloadAll">刷新分析</el-button></PageHeading
  >
  <section class="panel conversion-panel">
    <div class="panel-heading">
      <div>
        <h2>Session 行为关联</h2>
        <p>以 Session 为统计单位，观察行为共同出现的比例</p>
      </div>
      <span v-if="conv.data.value" class="header-chip"
        >{{ number(conv.data.value.total_sessions) }} 个 Session</span
      >
    </div>
    <DataState :loading="conv.loading.value" :error="conv.error.value" @retry="reloadConversion"
      ><template v-if="conv.data.value"
        ><div class="conversion-layout">
          <div class="session-bars">
            <div v-for="row in conversionRows" :key="row.en" class="session-bar">
              <div>
                <span
                  >{{ row.label }}<small>{{ row.en }}</small></span
                ><strong>{{ number(row.count) }}</strong>
              </div>
              <div class="bar-track">
                <i
                  :style="{
                    width: `${conv.data.value.total_sessions ? (row.count / conv.data.value.total_sessions) * 100 : 0}%`,
                    background: row.color,
                  }"
                />
              </div>
            </div>
          </div>
          <div class="conversion-rates">
            <MetricCard
              label="浏览 → 加购"
              :value="percent(conv.data.value.view_to_cart_rate)"
              :detail="`${number(conv.data.value.view_cart_sessions)} 个共同发生的 Session`"
              index="01"
            /><MetricCard
              label="加购 → 购买"
              :value="percent(conv.data.value.cart_to_purchase_rate)"
              :detail="`${number(conv.data.value.cart_purchase_sessions)} 个共同发生的 Session`"
              index="02"
              accent="#7c9dff"
            /><MetricCard
              label="浏览 → 购买"
              :value="percent(conv.data.value.view_to_purchase_rate)"
              :detail="`${number(conv.data.value.view_purchase_sessions)} 个共同发生的 Session`"
              index="03"
              accent="#f6c780"
            />
          </div></div></template
    ></DataState>
    <div class="method-note">
      <span>统计口径</span>
      <p>
        转化率 = 同时出现两类行为的 Session 数 ÷ 出现前一类行为的 Session 数。同一 Session
        内共同出现，<strong>不保证行为先后顺序</strong>，各类 Session 也不构成严格的逐级漏斗。
      </p>
    </div>
  </section>
  <section class="panel ranking-panel">
    <div class="panel-heading">
      <div>
        <h2>热度排行</h2>
        <p>按行为事件数量降序排列 · 销售金额为购买事件价格合计</p>
      </div>
      <el-select
        :model-value="limit"
        aria-label="排行数量"
        class="limit-select"
        @change="switchRank(kind, $event)"
        ><el-option v-for="n in [5, 10, 20, 50]" :key="n" :value="n" :label="`Top ${n}`"
      /></el-select>
    </div>
    <div class="rank-tabs">
      <el-radio-group
        :model-value="kind"
        aria-label="排行维度"
        @change="switchRank($event as RankingKind)"
        ><el-radio-button value="products">商品排行</el-radio-button
        ><el-radio-button value="brands">品牌排行</el-radio-button
        ><el-radio-button value="categories">类别排行</el-radio-button></el-radio-group
      ><span class="subtle-label">RANKED BY EVENT COUNT</span>
    </div>
    <DataState
      :loading="loading"
      :error="error"
      :empty="data?.items.length === 0"
      @retry="reloadRank"
      ><template v-if="data"
        ><div class="ranking-chart-scroll">
          <ChartPanel
            :option="rankChart"
            :height="Math.max(260, data.items.length * 36 + 30)"
            label="按事件数量降序排列的热度排行"
          />
        </div>
        <el-table
          :data="data.items"
          :row-key="(row: RankItem) => row.product_id || row.brand_id || row.category_id || ''"
          ><el-table-column type="index" label="排名" width="80"
            ><template #default="{ $index }"
              ><span class="rank-no" :class="{ first: $index === 0 }">{{
                String($index + 1).padStart(2, '0')
              }}</span></template
            ></el-table-column
          ><el-table-column label="分析对象" min-width="340"
            ><template #default="{ row }"
              ><RouterLink
                v-if="row.product_id"
                :to="`/products/${row.product_id}`"
                class="table-link"
                >商品 {{ row.product_id }}</RouterLink
              >
              <div v-else class="two-line-cell">
                <span>{{ row.brand_name || row.category_code || '未提供类别名称' }}</span
                ><small class="mono">{{ row.brand_id || row.category_id }}</small>
              </div></template
            ></el-table-column
          ><el-table-column label="行为事件" min-width="130" align="right"
            ><template #default="{ row }">{{ number(row.event_count) }}</template></el-table-column
          ><el-table-column label="购买次数" min-width="130" align="right"
            ><template #default="{ row }">{{
              number(row.purchase_count)
            }}</template></el-table-column
          ><el-table-column label="销售金额" min-width="160" align="right"
            ><template #default="{ row }">{{ money(row.sales_amount) }}</template></el-table-column
          ></el-table
        >
        <p class="page-note inside">
          金额币种待确认。品牌和类别以 ID 区分，类别名称可能为空或重复。
        </p></template
      ></DataState
    >
  </section>
</template>
