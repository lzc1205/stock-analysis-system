<template>
  <div class="overview-panel">
    <div class="panel-top-bar">
      <span class="panel-title">个股概览</span>
      <span class="update-time" v-if="data?.update_date">{{ data.update_date }}</span>
    </div>
    <div class="data-table" v-if="data">
      <div class="table-row">
        <span class="row-label">成交量</span>
        <span class="row-value">{{ formatVolume(data.latest_vol) }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">成交额</span>
        <span class="row-value">{{ formatAmount(data.latest_amount) }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">市盈率</span>
        <span class="row-value">{{ data.pe != null ? data.pe.toFixed(2) : '--' }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">市净率</span>
        <span class="row-value">{{ data.pb != null ? data.pb.toFixed(2) : '--' }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">总市值</span>
        <span class="row-value">{{ formatMarketCap(data.total_mv) }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">流通市值</span>
        <span class="row-value">{{ formatMarketCap(data.circ_mv) }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">MA5</span>
        <span class="row-value" style="color: var(--ma5)">{{ data.ma5 != null ? data.ma5.toFixed(2) : '--' }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">MA20</span>
        <span class="row-value" style="color: var(--ma20)">{{ data.ma20 != null ? data.ma20.toFixed(2) : '--' }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">MACD DIF</span>
        <span class="row-value">{{ data.dif != null ? data.dif.toFixed(3) : '--' }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">MACD DEA</span>
        <span class="row-value">{{ data.dea != null ? data.dea.toFixed(3) : '--' }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">RSI(6)</span>
        <span class="row-value">{{ data.rsi6 != null ? data.rsi6.toFixed(2) : '--' }}</span>
      </div>
      <div class="table-row">
        <span class="row-label">主力净流入</span>
        <span class="row-value" :class="data.net_mf_vol >= 0 ? 'up' : 'down'">
          {{ formatAmount(data.net_mf_vol) }}
        </span>
      </div>
    </div>
    <div class="empty-state" v-else>
      <p>暂无数据</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  data: { type: Object, default: null },
})

const formatVolume = (val) => {
  if (!val) return '--'
  if (val >= 10000) return (val / 10000).toFixed(2) + '万手'
  return val.toFixed(0) + '手'
}

const formatAmount = (val) => {
  if (!val) return '--'
  const abs = Math.abs(val)
  if (abs >= 1e8) return (val / 1e8).toFixed(2) + '亿'
  if (abs >= 1e4) return (val / 1e4).toFixed(2) + '万'
  return val.toFixed(2)
}

const formatMarketCap = (val) => {
  if (!val) return '--'
  if (val >= 1e8) return (val / 1e8).toFixed(2) + '亿'
  if (val >= 1e4) return (val / 1e4).toFixed(2) + '万'
  return val.toFixed(2)
}
</script>

<style scoped>
.overview-panel {
  padding: 10px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #141A22;
}

.panel-top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  flex-shrink: 0;
  padding-bottom: 6px;
  border-bottom: 1px solid var(--border);
}

.panel-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-primary);
}

.update-time {
  font-size: 10px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.data-table {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.table-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 0;
  border-bottom: 1px dashed var(--border);
}

.table-row:last-child {
  border-bottom: none;
}

.row-label {
  font-size: 11px;
  color: var(--text-secondary);
}

.row-value {
  font-size: 12px;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-weight: 500;
}

.row-value.up { color: var(--up-color); }
.row-value.down { color: var(--down-color); }

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: var(--text-secondary);
  font-size: 13px;
}
</style>