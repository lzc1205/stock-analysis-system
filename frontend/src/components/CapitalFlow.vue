<template>
  <div class="capital-panel">
    <div class="empty-state" v-if="!data || data.length === 0">
      <p>暂无资金流向数据</p>
    </div>
    <div ref="chartRef" class="chart-box" v-show="data && data.length > 0"></div>
    <div class="flow-summary" v-if="latestFlow">
      <span>主力净流入 <span :class="latestFlow.net_mf >= 0 ? 'up' : 'down'">{{ formatNum(latestFlow.net_mf) }}万</span></span>
      <span>超大单 <span :class="latestFlow.net_elg >= 0 ? 'up' : 'down'">{{ formatNum(latestFlow.net_elg) }}万</span></span>
      <span>大单 <span :class="latestFlow.net_lg >= 0 ? 'up' : 'down'">{{ formatNum(latestFlow.net_lg) }}万</span></span>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  tsCode: { type: String, default: '' },
})

const chartRef = ref(null)
let chartInstance = null
let resizeObserver = null

const latestFlow = computed(() => {
  if (!props.data.length) return null
  const latest = props.data[props.data.length - 1]
  return {
    net_mf: latest.net_total || 0,
    net_elg: latest.net_elg || 0,
    net_lg: latest.net_lg || 0,
  }
})

const formatNum = (val) => {
  if (val == null) return '--'
  return (val / 10000).toFixed(0)
}

const initChart = () => {
  if (!chartRef.value || !props.data.length) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value, 'dark')

  const dates = props.data.map((d) => d.trade_date?.slice(5) || '')
  const netSm = props.data.map((d) => d.net_sm || 0)
  const netMd = props.data.map((d) => d.net_md || 0)
  const netLg = props.data.map((d) => d.net_lg || 0)
  const netElg = props.data.map((d) => d.net_elg || 0)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1C2128',
      borderColor: '#252B36',
      borderRadius: 8,
      textStyle: { color: '#E6EDF3', fontSize: 11, fontFamily: 'JetBrains Mono, Consolas, monospace' },
    },
    legend: {
      data: ['小单', '中单', '大单', '超大单'],
      top: 0,
      textStyle: { color: '#8B95A5', fontSize: 10 },
      itemWidth: 10,
      itemHeight: 6,
      itemGap: 12,
    },
    grid: {
      left: '2%',
      right: '2%',
      top: '14%',
      bottom: '5%',
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#252B36' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#8B95A5', fontFamily: 'JetBrains Mono, Consolas, monospace' },
    },
    yAxis: {
      type: 'value',
      name: '万',
      nameTextStyle: { color: '#8B95A5', fontSize: 10 },
      axisLabel: {
        fontSize: 10,
        color: '#8B95A5',
        fontFamily: 'JetBrains Mono, Consolas, monospace',
        formatter: (val) => (val / 10000).toFixed(0) + '万',
      },
      splitLine: { lineStyle: { color: '#252B36', type: 'solid' } },
    },
    series: [
      { name: '小单', type: 'bar', stack: 'total', data: netSm, itemStyle: { color: '#5B8DEF' } },
      { name: '中单', type: 'bar', stack: 'total', data: netMd, itemStyle: { color: '#089981' } },
      { name: '大单', type: 'bar', stack: 'total', data: netLg, itemStyle: { color: '#E6C07B' } },
      { name: '超大单', type: 'bar', stack: 'total', data: netElg, itemStyle: { color: '#F23645' } },
    ],
  }

  chartInstance.setOption(option)
}

watch(
  () => props.data,
  async () => {
    if (props.data && props.data.length > 0) {
      await nextTick()
      initChart()
    }
  },
  { deep: true },
)

onMounted(async () => {
  await nextTick()
  initChart()
  resizeObserver = new ResizeObserver(() => chartInstance?.resize())
  if (chartRef.value) resizeObserver.observe(chartRef.value)
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chartInstance?.dispose()
})
</script>

<style scoped>
.capital-panel {
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chart-box {
  flex: 1;
  min-height: 0;
}

.flow-summary {
  display: flex;
  gap: 16px;
  padding: 8px 0 4px;
  font-size: 11px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
}

.flow-summary span {
  font-family: var(--font-mono);
}

.flow-summary .up { color: var(--up-color); }
.flow-summary .down { color: var(--down-color); }

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
  font-size: 13px;
}
</style>