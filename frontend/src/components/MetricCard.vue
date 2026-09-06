<script setup lang="ts">
import type { Component } from 'vue'
defineProps<{
  label: string
  value: string
  detail?: string
  icon?: Component
  accent?: string
  index?: string
}>()
</script>
<template>
  <article class="metric-card" :style="{ '--metric-accent': accent || '#78e4d0' }">
    <div class="metric-label">
      <span>{{ label }}</span
      ><component :is="icon" v-if="icon" /><span v-else class="metric-index">{{ index }}</span>
    </div>
    <strong class="metric-value">{{ value }}</strong>
    <div class="metric-detail"><span class="metric-tick" />{{ detail }}</div>
    <div class="metric-decoration" />
  </article>
</template>
