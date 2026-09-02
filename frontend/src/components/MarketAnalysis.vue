<template>
  <div class="market-analysis">
    <div v-if="loading" class="loading-state">加载中...</div>
    <div v-else-if="!data" class="empty-state">暂无数据</div>
    <template v-else>
      <!-- 概览卡片 -->
      <div class="overview-cards">
        <div class="card">
          <div class="card-label">市场股票</div>
          <div class="card-value">{{ data.total_stocks }}</div>
        </div>
        <div class="card">
          <div class="card-label">上涨家数</div>
          <div class="card-value up">{{ data.up_count }}</div>
          <div class="card-sub">{{ data.up_ratio }}%</div>
        </div>
        <div class="card">
          <div class="card-label">下跌家数</div>
          <div class="card-value down">{{ data.down_count }}</div>
          <div class="card-sub">{{ (100 - data.up_ratio - (data.flat_count / data.total_stocks * 100)).toFixed(1) }}%</div>
        </div>
        <div class="card">
          <div class="card-label">平均涨跌</div>
          <div class="card-value" :class="data.avg_pct >= 0 ? 'up' : 'down'">{{ data.avg_pct >= 0 ? '+' : '' }}{{ data.avg_pct }}%</div>
        </div>
      </div>

      <!-- 涨跌幅分布 -->
      <div class="section">
        <div class="section-title">涨跌幅分布</div>
        <div ref="distChartRef" class="chart-box"></div>
      </div>

      <!-- 行业涨幅榜 -->
      <div class="section">
        <div class="section-title">行业涨幅榜</div>
        <div class="industry-list">
          <div
            v-for="(item, idx) in data.industry_rank"
            :key="item.name"
            class="industry-row"
          >
            <span class="rank">{{ idx + 1 }}</span>
            <span class="ind-name">{{ item.name }}</span>
            <span class="bar-wrap">
              <span class="bar" :style="{
                width: Math.max(Math.abs(item.avg_pct) * 6, 2) + '%',
                background: item.avg_pct >= 0
                  ? 'linear-gradient(90deg, rgba(242,54,69,0.65), rgba(242,54,69,0.18))'
                  : 'linear-gradient(90deg, rgba(8,153,129,0.65), rgba(8,153,129,0.18))'
              }"></span>
            </span>
            <span class="pct" :class="item.avg_pct >= 0 ? 'up' : 'down'">{{ item.avg_pct >= 0 ? '+' : '' }}{{ item.avg_pct }}%</span>
            <span class="up-ratio">{{ item.up_ratio }}%↑</span>
          </div>
        </div>
      </div>

      <!-- 资金流入 TOP10 -->
      <div class="section">
        <div class="section-title">主力净流入 TOP10</div>
        <div class="money-list">
          <div
            v-for="(item, idx) in data.top_money_flow"
            :key="item.ts_code"
            class="money-row"
            @click="$emit('selectStock', item.ts_code)"
          >
            <span class="rank">{{ idx + 1 }}</span>
            <span class="stock-name">{{ item.name }}</span>
            <span class="money-val up">{{ formatMoney(item.net_mf_vol) }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import * as echarts from 'echarts'
import { getMarketAnalysis } from '@/api'

const props = defineProps({
  refreshKey: { type: Number, default: 0 },
})
const emit = defineEmits(['selectStock'])

const data = ref(null)
const loading = ref(true)
const distChartRef = ref(null)
let distChart = null
let resizeObserver = null

const initDistChart = () => {
  if (!data.value || !distChartRef.value) return
  if (distChart) distChart.dispose()
  distChart = echarts.init(distChartRef.value, 'dark')

  const dist = data.value.pct_distribution
  if (!dist) return
  const categories = ['涨停', '7~10%', '5~7%', '3~5%', '1~3%', '0~1%', '平盘', '-0~1%', '-1~3%', '-3~5%', '-5~7%', '-7~10%', '跌停']
  const values = [
    dist.limit_up, dist.gt7, dist.gt5, dist.gt3, dist.gt1, dist.gt0,
    dist.eq0, dist.lt0, dist.lt_1, dist.lt_3, dist.lt_5, dist.lt_7, dist.limit_down,
  ]
  const colors = values.map((v, i) => {
    if (i < 6) return '#ef4444'
    if (i === 6) return '#6b7280'
    return '#22c55e'
  })

  distChart.setOption({
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: 2, right: 2, top: 1, bottom: 12 },
    xAxis: {
      type: 'category',
      data: categories,
      axisLabel: { color: '#9ca3af', fontSize: 7, rotate: 30 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#9ca3af', fontSize: 7 },
      splitLine: { lineStyle: { color: '#1f2937' } },
    },
    series: [{
      type: 'bar',
      data: values.map((v, i) => ({ value: v, itemStyle: { color: colors[i] } })),
      barWidth: '75%',
    }],
  })
}

const formatMoney = (val) => {
  if (!val && val !== 0) return '--'
  const abs = Math.abs(val)
  if (abs >= 1e8) return (val / 1e8).toFixed(2) + '亿'
  if (abs >= 1e4) return (val / 1e4).toFixed(0) + '万'
  return val.toFixed(0)
}

const fetchData = async () => {
  loading.value = true
  try {
    data.value = await getMarketAnalysis()
    await nextTick()
    initDistChart()
    if (distChartRef.value && !resizeObserver) {
      resizeObserver = new ResizeObserver(() => distChart?.resize())
      resizeObserver.observe(distChartRef.value)
    }
  } catch (e) {
    console.error('获取市场分析失败:', e)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)
watch(() => props.refreshKey, fetchData)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  distChart?.dispose()
})
</script>

