<template>
  <div class="technical-panel">
    <h3 class="panel-title">技术指标面板</h3>
    <div class="indicator-grid">
      <!-- MA 移动平均线 -->
      <div class="indicator-section">
        <h4 class="indicator-label">MA 移动平均线</h4>
        <div class="ma-values">
          <div class="ma-item">
            <span class="ma-period">MA5</span>
            <span class="ma-value" :class="getTrendClass(ma5Trend)">{{ formatValue(data?.ma5) }}</span>
          </div>
          <div class="ma-item">
            <span class="ma-period">MA10</span>
            <span class="ma-value" :class="getTrendClass(ma10Trend)">{{ formatValue(data?.ma10) }}</span>
          </div>
          <div class="ma-item">
            <span class="ma-period">MA20</span>
            <span class="ma-value" :class="getTrendClass(ma20Trend)">{{ formatValue(data?.ma20) }}</span>
          </div>
          <div class="ma-item">
            <span class="ma-period">MA60</span>
            <span class="ma-value" :class="getTrendClass(ma60Trend)">{{ formatValue(data?.ma60) }}</span>
          </div>
        </div>
        <div class="ma-status">
          <span v-if="ma5Trend === 'up' && ma10Trend === 'up'" class="status bullish">多头排列 ↑</span>
          <span v-else-if="ma5Trend === 'down' && ma10Trend === 'down'" class="status bearish">空头排列 ↓</span>
          <span v-else class="status neutral">震荡整理 →</span>
        </div>
      </div>

      <!-- MACD -->
      <div class="indicator-section">
        <h4 class="indicator-label">MACD</h4>
        <div class="macd-values">
          <div class="macd-row">
            <span>DIF</span>
            <span :class="data?.dif >= 0 ? 'up' : 'down'">{{ formatValue(data?.dif) }}</span>
          </div>
          <div class="macd-row">
            <span>DEA</span>
            <span :class="data?.dea >= 0 ? 'up' : 'down'">{{ formatValue(data?.dea) }}</span>
          </div>
          <div class="macd-row">
            <span>MACD</span>
            <span :class="data?.macd_bar >= 0 ? 'up' : 'down'">{{ formatValue(data?.macd_bar) }}</span>
          </div>
        </div>
        <div class="macd-status">
          <span v-if="data?.dif > data?.dea" class="status bullish">金叉区域 ↑</span>
          <span v-else class="status bearish">死叉区域 ↓</span>
        </div>
      </div>

      <!-- RSI -->
      <div class="indicator-section">
        <h4 class="indicator-label">RSI 相对强弱</h4>
        <div class="rsi-bars">
          <div class="rsi-bar-row">
            <span>RSI6</span>
            <div class="rsi-track">
              <div class="rsi-fill" :style="{ width: (data?.rsi6 || 50) + '%' }"
                :class="getRSIClass(data?.rsi6)"></div>
            </div>
            <span class="rsi-num">{{ formatValue(data?.rsi6) }}</span>
          </div>
          <div class="rsi-bar-row">
            <span>RSI12</span>
            <div class="rsi-track">
              <div class="rsi-fill" :style="{ width: (data?.rsi12 || 50) + '%' }"
                :class="getRSIClass(data?.rsi12)"></div>
            </div>
            <span class="rsi-num">{{ formatValue(data?.rsi12) }}</span>
          </div>
          <div class="rsi-bar-row">
            <span>RSI24</span>
            <div class="rsi-track">
              <div class="rsi-fill" :style="{ width: (data?.rsi24 || 50) + '%' }"
                :class="getRSIClass(data?.rsi24)"></div>
            </div>
            <span class="rsi-num">{{ formatValue(data?.rsi24) }}</span>
          </div>
        </div>
        <div class="rsi-status">
          <span v-if="(data?.rsi6 || 50) > 70" class="status bearish">超买区域</span>
          <span v-else-if="(data?.rsi6 || 50) < 30" class="status bullish">超卖区域</span>
          <span v-else class="status neutral">正常区间</span>
        </div>
      </div>

      <!-- KDJ -->
      <div class="indicator-section">
        <h4 class="indicator-label">KDJ 随机指标</h4>
        <div class="kdj-values">
          <div class="kdj-row">
            <span>K</span>
            <span :class="getKDJClass(data?.k)">{{ formatValue(data?.k) }}</span>
          </div>
          <div class="kdj-row">
            <span>D</span>
            <span :class="getKDJClass(data?.d)">{{ formatValue(data?.d) }}</span>
          </div>
          <div class="kdj-row">
            <span>J</span>
            <span :class="getKDJClass(data?.j)">{{ formatValue(data?.j) }}</span>
          </div>
        </div>
        <div class="kdj-status">
          <span v-if="data?.k > data?.d && data?.j > data?.k" class="status bullish">强势金叉 ↑</span>
          <span v-else-if="data?.k > data?.d" class="status bullish">金叉 ↑</span>
          <span v-else-if="data?.k < data?.d" class="status bearish">死叉 ↓</span>
          <span v-else class="status neutral">粘合 →</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: {
    type: Object,
    default: () => ({})
  }
})

