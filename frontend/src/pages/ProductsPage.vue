<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Search, Right } from '@element-plus/icons-vue'
import PageHeading from '../components/PageHeading.vue'
import DataState from '../components/DataState.vue'
import { useResource } from '../composables/useResource'
import { api } from '../api'
import type { Page, Product } from '../types'
import { number, positiveInt, validId, DEMO } from '../utils'
const route = useRoute(),
  router = useRouter()
const page = computed(() => positiveInt(route.query.page, 1))
const size = computed(() => positiveInt(route.query.page_size, 20, 100))
const id = ref(''),
  inputError = ref('')
const { data, loading, error, load } = useResource<Page<Product>>()
const reload = () => load((signal) => api.products(page.value, size.value, signal))
watch([page, size], reload, { immediate: true })
function paginate(next: number, pageSize = size.value) {
  void router.push({ query: { page: next, page_size: pageSize } })
}
function search() {
  inputError.value = validId(id.value.trim()) ? '' : '请输入有效的数字商品 ID'
  if (!inputError.value) void router.push(`/products/${id.value.trim()}`)
}
</script>
<template>
  <PageHeading
    title="商品探索"
    eyebrow="PRODUCT EXPLORER"
    description="从商品出发，了解类别归属与每一次行为互动。"
    ><span class="header-chip">PRODUCT INTELLIGENCE</span></PageHeading
  >
  <section class="panel">
    <div class="query-toolbar">
      <form class="inline-form" @submit.prevent="search">
        <el-input
          v-model="id"
          aria-label="商品 ID"
          placeholder="输入商品 ID，直达详情"
          :prefix-icon="Search"
          clearable
        /><el-button type="primary" native-type="submit">查询商品</el-button>
      </form>
      <el-button text @click="router.push(`/products/${DEMO.product}`)"
        >查看演示商品 <Right
      /></el-button>
    </div>
    <p v-if="inputError" class="input-error" role="alert">{{ inputError }}</p>
    <div class="table-heading">
      <h2>商品目录</h2>
      <span v-if="data" class="subtle-label">共 {{ number(data.total) }} 件商品</span>
    </div>
    <DataState
      :loading="loading"
      :error="error"
      :empty="data?.items.length === 0"
      emptyDescription="当前页没有商品，可返回第一页继续浏览。"
      @retry="reload"
      ><template #empty-action><el-button @click="paginate(1)">返回第一页</el-button></template>
      <el-table v-if="data" :data="data.items" row-key="product_id"
        ><el-table-column label="商品 ID" min-width="180"
          ><template #default="{ row }"
            ><RouterLink
              :to="{
                path: `/products/${row.product_id}`,
                query: { from_page: page, from_size: size },
              }"
              class="table-link"
              ><span class="product-mark">P</span>{{ row.product_id }}</RouterLink
            ></template
          ></el-table-column
        ><el-table-column label="类别" min-width="290"
          ><template #default="{ row }"
            ><span class="category-code">{{
              row.category_code || '未提供类别名称'
            }}</span></template
          ></el-table-column
        ><el-table-column
          prop="category_id"
          label="类别 ID"
          min-width="230"
          class-name="mono" /><el-table-column label="操作" width="120" align="right"
          ><template #default="{ row }"
            ><RouterLink
              :to="{
                path: `/products/${row.product_id}`,
                query: { from_page: page, from_size: size },
              }"
              class="text-link"
              >查看详情 <Right /></RouterLink></template></el-table-column
      ></el-table>
    </DataState>
    <div v-if="data && data.total" class="pagination-row">
      <span>第 {{ page }} 页 · 每页 {{ size }} 条</span
      ><el-pagination
        :current-page="page"
        :page-size="size"
        :page-sizes="[10, 20, 50, 100]"
        :total="data.total"
        layout="sizes, prev, pager, next"
        @current-change="paginate"
        @size-change="paginate(1, $event)"
      />
    </div>
  </section>
  <p class="page-note">商品价格记录在行为发生时点；商品详情提供关联品牌与行为统计。</p>
</template>