<style scoped>
.market-analysis {
  height: 100%;
  overflow-y: auto;
  padding: 8px 10px 2px;
  font-size: 12px;
  display: flex;
  flex-direction: column;
}

.loading-state, .empty-state {
  color: var(--text-secondary);
  text-align: center;
  padding: 20px;
}

.overview-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-bottom: 4px;
  flex-shrink: 0;
}

.card {
  background: var(--bg-card);
  border-radius: 6px;
  border: 1px solid var(--border);
  padding: 7px 10px;
  text-align: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.25);
}

.card-label {
  color: var(--text-secondary);
  font-size: 10px;
  margin-bottom: 1px;
}

.card-value {
  font-size: 17px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-primary);
}

.card-value.up { color: var(--up-color); }
.card-value.down { color: var(--down-color); }

.card-sub {
  color: var(--text-secondary);
  font-size: 9px;
}

.section {
  margin-bottom: 0;
  flex-shrink: 0;
}

.section:last-child {
  margin-bottom: 0;
}

.section-title {
  color: var(--text-primary);
  font-size: 11px;
  font-weight: 600;
  margin-bottom: 2px;
  padding-left: 2px;
  padding-bottom: 1px;
  border-bottom: 1px solid var(--border);
}

.chart-box {
  width: 100%;
  height: 75px;
}

.industry-list, .money-list {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.industry-row, .money-row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px;
  border-radius: 3px;
  height: 24px;
  border-bottom: 1px dashed rgba(37, 45, 56, 0.5);
}

.industry-row:last-child, .money-row:last-child {
  border-bottom: none;
}

.industry-row:hover, .money-row:hover {
  background: rgba(255,255,255,0.03);
}

.money-row {
  cursor: pointer;
}

.rank {
  width: 16px;
  text-align: center;
  font-weight: 700;
  color: var(--text-secondary);
  font-size: 10px;
  flex-shrink: 0;
}

.industry-row:nth-child(1) .rank,
.industry-row:nth-child(2) .rank,
.industry-row:nth-child(3) .rank {
  color: #E8C07D;
}

.ind-name, .stock-name {
  width: 52px;
  flex-shrink: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--text-primary);
  font-size: 11px;
}

.stock-name {
  flex: 1;
  width: auto;
}

.bar-wrap {
  flex: 1;
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s;
}

.pct {
  width: 48px;
  text-align: right;
  font-family: var(--font-mono);
  font-size: 11px;
  flex-shrink: 0;
}

.pct.up { color: var(--up-color); }
.pct.down { color: var(--down-color); }

.up-ratio {
  width: 32px;
  text-align: right;
  color: var(--up-color);
  font-size: 9px;
  flex-shrink: 0;
}

.money-val {
  font-family: var(--font-mono);
  font-size: 11px;
  color: var(--up-color);
  white-space: nowrap;
}

.money-row:nth-child(1),
.money-row:nth-child(2),
.money-row:nth-child(3) {
  background: rgba(242, 54, 69, 0.05);
}
</style>