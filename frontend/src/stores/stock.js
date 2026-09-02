import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api'

export const useStockStore = defineStore('stock', () => {
  const currentStock = ref('600000.SH')
  const stockName = ref('浦发银行')
  const stockList = ref([])
  const dashboardData = ref(null)
  const loading = ref(false)
  const sessionId = ref('session_' + Date.now())

  const fetchStockList = async (keyword) => {
    try {
      const data = await api.getStockList(keyword)
      stockList.value = data || []
    } catch (e) {
      console.error('获取股票列表失败:', e)
    }
  }

  const fetchDashboardData = async (tsCode) => {
    loading.value = true
    try {
      const data = await api.getDashboardData(tsCode)
      dashboardData.value = data
      if (data?.stock_overview?.name) {
        stockName.value = data.stock_overview.name
      }
    } catch (e) {
      console.error('获取大屏数据失败:', e)
    } finally {
      loading.value = false
    }
  }

  const selectStock = async (tsCode) => {
    currentStock.value = tsCode
    await fetchDashboardData(tsCode)
  }

  return {
    currentStock,
    stockName,
    stockList,
    dashboardData,
    loading,
    sessionId,
    fetchStockList,
    fetchDashboardData,
    selectStock,
  }
})