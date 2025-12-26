<!-- QnAView.vue - 智能问答界面 -->
<template>
  <div class="qna-container">
    <div class="qna-header">
      <h2>智能知识问答</h2>
      <p>基于您的知识库进行智能问答，支持多轮对话</p>
    </div>

    <div class="qna-content">
      <!-- 左侧：问答界面 -->
      <div class="chat-section">
        <div class="chat-container">
          <!-- 对话历史 -->
          <div class="chat-history" ref="chatHistory">
            <div 
              v-for="(message, index) in conversationHistory" 
              :key="index"
              :class="['message', message.type]">
              <div class="message-avatar">
                <el-avatar 
                  :size="32" 
                  :src="message.type === 'user' ? userAvatar : botAvatar"
                  :icon="message.type === 'user' ? User : Avatar" />
              </div>
              <div class="message-content">
                <div class="message-text">{{ message.content }}</div>
                <div v-if="message.confidence !== undefined" class="confidence">
                  置信度: {{ (message.confidence * 100).toFixed(1) }}%
                </div>
                <div v-if="message.sources && message.sources.length" class="sources">
                  来源: {{ message.sources.join('，') }}
                </div>
                <div class="message-time">{{ message.timestamp }}</div>
              </div>
            </div>
          </div>

          <!-- 输入区域 -->
          <div class="input-section">
            <div class="input-container">
              <el-input
                v-model="currentQuestion"
                type="textarea"
                :rows="3"
                placeholder="请输入您的问题..."
                :maxlength="500"
                show-word-limit
                @keydown.enter.exact.prevent="sendQuestion"
                :disabled="loading"
              />
              <div class="input-actions">
                <el-checkbox v-model="conversationMode" :disabled="loading">
                  多轮对话模式
                </el-checkbox>
                <div class="action-buttons">
                  <el-button 
                    @click="clearHistory" 
                    :disabled="loading || conversationHistory.length === 0">
                    清空对话
                  </el-button>
                  <el-button 
                    type="primary" 
                    @click="sendQuestion" 
                    :loading="loading"
                    :disabled="!currentQuestion.trim()">
                    {{ loading ? '思考中...' : '发送' }}
                  </el-button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧：相关信息 -->
      <div class="info-section">
        <!-- 知识库信息 -->
        <el-card class="kb-info-card">
          <template #header>
            <div class="card-header">
              <el-icon><Document /></el-icon>
              <span>知识库信息</span>
            </div>
          </template>
          <div v-if="kbInfo" class="kb-info">
            <div class="kb-item">
              <span class="label">名称:</span>
              <span class="value">{{ kbInfo.name }}</span>
            </div>
            <div class="kb-item">
              <span class="label">领域:</span>
              <span class="value">{{ kbInfo.domain }}</span>
            </div>
            <div class="kb-item">
              <span class="label">文档数:</span>
              <span class="value">{{ kbInfo.document_count }}</span>
            </div>
            <div class="kb-item">
              <span class="label">知识块:</span>
              <span class="value">{{ kbInfo.chunk_count }}</span>
            </div>
          </div>
          <div v-else class="no-kb">
            <el-empty description="暂无知识库信息" />
          </div>
        </el-card>

        <!-- 相关问题 -->
        <el-card class="related-questions-card" v-if="relatedQuestions.length > 0">
          <template #header>
            <div class="card-header">
              <el-icon><HelpFilled /></el-icon>
              <span>相关问题</span>
            </div>
          </template>
          <div class="questions-list">
            <div 
              v-for="(question, index) in relatedQuestions" 
              :key="index"
              class="question-item"
              @click="useRelatedQuestion(question)">
              <el-icon><ChatDotRound /></el-icon>
              <span class="question-text">{{ question }}</span>
            </div>
          </div>
        </el-card>

        <!-- 对话统计 -->
        <el-card class="stats-card">
          <template #header>
            <div class="card-header">
              <el-icon><DataAnalysis /></el-icon>
              <span>对话统计</span>
            </div>
          </template>
          <div class="stats">
            <div class="stat-item">
              <span class="label">对话轮数:</span>
              <span class="value">{{ conversationHistory.filter(m => m.type === 'user').length }}</span>
            </div>
            <div class="stat-item">
              <span class="label">平均置信度:</span>
              <span class="value">{{ averageConfidence }}%</span>
            </div>
            <div class="stat-item">
              <span class="label">多轮对话:</span>
              <span class="value">{{ conversationMode ? '启用' : '禁用' }}</span>
            </div>
          </div>
        </el-card>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-content">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>AI正在思考中...</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { 
  User, 
  Avatar, 
  Document, 
  HelpFilled, 
  ChatDotRound, 
  DataAnalysis, 
  Loading 
} from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/userStore'
import apiClient from '@/utils/axios'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

