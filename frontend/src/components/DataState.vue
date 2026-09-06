<script setup lang="ts">
import { Loading, Warning, Search } from '@element-plus/icons-vue'
import type { ApiError } from '../api/client'
defineProps<{
  loading?: boolean
  error?: ApiError | null
  empty?: boolean
  emptyTitle?: string
  emptyDescription?: string
  notFoundText?: string
}>()
defineEmits<{ retry: [] }>()
</script>
<template>
  <div v-if="loading" class="data-state" role="status" aria-live="polite">
    <Loading class="state-icon rotating" /><strong>正在读取数据</strong>
    <p>稍等片刻，洞察即将呈现</p>
  </div>
  <div v-else-if="error" class="data-state" role="alert">
    <component :is="error.status === 404 ? Search : Warning" class="state-icon" /><strong>{{
      error.status === 404 ? notFoundText || '未找到对应的数据' : '数据暂时无法加载'
    }}</strong>
    <p>
      {{
        error.status === 404
          ? '请检查查询条件，或使用演示对象重新查询。'
          : error.status === 500
            ? '数据服务暂时不可用，请稍后重试。'
            : error.message
      }}
    </p>
    <el-button @click="$emit('retry')">重新加载</el-button>
  </div>
  <div v-else-if="empty" class="data-state">
    <Search class="state-icon" /><strong>{{ emptyTitle || '暂无数据' }}</strong>
    <p>{{ emptyDescription || '试试其他查询条件。' }}</p>
    <slot name="empty-action" />
  </div>
  <slot v-else />
</template>
