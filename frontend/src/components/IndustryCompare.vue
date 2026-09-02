<template>
  <div class="industry-panel">
    <div class="empty-state" v-if="!localData.length && (!data || data.length === 0)">
      <p>暂无行业对比数据</p>
    </div>
    <div ref="chartRef" class="chart-box" v-show="localData.length > 0 || (data && data.length > 0)"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import * as echarts from 'echarts'
import { getIndustryCompare } from '@/api'

const props = defineProps({
  data: { type: Array, default: () => [] },
  tsCode: { type: String, default: '' },
})

const chartRef = ref(null)
const localData = ref([])
let chartInstance = null
let resizeObserver = null

const fetchData = async () => {
  try {
    const result = await getIndustryCompare()
    localData.value = result || []
  } catch (e) {
    console.error('获取行业对比数据失败:', e)
  }
}

const initChart = () => {
  const sourceData = localData.value.length > 0 ? localData.value : props.data
  if (!chartRef.value || !sourceData.length) return
  if (chartInstance) chartInstance.dispose()
  chartInstance = echarts.init(chartRef.value, 'dark')

  const industries = sourceData.map((d) => {
    const name = d.industry_l1 || d.industry || ''
    return name.length > 5 ? name.slice(0, 5) + '…' : name
  })
  const avgPct = sourceData.map((d) => d.avg_pct_chg || 0)
  const upCount = sourceData.map((d) => d.rise_count || d.up_count || 0)
  const downCount = sourceData.map((d) => d.fall_count || d.down_count || 0)

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1C2128',
      borderColor: '#252B36',
      borderRadius: 8,
      textStyle: { color: '#E6EDF3', fontSize: 11, fontFamily: 'JetBrains Mono, Consolas, monospace' },
      formatter: (params) => {
        const idx = params[0]?.dataIndex
        const fullName = sourceData[idx]?.industry_l1 || sourceData[idx]?.industry || ''
        let html = `<div style="margin-bottom:4px;color:#E6EDF3;font-weight:600">${fullName}</div>`
        params.forEach((p) => {
          html += `<div>${p.marker} ${p.seriesName}：<b>${p.value}</b>${p.seriesName === '平均涨幅' ? '%' : ''}</div>`
        })
        return html
      },
    },
    legend: {
      data: ['平均涨幅', '上涨家数', '下跌家数'],
      bottom: 0,
      textStyle: { color: '#8B95A5', fontSize: 10 },
      itemWidth: 10,
      itemHeight: 6,
      itemGap: 12,
    },
    grid: {
      top: 10,
      left: 50,
      right: 60,
      bottom: 40,
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: industries,
      axisLine: { lineStyle: { color: '#252B36' } },
      axisTick: { show: false },
      axisLabel: { fontSize: 10, color: '#8B95A5' },
    },
    yAxis: [
      {
        type: 'value',
        name: '%',
        nameTextStyle: { color: '#5B8DEF', fontSize: 10 },
        axisLabel: {
          fontSize: 10,
          color: '#5B8DEF',
          fontFamily: 'JetBrains Mono, Consolas, monospace',
          formatter: (val) => val.toFixed(1) + '%',
        },
        splitLine: { lineStyle: { color: '#252B36', type: 'solid' } },
      },
      {
        type: 'value',
        name: '家',
        nameTextStyle: { color: '#8B95A5', fontSize: 10 },
        axisLabel: {
          fontSize: 10,
          color: '#8B95A5',
          fontFamily: 'JetBrains Mono, Consolas, monospace',
        },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: '平均涨幅',
        type: 'bar',
        barWidth: 12,
        data: avgPct,
        itemStyle: { color: '#5B8DEF', borderRadius: [2, 2, 0, 0] },
      },
      {
        name: '上涨家数',
        type: 'bar',
        barWidth: 12,
        yAxisIndex: 1,
        data: upCount,
        itemStyle: { color: '#F23645', borderRadius: [2, 2, 0, 0], opacity: 0.8 },
      },
      {
        name: '下跌家数',
        type: 'bar',
        barWidth: 12,
        yAxisIndex: 1,
        data: downCount,
        itemStyle: { color: '#089981', borderRadius: [2, 2, 0, 0], opacity: 0.8 },
      },
    ],
  }

  chartInstance.setOption(option)
}

watch(
  () => localData.value,
  async () => {
    if (localData.value.length > 0) {
      await nextTick()
      initChart()
    }
  },
  { deep: true }
)

watch(
  () => props.data,
  async () => {
    if (props.data && props.data.length > 0) {
      await nextTick()
      initChart()
    }
  },
  { deep: true }
)

onMounted(async () => {
  resizeObserver = new ResizeObserver(() => chartInstance?.resize())
  if (chartRef.value) resizeObserver.observe(chartRef.value)
  await fetchData()
  await nextTick()
  initChart()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chartInstance?.dispose()
})
</script>

<style scoped>
.industry-panel {
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.chart-box {
  flex: 1;
  min-height: 0;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
  font-size: 13px;
}
</style>