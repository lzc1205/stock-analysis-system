<template>
  <div class="kline-wrapper">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  data: { type: Array, default: () => [] },
  tsCode: { type: String, default: '' },
  activeIndicator: { type: String, default: 'MA' },
})

const chartRef = ref(null)
let chartInstance = null
let resizeObserver = null

/* ===== 指标计算函数 ===== */

// EMA
const ema = (data, period) => {
  const result = new Array(data.length).fill(null)
  if (data.length < period) return result
  const k = 2 / (period + 1)
  let prev = data.slice(0, period).reduce((a, b) => a + b, 0) / period
  result[period - 1] = prev
  for (let i = period; i < data.length; i++) {
    prev = (data[i] - prev) * k + prev
    result[i] = prev
  }
  return result
}

// BOLL: 布林带 (20, 2)
const calcBoll = (closes) => {
  const n = closes.length
  const mid = new Array(n).fill(null)
  const upper = new Array(n).fill(null)
  const lower = new Array(n).fill(null)
  const period = 20
  for (let i = period - 1; i < n; i++) {
    const slice = closes.slice(i - period + 1, i + 1)
    const avg = slice.reduce((a, b) => a + b, 0) / period
    const variance = slice.reduce((s, v) => s + (v - avg) ** 2, 0) / period
    const std = Math.sqrt(variance)
    mid[i] = avg
    upper[i] = avg + 2 * std
    lower[i] = avg - 2 * std
  }
  return { mid, upper, lower }
}

// MACD: DIF(EMA12-EMA26), DEA(EMA9 of DIF), MACD柱(2*(DIF-DEA))
const calcMacd = (closes) => {
  const ema12 = ema(closes, 12)
  const ema26 = ema(closes, 26)
  const n = closes.length
  const dif = new Array(n).fill(null)
  const dea = new Array(n).fill(null)
  const macd = new Array(n).fill(null)
  for (let i = 0; i < n; i++) {
    if (ema12[i] != null && ema26[i] != null) {
      dif[i] = ema12[i] - ema26[i]
    }
  }
  const difValid = dif.filter((v) => v != null)
  const deaValues = ema(difValid, 9)
  let deaIdx = 0
  for (let i = 0; i < n; i++) {
    if (dif[i] != null) {
      if (deaIdx < deaValues.length) {
        dea[i] = deaValues[deaIdx]
        deaIdx++
      }
    }
  }
  for (let i = 0; i < n; i++) {
    if (dif[i] != null && dea[i] != null) {
      macd[i] = (dif[i] - dea[i]) * 2
    }
  }
  return { dif, dea, macd }
}

// KDJ (9, 3, 3)
const calcKdj = (highs, lows, closes) => {
  const n = closes.length
  const period = 9
  const k = new Array(n).fill(null)
  const d = new Array(n).fill(null)
  const j = new Array(n).fill(null)
  let prevK = 50, prevD = 50
  for (let i = period - 1; i < n; i++) {
    const h = Math.max(...highs.slice(i - period + 1, i + 1))
    const l = Math.min(...lows.slice(i - period + 1, i + 1))
    const rsv = h === l ? 50 : ((closes[i] - l) / (h - l)) * 100
    prevK = (2 / 3) * prevK + (1 / 3) * rsv
    prevD = (2 / 3) * prevD + (1 / 3) * prevK
    k[i] = prevK
    d[i] = prevD
    j[i] = 3 * prevK - 2 * prevD
  }
  return { k, d, j }
}

// RSI (14)
const calcRsi = (closes, period = 14) => {
  const n = closes.length
  const rsi = new Array(n).fill(null)
  if (n < period + 1) return rsi
  let avgGain = 0, avgLoss = 0
  for (let i = 1; i <= period; i++) {
    const diff = closes[i] - closes[i - 1]
    if (diff > 0) avgGain += diff
    else avgLoss -= diff
  }
  avgGain /= period
  avgLoss /= period
  rsi[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss)
  for (let i = period + 1; i < n; i++) {
    const diff = closes[i] - closes[i - 1]
    const gain = diff > 0 ? diff : 0
    const loss = diff < 0 ? -diff : 0
    avgGain = (avgGain * (period - 1) + gain) / period
    avgLoss = (avgLoss * (period - 1) + loss) / period
    rsi[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss)
  }
  return rsi
}

