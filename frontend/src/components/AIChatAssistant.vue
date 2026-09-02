<template>
  <div class="panel-card chat-panel">
    <div class="panel-header">
      <span class="panel-title">AI 智能助手</span>
      <button class="clear-btn" @click="onClear" title="清除对话">清除</button>
    </div>

    <div class="chat-messages" ref="messagesRef">
      <div v-if="messages.length === 0" class="chat-welcome">
        <div class="welcome-icon">🤖</div>
        <p>你好！我是金融数据分析助手</p>
        <p class="welcome-hint">可以问我股票行情、技术指标、财务数据等问题</p>
        <div class="quick-questions">
          <button class="quick-btn" @click="onQuickAsk('今日行情怎么样？')">📊 今日行情</button>
          <button class="quick-btn" @click="onQuickAsk('技术指标分析')">📈 技术分析</button>
          <button class="quick-btn" @click="onQuickAsk('财务健康度如何？')">💰 财务解读</button>
        </div>
      </div>

      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        class="chat-message"
        :class="msg.role"
      >
        <div class="message-avatar">
          {{ msg.role === 'user' ? '👤' : '🤖' }}
        </div>
        <div class="message-content" v-html="renderMarkdown(msg.content)"></div>
      </div>

      <div v-if="loading" class="chat-message assistant">
        <div class="message-avatar">🤖</div>
        <div class="message-content typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <div class="chat-input-area">
      <input
        v-model="inputText"
        type="text"
        placeholder="输入问题，如：今天涨了多少？"
        @keyup.enter="onSend"
        :disabled="loading"
        class="chat-input"
      />
      <button class="send-btn" @click="onSend" :disabled="loading || !inputText.trim()">
        发送
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import { aiChat, clearChatHistory } from '@/api'
import { useStockStore } from '@/stores/stock'

const store = useStockStore()
const messages = ref([])
const inputText = ref('')
const loading = ref(false)
const messagesRef = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

const onSend = async () => {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  await scrollToBottom()

  try {
    const result = await aiChat(
      store.sessionId,
      text,
      store.currentStock
    )
    messages.value.push({
      role: 'assistant',
      content: result.answer || '抱歉，未能获取到回答。',
    })
  } catch (e) {
    messages.value.push({
      role: 'assistant',
      content: '抱歉，AI服务暂时不可用，请稍后再试。',
    })
  } finally {
    loading.value = false
    await scrollToBottom()
  }
}

const onQuickAsk = (question) => {
  inputText.value = question
  onSend()
}

const onClear = async () => {
  messages.value = []
  try {
    await clearChatHistory(store.sessionId)
  } catch (e) {
    // ignore
  }
}

const renderMarkdown = (text) => {
  if (!text) return ''
  let html = text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n/g, '<br>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
  return html
}
</script>

<style scoped>
.panel-card {
  background: rgba(10, 25, 50, 0.8);
  border: 1px solid rgba(0, 150, 255, 0.15);
  border-radius: 8px;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.chat-panel {
  padding: 16px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(0, 150, 255, 0.1);
  flex-shrink: 0;
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: #00d4ff;
}

.clear-btn {
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(224, 230, 237, 0.5);
  padding: 2px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.clear-btn:hover {
  border-color: rgba(255, 77, 79, 0.5);
  color: #ff4d4f;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  margin-bottom: 12px;
  padding-right: 4px;
}

.chat-welcome {
  text-align: center;
  padding: 30px 10px;
}

.welcome-icon {
  font-size: 40px;
  margin-bottom: 12px;
}

.chat-welcome p {
  font-size: 14px;
  color: rgba(224, 230, 237, 0.7);
  margin-bottom: 6px;
}

.welcome-hint {
  font-size: 12px !important;
  color: rgba(224, 230, 237, 0.4) !important;
  margin-bottom: 16px !important;
}

.quick-questions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 12px;
}

.quick-btn {
  background: rgba(0, 150, 255, 0.08);
  border: 1px solid rgba(0, 150, 255, 0.2);
  color: #00d4ff;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: rgba(0, 150, 255, 0.15);
  border-color: rgba(0, 150, 255, 0.4);
}

.chat-message {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.chat-message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(0, 150, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  flex-shrink: 0;
}

.message-content {
  max-width: 85%;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}

.user .message-content {
  background: rgba(0, 150, 255, 0.15);
  border: 1px solid rgba(0, 150, 255, 0.2);
}

.assistant .message-content {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.message-content :deep(code) {
  background: rgba(0, 150, 255, 0.1);
  padding: 1px 4px;
  border-radius: 3px;
  font-size: 12px;
}

.message-content :deep(strong) {
  color: #00d4ff;
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 12px !important;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: rgba(0, 212, 255, 0.6);
  border-radius: 50%;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-4px); }
}

.chat-input-area {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.chat-input {
  flex: 1;
  height: 36px;
  padding: 0 12px;
  border: 1px solid rgba(0, 150, 255, 0.2);
  border-radius: 6px;
  background: rgba(10, 20, 40, 0.8);
  color: #e0e6ed;
  font-size: 13px;
  outline: none;
}

.chat-input:focus {
  border-color: rgba(0, 150, 255, 0.5);
}

.chat-input::placeholder {
  color: rgba(224, 230, 237, 0.3);
}

.send-btn {
  width: 56px;
  height: 36px;
  background: linear-gradient(135deg, #0090ff, #00d4ff);
  border: none;
  border-radius: 6px;
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition: opacity 0.2s;
}

.send-btn:hover {
  opacity: 0.9;
}

.send-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>