<template>
  <div class="panel-card">
    <div class="panel-header">
      <span class="panel-title">技术指标雷达</span>
      <span class="signal-badge" :class="signalClass" v-if="data?.signal">{{ data.signal }}</span>
    </div>
    <div ref="chartRef" class="chart-container" v-if="data"></div>
    <div class="empty-state" v-else>
      <p>暂无技术指标数据</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Object, default: null },
})

const chartRef = ref(null)
let chartInstance = null
let resizeObserver = null

const signalClass = computed(() => {
  if (props.data?.signal === '买入') return 'buy'
  if (props.data?.signal === '卖出') return 'sell'
  return 'hold'
})

const initChart = () => {
  if (!chartRef.value || !props.data) return
  chartInstance = echarts.init(chartRef.value, 'dark')

  const option = {
    backgroundColor: 'transparent',
    radar: {
      center: ['50%', '55%'],
      radius: '65%',
      indicator: [
        { name: '趋势', max: 100 },
        { name: '动量', max: 100 },
        { name: '波动', max: 100 },
        { name: '量能', max: 100 },
      ],
      axisName: { color: 'rgba(224,230,237,0.6)', fontSize: 11 },
      splitArea: {
        areaStyle: { color: ['rgba(0,150,255,0.02)', 'rgba(0,150,255,0.04)'] },
      },
      splitLine: { lineStyle: { color: 'rgba(0,150,255,0.1)' } },
      axisLine: { lineStyle: { color: 'rgba(0,150,255,0.15)' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: [
              props.data.trend_score || 0,
              props.data.momentum_score || 0,
              props.data.volatility_score || 0,
              props.data.volume_score || 0,
            ],
            name: '技术评分',
            areaStyle: { color: 'rgba(0,212,255,0.2)' },
            lineStyle: { color: '#00d4ff', width: 2 },
            itemStyle: { color: '#00d4ff' },
          },
        ],
      },
    ],
  }

  chartInstance.setOption(option)
}

watch(
  () => props.data,
  () => {
    if (props.data) initChart()
  },
  { deep: true }
)

onMounted(() => {
  resizeObserver = new ResizeObserver(() => chartInstance?.resize())
  if (chartRef.value) resizeObserver.observe(chartRef.value)
  initChart()
})

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  chartInstance?.dispose()
})
</script>

<style scoped>
.panel-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 150, 255, 0.15);
  border-radius: 8px;
  padding: 16px;
  flex: 1;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #00d4ff;
}

.signal-badge {
  font-size: 12px;
  padding: 2px 10px;
  border-radius: 10px;
  font-weight: 600;
}

.signal-badge.buy {
  background: rgba(255, 77, 79, 0.2);
  color: #ff4d4f;
  border: 1px solid rgba(255, 77, 79, 0.3);
}

.signal-badge.sell {
  background: rgba(0, 230, 118, 0.2);
  color: #00e676;
  border: 1px solid rgba(0, 230, 118, 0.3);
}

.signal-badge.hold {
  background: rgba(245, 166, 35, 0.2);
  color: #f5a623;
  border: 1px solid rgba(245, 166, 35, 0.3);
}

.chart-container {
  height: 220px;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: rgba(224, 230, 237, 0.4);
}
</style>