/* ===== 图表构建 ===== */

const initChart = () => {
  if (!chartRef.value) return
  chartInstance = echarts.init(chartRef.value, 'dark')
  updateChart()
}

const buildTooltip = (indicator) => {
  const indicatorLines = {
    MA: (params) => {
      const idx = params[0]?.dataIndex
      return `<div>MA5 <span style="color:#E6C07B">${props.data[idx]?.ma5?.toFixed(2) || '--'}</span>
        &nbsp;MA10 <span style="color:#5B8DEF">${props.data[idx]?.ma10?.toFixed(2) || '--'}</span></div>
        <div>MA20 <span style="color:#C792EA">${props.data[idx]?.ma20?.toFixed(2) || '--'}</span>
        &nbsp;MA60 <span style="color:#7D8590">${props.data[idx]?.ma60?.toFixed(2) || '--'}</span></div>`
    },
    BOLL: (params) => {
      const b = params.find((p) => p.seriesName === 'MID')
      return b ? `<div>BOLL 上轨 <span style="color:#C792EA">${b.data?.toFixed(2) || '--'}</span>
        &nbsp;中轨 <span style="color:#E6C07B">${params.find(p => p.seriesName === 'MID')?.data?.toFixed(2) || '--'}</span>
        &nbsp;下轨 <span style="color:#C792EA">${params.find(p => p.seriesName === 'LOWER')?.data?.toFixed(2) || '--'}</span></div>` : ''
    },
    MACD: (params) => {
      const dif = params.find((p) => p.seriesName === 'DIF')
      const dea = params.find((p) => p.seriesName === 'DEA')
      const macd = params.find((p) => p.seriesName === 'MACD')
      if (!dif) return ''
      return `<div>DIF <span style="color:#5B8DEF">${dif.data?.toFixed(4) || '--'}</span>
        &nbsp;DEA <span style="color:#E6C07B">${dea?.data?.toFixed(4) || '--'}</span>
        &nbsp;MACD <span style="color:${macd?.data >= 0 ? '#F23645' : '#089981'}">${macd?.data?.toFixed(4) || '--'}</span></div>`
    },
    KDJ: (params) => {
      const k = params.find((p) => p.seriesName === 'K')
      const d = params.find((p) => p.seriesName === 'D')
      const j = params.find((p) => p.seriesName === 'J')
      if (!k) return ''
      return `<div>K <span style="color:#5B8DEF">${k.data?.toFixed(2) || '--'}</span>
        &nbsp;D <span style="color:#E6C07B">${d?.data?.toFixed(2) || '--'}</span>
        &nbsp;J <span style="color:#C792EA">${j?.data?.toFixed(2) || '--'}</span></div>`
    },
    RSI: (params) => {
      const r = params.find((p) => p.seriesName === 'RSI(14)')
      return r ? `<div>RSI(14) <span style="color:#C792EA">${r.data?.toFixed(2) || '--'}</span></div>` : ''
    },
  }

  return {
    trigger: 'axis',
    axisPointer: { type: 'cross' },
    backgroundColor: '#1C2128',
    borderColor: '#252D38',
    borderRadius: 6,
    padding: [8, 12],
    textStyle: { color: '#E6EDF3', fontSize: 12, fontFamily: 'JetBrains Mono, Consolas, monospace' },
    formatter: (params) => {
      const date = params[0]?.axisValue || ''
      const k = params.find((p) => p.seriesName === 'K线')
      if (!k) return ''
      const idx = k.dataIndex
      const d = k.data
      const pct = props.data[idx]?.pct_chg
      const pctColor = pct >= 0 ? '#F23645' : '#089981'
      const pctStr = pct != null ? `<span style="color:${pctColor}">${pct >= 0 ? '+' : ''}${pct.toFixed(2)}%</span>` : '--'
      const vol = props.data[idx]?.vol || 0
      const volStr = vol >= 1e8 ? (vol / 1e8).toFixed(2) + '亿手' : (vol / 1e4).toFixed(2) + '万手'
      let html = `<div style="margin-bottom:4px;color:#E6EDF3;font-weight:600">${date}</div>
        <div>开 <b>${d[1]?.toFixed(2)}</b>&nbsp;&nbsp;收 <b>${d[2]?.toFixed(2)}</b></div>
        <div>高 ${d[3]?.toFixed(2)}&nbsp;&nbsp;低 ${d[4]?.toFixed(2)}</div>
        <div style="margin-bottom:4px">涨跌幅 ${pctStr}</div>
        <div>成交量 ${volStr}</div>`
      const extra = (indicatorLines[indicator] || (() => ''))(params)
      return html + extra
    },
  }
}

