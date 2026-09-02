<template>
  <div class="dashboard">
    <!-- 顶部信息栏 -->
    <header class="top-bar">
      <span class="top-title">个股金融数据可视化大屏</span>
      <div class="stock-search">
        <input
          v-model="searchKeyword"
          type="text"
          placeholder="搜索股票代码/名称..."
          @input="onSearch"
          @keyup.enter="onSelectFirst"
          @focus="onSearchFocus"
          class="search-input"
        />
        <div v-if="showDropdown && stockList.length > 0" class="search-dropdown">
          <div
            v-for="stock in stockList"
            :key="stock.ts_code"
            class="dropdown-item"
            @click="onSelectStock(stock)"
          >
            <span class="item-code">{{ stock.ts_code }}</span>
            <span class="item-name">{{ stock.name }}</span>
            <span class="item-price" :class="stock.latest_pct_chg >= 0 ? 'up' : 'down'">
              {{ stock.latest_price?.toFixed(2) }}
            </span>
          </div>
        </div>
      </div>
      <span class="stock-label">{{ stockName }} {{ currentStock }}</span>
      <span class="live-price" :class="priceChangeClass">{{ latestPrice }}</span>
      <span class="live-change" :class="priceChangeClass">
        <span class="change-arrow">{{ changeArrow }}</span>{{ latestPctChg }}%
      </span>
      <div class="live-clock">
        <span class="clock-date">{{ currentDate }}</span>
        <span class="clock-time">{{ currentTime }}</span>
      </div>
    </header>

    <!-- 主内容区域 -->
    <div class="main-area">
      <!-- 股票切换加载遮罩 -->
      <transition name="loading-fade">
        <div v-if="store.loading" class="loading-overlay">
          <div class="loading-spinner"></div>
          <span>切换中...</span>
        </div>
      </transition>
      <!-- 左侧数据面板 -->
      <div class="side-panel" :style="{ width: panelWidth + 'px', minWidth: panelWidth + 'px', flexShrink: 0 }">
        <div class="panel-tabs">
          <button
            v-for="tab in panelTabs"
            :key="tab.key"
            :class="['panel-tab', { active: activePanelTab === tab.key }]"
            @click="activePanelTab = tab.key"
          >{{ tab.label }}</button>
        </div>
        <div class="panel-content">
          <div v-if="activePanelTab === 'overview'" class="tab-content fade-in">
            <StockOverview :data="stockOverview" />
          </div>
          <div v-if="activePanelTab === 'capital'" class="tab-content fade-in">
            <CapitalFlow :data="capitalFlow" :tsCode="currentStock" />
          </div>
          <div v-if="activePanelTab === 'industry'" class="tab-content fade-in">
            <IndustryCompare :tsCode="currentStock" />
          </div>
          <div v-if="activePanelTab === 'financial'" class="tab-content fade-in">
            <FinancialHealth :data="financialHealth" />
          </div>
          <div v-if="activePanelTab === 'market'" class="tab-content fade-in">
            <MarketAnalysis :refreshKey="refreshKey" @selectStock="onMarketSelectStock" />
          </div>
        </div>
      </div>

      <!-- 拖拽分割条 -->
      <div class="splitter" @mousedown="onSplitterDragStart"></div>

      <!-- 右侧 K线主图 -->
      <div class="kline-zone">
        <div class="indicator-tabs">
          <button
            v-for="ind in indicators"
            :key="ind"
            :class="['ind-tab', { active: activeIndicator === ind }]"
            @click="activeIndicator = ind"
          >{{ ind }}</button>
        </div>
        <KLineChart :data="klineData" :tsCode="currentStock" :activeIndicator="activeIndicator" class="kline-chart" />
      </div>
    </div>

    <!-- AI 抽屉 -->
    <div class="ai-drawer-trigger" @click="showAIDrawer = !showAIDrawer">
      <span class="trigger-text">AI</span>
      <span class="trigger-icon">{{ showAIDrawer ? '▶' : '◀' }}</span>
    </div>
    <transition name="drawer-slide">
      <div v-if="showAIDrawer" class="ai-drawer">
        <AIChatAssistant :tsCode="currentStock" />
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useStockStore } from '@/stores/stock'
import StockOverview from '@/components/StockOverview.vue'
import KLineChart from '@/components/KLineChart.vue'
import CapitalFlow from '@/components/CapitalFlow.vue'
import IndustryCompare from '@/components/IndustryCompare.vue'
import FinancialHealth from '@/components/FinancialHealth.vue'
import MarketAnalysis from '@/components/MarketAnalysis.vue'
import AIChatAssistant from '@/components/AIChatAssistant.vue'

