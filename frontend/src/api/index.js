import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 30000,
})

http.interceptors.response.use(
  (response) => {
    const data = response.data
    if (data.code === 0) {
      return data.data
    }
    return Promise.reject(new Error(data.message || '请求失败'))
  },
  (error) => {
    return Promise.reject(error)
  }
)

export function getStockList(keyword) {
  return http.get('/stock/list', { params: { keyword } })
}

export function getStockOverview(tsCode) {
  return http.get(`/stock/overview/${tsCode}`)
}

export function getKlineData(tsCode, days = 120) {
  return http.get(`/stock/kline/${tsCode}`, { params: { days } })
}

export function getTechnicalRadar(tsCode) {
  return http.get(`/stock/technical/${tsCode}`)
}

export function getCapitalFlow(tsCode, days = 30) {
  return http.get(`/stock/capital_flow/${tsCode}`, { params: { days } })
}

export function getFinancialHealth(tsCode) {
  return http.get(`/stock/financial/${tsCode}`)
}

export function getIndustryCompare() {
  return http.get('/stock/industry_compare')
}

export function getMarketAnalysis() {
  return http.get('/stock/market_analysis')
}

export function getDashboardData(tsCode) {
  return http.get(`/dashboard/data/${tsCode}`)
}

export function getDailyIndicators(tsCode, days = 60) {
  return http.get(`/indicator/daily/${tsCode}`, { params: { days } })
}

export function getSignal(tsCode) {
  return http.get(`/indicator/signal/${tsCode}`)
}

export function aiChat(sessionId, question, stockCode) {
  return http.post('/ai/chat', { session_id: sessionId, question, stock_code: stockCode })
}

export function getChatHistory(sessionId) {
  return http.get(`/ai/history/${sessionId}`)
}

export function clearChatHistory(sessionId) {
  return http.delete(`/ai/history/${sessionId}`)
}