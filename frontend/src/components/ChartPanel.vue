<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref, watch } from 'vue'
import * as echarts from 'echarts/core'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, AriaComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import type { EChartsCoreOption } from 'echarts/core'
echarts.use([
  BarChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  AriaComponent,
  CanvasRenderer,
])
const props = withDefaults(
  defineProps<{ option: EChartsCoreOption; label: string; height?: number }>(),
  { height: 300 },
)
const container = ref<HTMLDivElement>()
let chart: echarts.ECharts | undefined
let observer: ResizeObserver | undefined
let frame = 0
const render = () =>
  chart?.setOption(
    {
      backgroundColor: 'transparent',
      textStyle: { fontFamily: 'system-ui, sans-serif' },
      aria: { enabled: true },
      animation: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      animationDuration: 400,
      ...props.option,
    },
    { notMerge: true },
  )
onMounted(() => {
  chart = echarts.init(container.value!)
  render()
  observer = new ResizeObserver(() => {
    cancelAnimationFrame(frame)
    frame = requestAnimationFrame(() => {
      if (
        chart &&
        container.value &&
        (chart.getWidth() !== container.value.clientWidth ||
          chart.getHeight() !== container.value.clientHeight)
      )
        chart.resize()
    })
  })
  observer.observe(container.value!)
})
watch(() => props.option, render, { deep: true })
onBeforeUnmount(() => {
  observer?.disconnect()
  cancelAnimationFrame(frame)
  chart?.dispose()
})
</script>
<template>
  <div
    ref="container"
    class="chart-container"
    :style="{ height: `${height}px` }"
    role="img"
    :aria-label="label"
  />
</template>