const store = useStockStore()
const searchKeyword = ref('')
const showDropdown = ref(false)
const showAIDrawer = ref(false)
const activePanelTab = ref('overview')
const activeIndicator = ref('MA')
const panelWidth = ref(320)
const refreshKey = ref(0)

const indicators = ['MA', 'BOLL', 'MACD', 'KDJ', 'RSI']
const panelTabs = [
  { key: 'overview', label: '概览' },
  { key: 'capital', label: '资金' },
  { key: 'industry', label: '行业' },
  { key: 'financial', label: '财务' },
  { key: 'market', label: '市场' },
]

const currentStock = computed(() => store.currentStock)
const stockName = computed(() => store.stockName)
const stockList = computed(() => store.stockList)
const stockOverview = computed(() => store.dashboardData?.stock_overview)
const klineData = computed(() => store.dashboardData?.kline_data || [])
const capitalFlow = computed(() => store.dashboardData?.capital_flow || [])
const financialHealth = computed(() => store.dashboardData?.financial_health)

const latestPrice = computed(() => {
  const p = stockOverview.value?.latest_price
  return p != null ? p.toFixed(2) : '--'
})

const latestPctChg = computed(() => {
  const p = stockOverview.value?.latest_pct_chg
  return p != null ? (p >= 0 ? '+' : '') + p.toFixed(2) : '0.00'
})

const priceChangeClass = computed(() => {
  const p = stockOverview.value?.latest_pct_chg
  if (p == null) return ''
  return p >= 0 ? 'up' : 'down'
})

const changeArrow = computed(() => {
  const p = stockOverview.value?.latest_pct_chg
  if (p == null) return ''
  return p >= 0 ? '▲' : '▼'
})

const currentDate = ref('')
const currentTime = ref('')
let clockTimer = null

const updateClock = () => {
  const now = new Date()
  const y = now.getFullYear()
  const m = String(now.getMonth() + 1).padStart(2, '0')
  const d = String(now.getDate()).padStart(2, '0')
  const hh = String(now.getHours()).padStart(2, '0')
  const mm = String(now.getMinutes()).padStart(2, '0')
  const ss = String(now.getSeconds()).padStart(2, '0')
  currentDate.value = `${y}-${m}-${d}`
  currentTime.value = `${hh}:${mm}:${ss}`
}

let searchTimer = null
const onSearchFocus = () => {
  if (stockList.value.length > 0) showDropdown.value = true
}
const onSearch = () => {
  clearTimeout(searchTimer)
  if (searchKeyword.value.trim()) {
    showDropdown.value = true
    searchTimer = setTimeout(() => store.fetchStockList(searchKeyword.value.trim()), 300)
  } else {
    showDropdown.value = false
  }
}
const onSelectStock = (stock) => {
  searchKeyword.value = `${stock.ts_code} ${stock.name}`
  showDropdown.value = false
  store.selectStock(stock.ts_code)
}
const onSelectFirst = () => {
  if (stockList.value.length > 0) onSelectStock(stockList.value[0])
}
const onMarketSelectStock = (tsCode) => {
  store.selectStock(tsCode)
}

const onSplitterDragStart = (e) => {
  e.preventDefault()
  const startX = e.clientX
  const startWidth = panelWidth.value
  const onMouseMove = (ev) => {
    const delta = ev.clientX - startX
    const newWidth = Math.max(260, Math.min(500, startWidth + delta))
    panelWidth.value = newWidth
  }
  const onMouseUp = () => {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }
  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

onMounted(() => {
  store.fetchStockList()
  store.fetchDashboardData('600000.SH')
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
})

onBeforeUnmount(() => {
  clearInterval(clockTimer)
})
</script>

<style scoped>
.dashboard {
  width: 100%;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: transparent;
  overflow: hidden;
}

/* 顶部信息栏 */
.top-bar {
  height: 48px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 16px;
  background: #141A22;
  border-bottom: 1px solid #252D38;
  flex-shrink: 0;
}

.top-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  margin-right: 8px;
  letter-spacing: 1px;
}

.stock-search {
  position: relative;
}

.search-input {
  width: 200px;
  height: 30px;
  padding: 0 10px;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-input);
  color: var(--text-primary);
  font-size: 12px;
  font-family: var(--font-mono);
  outline: none;
}

.search-input:focus {
  border-color: var(--accent);
}

.search-input::placeholder {
  color: var(--text-secondary);
}