const updateChart = () => {
  if (!chartInstance || !props.data || props.data.length === 0) return

  const indicator = props.activeIndicator || 'MA'
  const dates = props.data.map((d) => d.trade_date)
  const ohlc = props.data.map((d) => [d.open, d.close, d.low, d.high])
  const volumes = props.data.map((d) => d.vol)
  const closes = props.data.map((d) => d.close)
  const highs = props.data.map((d) => d.high)
  const lows = props.data.map((d) => d.low)

  const ma5 = props.data.map((d) => d.ma5)
  const ma10 = props.data.map((d) => d.ma10)
  const ma20 = props.data.map((d) => d.ma20)
  const ma60 = props.data.map((d) => d.ma60)

  // 计算各个指标
  const boll = calcBoll(closes)
  const macdData = calcMacd(closes)
  const kdjData = calcKdj(highs, lows, closes)
  const rsiData = calcRsi(closes, 14)

  // 是否需要副图指标区（MACD/KDJ/RSI）
  const needsIndicatorPane = ['MACD', 'KDJ', 'RSI'].includes(indicator)

  // 网格布局
  let grid, xAxisArr, yAxisArr

  if (needsIndicatorPane) {
    grid = [
      { left: '1%', right: '1%', top: '3%', height: '42%' },
      { left: '8%', right: '1%', top: '54%', height: '14%' },
      { left: '8%', right: '1%', top: '73%', height: '14%' },
    ]
    xAxisArr = [
      {
        type: 'category', data: dates, gridIndex: 0, boundaryGap: true,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, axisTick: { show: false },
        axisLabel: { show: false },
        splitLine: { show: false },
      },
      {
        type: 'category', data: dates, gridIndex: 1, boundaryGap: true,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, axisTick: { show: false },
        axisLabel: { show: false },
        splitLine: { show: false },
      },
      {
        type: 'category', data: dates, gridIndex: 2, boundaryGap: true,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, axisTick: { show: false },
        axisLabel: {
          show: true, fontSize: 11, color: '#6B7280',
          fontFamily: 'JetBrains Mono, Consolas, monospace',
          interval: Math.max(1, Math.floor(dates.length / 6)),
          formatter: (val) => val?.slice(5) || val,
        },
        splitLine: { show: false },
      },
    ]
    yAxisArr = [
      {
        type: 'value', gridIndex: 0, scale: true, position: 'right',
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { fontSize: 11, color: '#6B7280', fontFamily: 'JetBrains Mono, Consolas, monospace', formatter: (v) => v.toFixed(2) },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'solid' } },
      },
      {
        type: 'value', gridIndex: 1,
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { fontSize: 9, color: '#6B7280', fontFamily: 'JetBrains Mono, Consolas, monospace' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'solid' } },
      },
      {
        type: 'value', gridIndex: 2, name: '成交量',
        nameTextStyle: { color: '#6B7280', fontSize: 10 },
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { fontSize: 10, color: '#6B7280', fontFamily: 'JetBrains Mono, Consolas, monospace', formatter: (v) => (v / 10000).toFixed(0) + '万' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'solid' } },
      },
    ]
  } else {
    grid = [
      { left: '1%', right: '1%', top: '3%', height: '55%' },
      { left: '8%', right: '1%', top: '71%', height: '17%' },
    ]
    xAxisArr = [
      {
        type: 'category', data: dates, gridIndex: 0, boundaryGap: true,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, axisTick: { show: false },
        axisLabel: {
          show: true, fontSize: 11, color: '#6B7280',
          fontFamily: 'JetBrains Mono, Consolas, monospace',
          interval: Math.max(1, Math.floor(dates.length / 6)),
          formatter: (val) => val?.slice(5) || val,
        },
        splitLine: { show: false },
      },
      {
        type: 'category', data: dates, gridIndex: 1, boundaryGap: true,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, axisTick: { show: false },
        axisLabel: { show: false },
        splitLine: { show: false },
      },
    ]
    yAxisArr = [
      {
        type: 'value', gridIndex: 0, scale: true, position: 'right',
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { fontSize: 11, color: '#6B7280', fontFamily: 'JetBrains Mono, Consolas, monospace', formatter: (v) => v.toFixed(2) },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'solid' } },
      },
      {
        type: 'value', gridIndex: 1, name: '成交量',
        nameTextStyle: { color: '#6B7280', fontSize: 10 },
        axisLine: { show: false }, axisTick: { show: false },
        axisLabel: { fontSize: 10, color: '#6B7280', fontFamily: 'JetBrains Mono, Consolas, monospace', formatter: (v) => (v / 10000).toFixed(0) + '万' },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)', type: 'solid' } },
      },
    ]
  }

  // 基础 series（K线 + 成交量）
  const baseSeries = [
    {
      name: 'K线', type: 'candlestick', data: ohlc,
      xAxisIndex: 0, yAxisIndex: 0,
      barWidth: '60%',
      barMaxWidth: 12,
      itemStyle: {
        color: '#F23645', color0: '#089981',
        borderColor: '#F23645', borderColor0: '#089981',
      },
    },
  ]

  // 成交量 series
  const volIdx = needsIndicatorPane ? 2 : 1
  const volSeries = {
    name: '成交量', type: 'bar', data: volumes,
    xAxisIndex: volIdx, yAxisIndex: volIdx,
    itemStyle: {
      opacity: 0.75,
      color: (params) => {
        const idx = params.dataIndex
        const item = ohlc[idx]
        if (!item) return '#089981'
        return item[1] >= item[0] ? '#F23645' : '#089981'
      },
    },
  }

  // 指标 series
  let indicatorSeries = []
  let legendData = ['K线']

  switch (indicator) {
    case 'MA':
      legendData.push('MA5', 'MA10', 'MA20', 'MA60')
      indicatorSeries = [
        { name: 'MA5', type: 'line', data: ma5, xAxisIndex: 0, yAxisIndex: 0, smooth: true, lineStyle: { width: 1.5, color: '#E8C07D' }, symbol: 'none' },
        { name: 'MA10', type: 'line', data: ma10, xAxisIndex: 0, yAxisIndex: 0, smooth: true, lineStyle: { width: 1.5, color: '#5B8DEF' }, symbol: 'none' },
        { name: 'MA20', type: 'line', data: ma20, xAxisIndex: 0, yAxisIndex: 0, smooth: true, lineStyle: { width: 1.5, color: '#C792EA' }, symbol: 'none' },
        { name: 'MA60', type: 'line', data: ma60, xAxisIndex: 0, yAxisIndex: 0, smooth: true, lineStyle: { width: 1.2, color: '#7D8590', type: 'dashed' }, symbol: 'none' },
      ]
      break
    case 'BOLL':
      legendData.push('UPPER', 'MID', 'LOWER')
      indicatorSeries = [
        { name: 'UPPER', type: 'line', data: boll.upper, xAxisIndex: 0, yAxisIndex: 0, smooth: true, lineStyle: { width: 1, color: '#C792EA', type: 'dashed' }, symbol: 'none' },
        { name: 'MID', type: 'line', data: boll.mid, xAxisIndex: 0, yAxisIndex: 0, smooth: true, lineStyle: { width: 1, color: '#E6C07B' }, symbol: 'none' },
        { name: 'LOWER', type: 'line', data: boll.lower, xAxisIndex: 0, yAxisIndex: 0, smooth: true, lineStyle: { width: 1, color: '#C792EA', type: 'dashed' }, symbol: 'none' },
      ]
      break
    case 'MACD':
      legendData.push('DIF', 'DEA', 'MACD')
      indicatorSeries = [
        { name: 'DIF', type: 'line', data: macdData.dif, xAxisIndex: 1, yAxisIndex: 1, smooth: true, lineStyle: { width: 1, color: '#5B8DEF' }, symbol: 'none' },
        { name: 'DEA', type: 'line', data: macdData.dea, xAxisIndex: 1, yAxisIndex: 1, smooth: true, lineStyle: { width: 1, color: '#E6C07B' }, symbol: 'none' },
        { name: 'MACD', type: 'bar', data: macdData.macd, xAxisIndex: 1, yAxisIndex: 1,
          itemStyle: {
            color: (params) => params.data >= 0 ? '#F23645' : '#089981',
          },
        },
      ]
      break
    case 'KDJ':
      legendData.push('K', 'D', 'J')
      indicatorSeries = [
        { name: 'K', type: 'line', data: kdjData.k, xAxisIndex: 1, yAxisIndex: 1, smooth: true, lineStyle: { width: 1, color: '#5B8DEF' }, symbol: 'none' },
        { name: 'D', type: 'line', data: kdjData.d, xAxisIndex: 1, yAxisIndex: 1, smooth: true, lineStyle: { width: 1, color: '#E6C07B' }, symbol: 'none' },
        { name: 'J', type: 'line', data: kdjData.j, xAxisIndex: 1, yAxisIndex: 1, smooth: true, lineStyle: { width: 1, color: '#C792EA' }, symbol: 'none' },
      ]
      break
    case 'RSI':
      legendData.push('RSI(14)')
      indicatorSeries = [
        { name: 'RSI(14)', type: 'line', data: rsiData, xAxisIndex: 1, yAxisIndex: 1, smooth: true, lineStyle: { width: 1, color: '#C792EA' }, symbol: 'none' },
      ]
      break
  }

  const allSeries = [...baseSeries, ...indicatorSeries, volSeries]

  // dataZoom xAxisIndex
  const zoomIndices = needsIndicatorPane ? [0, 1, 2] : [0, 1]

  const option = {
    backgroundColor: 'transparent',
    legend: {
      data: legendData,
      top: 0,
      left: 'center',
      textStyle: { color: '#8B95A5', fontSize: 11 },
      itemWidth: 12,
      itemHeight: 2,
      itemGap: 16,
      icon: 'roundRect',
    },
    tooltip: buildTooltip(indicator),
    grid,
    xAxis: xAxisArr,
    yAxis: yAxisArr,
    series: allSeries,
    dataZoom: [
      { type: 'inside', xAxisIndex: zoomIndices, start: 50, end: 100 },
      {
        type: 'slider', xAxisIndex: zoomIndices, start: 50, end: 100,
        height: 16, bottom: 4,
        borderColor: '#252D38', backgroundColor: 'rgba(20,26,34,0.8)',
        fillerColor: 'rgba(59,130,246,0.12)',
        handleStyle: { color: '#6B7280' },
        textStyle: { color: '#6B7280', fontSize: 9 },
      },
    ],
  }

  chartInstance.setOption(option, true)
}

watch(
  () => props.data,
  () => { if (props.data && props.data.length > 0) updateChart() },
  { deep: true },
)

watch(
  () => props.activeIndicator,
  () => { if (props.data && props.data.length > 0) updateChart() },
)

onMounted(() => {
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
.kline-wrapper {
  width: 100%;
  height: 100%;
  padding: 4px;
}

.chart-container {
  width: 100%;
  height: 100%;
}
</style>