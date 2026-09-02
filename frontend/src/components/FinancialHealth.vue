<template>
  <div class="financial-panel">
    <div class="empty-state" v-if="!data">
      <p>暂无财务数据</p>
    </div>
    <template v-else>
      <div class="health-header">
        <div class="health-score-area">
          <div class="score-ring">
            <svg viewBox="0 0 100 64" class="ring-svg">
              <path
                d="M 8 52 A 42 42 0 0 1 92 52"
                fill="none"
                stroke="#252B36"
                stroke-width="7"
                stroke-linecap="round"
              />
              <path
                d="M 8 52 A 42 42 0 0 1 92 52"
                fill="none"
                :stroke="scoreColor"
                stroke-width="7"
                stroke-linecap="round"
                :stroke-dasharray="`${(data.health_score || 0) * 1.32} 264`"
                class="score-arc"
              />
            </svg>
            <div class="score-text">
              <span class="score-num">{{ data.health_score?.toFixed(0) || '--' }}</span>
              <span class="score-label">分</span>
            </div>
          </div>
          <span class="health-level" :class="healthClass">{{ data.health_level || '--' }}</span>
        </div>
      </div>
      <div class="health-metrics">
        <div class="metric-row">
          <span class="metric-label">ROE</span>
          <span class="metric-value">{{ fmt(data.roe) }}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">毛利率</span>
          <span class="metric-value">{{ fmt(data.gross_margin) }}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">净利率</span>
          <span class="metric-value">{{ fmt(data.net_margin) }}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">资产负债率</span>
          <span class="metric-value">{{ fmt(data.debt_ratio) }}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">营收同比</span>
          <span class="metric-value" :class="(data.revenue_yoy || 0) >= 0 ? 'up' : 'down'">{{ fmt(data.revenue_yoy) }}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">净利润同比</span>
          <span class="metric-value" :class="(data.n_income_yoy || 0) >= 0 ? 'up' : 'down'">{{ fmt(data.n_income_yoy) }}</span>
        </div>
        <div class="metric-row">
          <span class="metric-label">EPS</span>
          <span class="metric-value">{{ data.eps != null ? data.eps.toFixed(4) : '--' }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  data: { type: Object, default: null },
})

const fmt = (val) => {
  if (val == null) return '--'
  return val.toFixed(2) + '%'
}

const healthClass = computed(() => {
  const level = props.data?.health_level
  if (level === '优秀' || level === '良好') return 'good'
  if (level === '一般') return 'normal'
  return 'bad'
})

const scoreColor = computed(() => {
  const score = props.data?.health_score || 0
  if (score >= 80) return '#089981'
  if (score >= 60) return '#E6C07B'
  if (score >= 40) return '#f5a623'
  return '#F23645'
})
</script>

<style scoped>
.financial-panel {
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.health-header {
  margin-bottom: 8px;
  flex-shrink: 0;
}

.health-score-area {
  display: flex;
  align-items: center;
  gap: 12px;
}

.score-ring {
  position: relative;
  width: 72px;
  height: 52px;
  flex-shrink: 0;
}

.ring-svg {
  width: 100%;
  height: 100%;
}

.score-arc {
  transition: stroke-dasharray 0.6s ease-out;
}

.score-text {
  position: absolute;
  top: 72%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
}

.score-num {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  font-family: var(--font-mono);
  line-height: 1;
}

.score-label {
  font-size: 9px;
  color: var(--text-secondary);
  display: block;
}

.health-level {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 10px;
  font-family: var(--font-mono);
}

.health-level.good {
  background: rgba(8, 153, 129, 0.12);
  color: #089981;
  border: 1px solid rgba(8, 153, 129, 0.2);
}

.health-level.normal {
  background: rgba(230, 192, 123, 0.12);
  color: #E6C07B;
  border: 1px solid rgba(230, 192, 123, 0.2);
}

.health-level.bad {
  background: rgba(242, 54, 69, 0.1);
  color: #F23645;
  border: 1px solid rgba(242, 54, 69, 0.15);
}

.health-metrics {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px dashed var(--border);
}

.metric-row:last-child {
  border-bottom: none;
}

.metric-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.metric-value {
  font-size: 12px;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-weight: 500;
}

.metric-value.up { color: var(--up-color); }
.metric-value.down { color: var(--down-color); }

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
  font-size: 13px;
}
</style>