.search-dropdown {
  position: absolute;
  top: 36px;
  left: 0;
  width: 240px;
  max-height: 260px;
  overflow-y: auto;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-radius: 4px;
  z-index: 100;
}

.dropdown-item {
  display: flex;
  align-items: center;
  padding: 7px 10px;
  cursor: pointer;
  gap: 8px;
  font-size: 12px;
}

.dropdown-item:hover {
  background: var(--bg-hover);
}

.item-code {
  color: var(--accent);
  font-family: var(--font-mono);
}

.item-name {
  flex: 1;
}

.item-price {
  font-family: var(--font-mono);
}
.item-price.up { color: var(--up-color); }
.item-price.down { color: var(--down-color); }

.stock-label {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
}

.live-price {
  font-size: 20px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-primary);
}

.live-change {
  font-size: 14px;
  font-weight: 600;
  font-family: var(--font-mono);
  display: flex;
  align-items: center;
  gap: 2px;
}

.change-arrow { font-size: 10px; }

.live-price.up, .live-change.up { color: var(--up-color); }
.live-price.down, .live-change.down { color: var(--down-color); }

.live-clock {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.clock-date {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.clock-time {
  font-size: 12px;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

/* 主区域 */
.main-area {
  flex: 1;
  display: flex;
  overflow: hidden;
  position: relative;
}

/* 加载遮罩 */
.loading-overlay {
  position: absolute;
  inset: 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: rgba(10, 14, 23, 0.75);
  backdrop-filter: blur(2px);
  color: var(--text-secondary);
  font-size: 14px;
}

.loading-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid var(--border);
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-fade-enter-active,
.loading-fade-leave-active {
  transition: opacity 0.2s ease;
}
.loading-fade-enter-from,
.loading-fade-leave-to {
  opacity: 0;
}

/* K线区域 */
.kline-zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.indicator-tabs {
  height: 32px;
  display: flex;
  align-items: center;
  gap: 0;
  padding: 0 12px;
  background: transparent;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.ind-tab {
  height: 32px;
  padding: 0 16px;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: 12px;
  font-family: var(--font-mono);
  cursor: pointer;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}

.ind-tab:hover {
  color: var(--text-primary);
  background: rgba(59, 130, 246, 0.04);
}

.ind-tab.active {
  color: var(--text-primary);
  border-bottom-color: var(--accent);
  background: rgba(59, 130, 246, 0.08);
}

.kline-chart {
  flex: 1;
  min-height: 0;
}

/* 左侧面板 */
.side-panel {
  display: flex;
  flex-direction: column;
  background: #141A22;
  border-right: 1px solid var(--border);
  box-shadow: 2px 0 8px rgba(0,0,0,0.3);
}

/* 拖拽分割条 */
.splitter {
  width: 4px;
  cursor: col-resize;
  background: var(--border);
  flex-shrink: 0;
  transition: background 0.15s;
}

.splitter:hover {
  background: var(--accent);
}

.panel-tabs {
  height: 40px;
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}

.panel-tab {
  flex: 1;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-secondary);
  font-size: 13px;
  cursor: pointer;
  transition: color 0.15s, background 0.15s, border-color 0.15s;
}

.panel-tab:hover {
  color: #C0C8D4;
  background: rgba(255,255,255,0.02);
}

.panel-tab.active {
  color: var(--text-primary);
  background: rgba(59, 130, 246, 0.08);
  border-bottom-color: var(--accent);
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding-bottom: 0;
}

.tab-content {
  height: 100%;
}

.fade-in {
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* AI 抽屉 */
.ai-drawer-trigger {
  position: fixed;
  left: 0;
  bottom: 0;
  width: 64px;
  height: 32px;
  background: var(--accent);
  border-radius: 0 4px 0 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  cursor: pointer;
  z-index: 200;
  transition: opacity 0.2s;
}

.ai-drawer-trigger:hover {
  opacity: 0.85;
}

.trigger-text {
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 2px;
}

.trigger-icon {
  color: #fff;
  font-size: 10px;
}

.ai-drawer {
  position: fixed;
  left: 64px;
  bottom: 0;
  width: 380px;
  height: 420px;
  background: var(--bg-panel);
  border: 1px solid var(--border);
  border-left: none;
  border-radius: 0 6px 0 0;
  z-index: 199;
  display: flex;
  flex-direction: column;
}

.drawer-slide-enter-active,
.drawer-slide-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}

.drawer-slide-enter-from,
.drawer-slide-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}
</style>