const ma5Trend = computed(() => {
  const v = props.data?.ma5 || 0
  return v > 0 ? 'up' : v < 0 ? 'down' : 'neutral'
})

const ma10Trend = computed(() => {
  const v = props.data?.ma10 || 0
  return v > 0 ? 'up' : v < 0 ? 'down' : 'neutral'
})

const ma20Trend = computed(() => {
  const v = props.data?.ma20 || 0
  return v > 0 ? 'up' : v < 0 ? 'down' : 'neutral'
})

const ma60Trend = computed(() => {
  const v = props.data?.ma60 || 0
  return v > 0 ? 'up' : v < 0 ? 'down' : 'neutral'
})

function formatValue(val) {
  if (val === null || val === undefined) return '--'
  return Number(val).toFixed(2)
}

function getTrendClass(trend) {
  return { up: trend === 'up', down: trend === 'down' }
}

function getRSIClass(val) {
  if (!val) return ''
  if (val > 70) return 'rsi-overbought'
  if (val < 30) return 'rsi-oversold'
  return 'rsi-normal'
}

function getKDJClass(val) {
  if (!val && val !== 0) return ''
  if (val > 80) return 'kdj-overbought'
  if (val < 20) return 'kdj-oversold'
  return ''
}
</script>

<style scoped>
.technical-panel {
  padding: 12px;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #00d4ff;
  margin: 0 0 10px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(0, 150, 255, 0.2);
}

.indicator-grid {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-y: auto;
}

.indicator-section {
  background: rgba(0, 150, 255, 0.05);
  border-radius: 6px;
  padding: 10px;
  border: 1px solid rgba(0, 150, 255, 0.1);
}

.indicator-label {
  font-size: 12px;
  color: #8899aa;
  margin: 0 0 6px 0;
  font-weight: 500;
}

.ma-values {
  display: flex;
  gap: 8px;
  margin-bottom: 6px;
}

.ma-item {
  flex: 1;
  text-align: center;
}

.ma-period {
  font-size: 10px;
  color: #667788;
  display: block;
}

.ma-value {
  font-size: 13px;
  font-family: monospace;
  font-weight: 600;
}

.ma-value.up { color: #ff4d4f; }
.ma-value.down { color: #00e676; }

.macd-values {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 6px;
}

.macd-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-family: monospace;
}

.macd-row span:first-child {
  color: #667788;
}

.macd-row .up { color: #ff4d4f; }
.macd-row .down { color: #00e676; }

.rsi-bars {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 6px;
}

.rsi-bar-row {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
}

.rsi-bar-row > span:first-child {
  width: 36px;
  color: #667788;
  flex-shrink: 0;
}

.rsi-track {
  flex: 1;
  height: 6px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 3px;
  overflow: hidden;
}

.rsi-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s;
}

.rsi-fill.rsi-normal { background: #00d4ff; }
.rsi-fill.rsi-overbought { background: #ff4d4f; }
.rsi-fill.rsi-oversold { background: #00e676; }

.rsi-num {
  width: 40px;
  text-align: right;
  font-family: monospace;
  font-size: 11px;
  color: #e0e6ed;
}

.kdj-values {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 6px;
}

.kdj-row {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  font-family: monospace;
}

.kdj-row span:first-child {
  color: #667788;
}

.kdj-row .kdj-overbought { color: #ff4d4f; }
.kdj-row .kdj-oversold { color: #00e676; }

.status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 3px;
  display: inline-block;
}

.status.bullish {
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

.status.bearish {
  color: #00e676;
  background: rgba(0, 230, 118, 0.1);
}

.status.neutral {
  color: #8899aa;
  background: rgba(136, 153, 170, 0.1);
}
</style>