// 响应式数据
const currentQuestion = ref('')
const conversationHistory = ref<Array<{
  type: 'user' | 'bot'
  content: string
  timestamp: string
  confidence?: number
  sources?: string[]
}>>([])
const loading = ref(false)
const conversationMode = ref(true)
const relatedQuestions = ref<string[]>([])
const kbInfo = ref<any>(null)
const chatHistory = ref<HTMLElement>()

// 头像
const userAvatar = ref('')
const botAvatar = ref('')

// 计算属性
const averageConfidence = computed(() => {
  const botMessages = conversationHistory.value.filter(m => m.type === 'bot' && m.confidence)
  if (botMessages.length === 0) return 0
  const total = botMessages.reduce((sum, msg) => sum + (msg.confidence || 0), 0)
  return ((total / botMessages.length) * 100).toFixed(1)
})

// 方法
const formatTime = () => {
  return new Date().toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

const scrollToBottom = () => {
  nextTick(() => {
    if (chatHistory.value) {
      chatHistory.value.scrollTop = chatHistory.value.scrollHeight
    }
  })
}

const sendQuestion = async () => {
  if (!currentQuestion.value.trim() || loading.value) return

  const question = currentQuestion.value.trim()
  currentQuestion.value = ''

  // 添加到对话历史
  conversationHistory.value.push({
    type: 'user',
    content: question,
    timestamp: formatTime()
  })

  loading.value = true
  scrollToBottom()

  try {
    // 调用问答API
    const response = await apiClient.post('/api/qna/ask', {
      question: question,
      kb_id: userStore.kbId,
      user_id: userStore.userId,
      conversation_mode: conversationMode.value
    })

    // 添加AI回复到对话历史
    conversationHistory.value.push({
      type: 'bot',
      content: response.data.answer,
      timestamp: formatTime(),
      confidence: response.data.confidence,
      sources: response.data.sources
    })

    // 获取相关问题
    await getRelatedQuestions(question)

  } catch (error: any) {
    console.error('问答失败:', error)
    ElMessage.error(`问答失败: ${error.response?.data?.detail || error.message}`)
    
    conversationHistory.value.push({
      type: 'bot',
      content: '抱歉，回答问题时出现错误，请稍后重试。',
      timestamp: formatTime(),
      confidence: 0
    })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

const getRelatedQuestions = async (question: string) => {
  try {
    const response = await apiClient.post('/api/qna/related-questions', {
      question: question,
      kb_id: userStore.kbId
    })
    relatedQuestions.value = response.data.related_questions
  } catch (error) {
    console.error('获取相关问题失败:', error)
  }
}

const useRelatedQuestion = (question: string) => {
  currentQuestion.value = question
}

const clearHistory = async () => {
  try {
    await apiClient.delete(`/api/qna/conversation-history/${userStore.userId}/${userStore.kbId}`)
    conversationHistory.value = []
    relatedQuestions.value = []
    ElMessage.success('对话历史已清空')
  } catch (error) {
    console.error('清空历史失败:', error)
    ElMessage.error('清空历史失败')
  }
}

const loadConversationHistory = async () => {
  try {
    const response = await apiClient.get(`/api/qna/conversation-history/${userStore.userId}/${userStore.kbId}`)
    if (response.data.history) {
      // 解析历史对话（简化实现）
      const lines = response.data.history.split('\n').filter((line: string) => line.trim())
      for (let i = 0; i < lines.length; i += 2) {
        if (lines[i].startsWith('用户:')) {
          conversationHistory.value.push({
            type: 'user',
            content: lines[i].replace('用户:', '').trim(),
            timestamp: formatTime()
          })
        }
        if (i + 1 < lines.length && lines[i + 1].startsWith('助手:')) {
          conversationHistory.value.push({
            type: 'bot',
            content: lines[i + 1].replace('助手:', '').trim(),
            timestamp: formatTime()
          })
        }
      }
    }
  } catch (error) {
    console.error('加载对话历史失败:', error)
  }
}

const loadKnowledgeBaseInfo = async () => {
  try {
    const response = await apiClient.get(`/api/qna/knowledge-base-info/${userStore.kbId}`)
    kbInfo.value = response.data
  } catch (error) {
    console.error('加载知识库信息失败:', error)
  }
}

// 生命周期
onMounted(async () => {
  if (userStore.kbId) {
    await Promise.all([
      loadConversationHistory(),
      loadKnowledgeBaseInfo()
    ])
    scrollToBottom()
  } else {
    ElMessage.warning('请先上传文档创建知识库')
  }
})

// 监听知识库ID变化
watch(() => userStore.kbId, async (newKbId) => {
  if (newKbId) {
    await loadKnowledgeBaseInfo()
    await loadConversationHistory()
  }
})
</script>

<style scoped>
.qna-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

.qna-header {
  text-align: center;
  margin-bottom: 30px;
}

.qna-header h2 {
  font-size: 2.5rem;
  color: #1890ff;
  margin-bottom: 10px;
}

.qna-header p {
  font-size: 1.1rem;
  color: #666;
}

.qna-content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
  height: calc(100vh - 200px);
}

.chat-section {
  display: flex;
  flex-direction: column;
}

.chat-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  overflow: hidden;
}

.chat-history {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #fafafa;
}

.message {
  display: flex;
  margin-bottom: 20px;
  gap: 12px;
}

.message.user {
  flex-direction: row-reverse;
}

.message-avatar {
  flex-shrink: 0;
}

.message-content {
  max-width: 70%;
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.message.user .message-content {
  background: #1890ff;
  color: white;
}

.message-text {
  line-height: 1.5;
  word-wrap: break-word;
}

.confidence, .sources {
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: 4px;
}

.message-time {
  font-size: 0.7rem;
  opacity: 0.6;
  margin-top: 4px;
}

.input-section {
  border-top: 1px solid #e0e0e0;
  background: white;
}

.input-container {
  padding: 16px;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 12px;
}

.action-buttons {
  display: flex;
  gap: 8px;
}

.info-section {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.kb-info .kb-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 4px 0;
}

.kb-item .label {
  font-weight: 500;
  color: #666;
}

.kb-item .value {
  color: #333;
}

.questions-list {
  max-height: 200px;
  overflow-y: auto;
}

.question-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
  cursor: pointer;
  border-bottom: 1px solid #f0f0f0;
  transition: background-color 0.2s;
}

.question-item:hover {
  background-color: #f5f5f5;
}

.question-item:last-child {
  border-bottom: none;
}

.question-text {
  flex: 1;
  font-size: 0.9rem;
  line-height: 1.3;
}

.stats .stat-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  padding: 4px 0;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.loading-content {
  text-align: center;
}

.loading-icon {
  font-size: 2rem;
  color: #1890ff;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .qna-content {
    grid-template-columns: 1fr;
    height: auto;
  }
  
  .info-section {
    order: -1;
  }
  
  .message-content {
    max-width: 85%;
  }
}
</style>