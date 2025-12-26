<template>
  <div class="interview-container">
    <h2>AI 模拟面试 - {{ sceneLabel }}</h2>

    <!-- 面试进度条 -->
    <div class="progress-section">
      <div class="progress-info">
        <span>第 {{ currentQuestion }} 题 / 共 {{ totalQuestions }} 题</span>
        <span class="progress-percentage">{{ progress }}%</span>
      </div>
      <el-progress :percentage="progress" :stroke-width="8" :color="progressColor" />
    </div>

    <div class="chat-box">
      <ChatMessage
        v-for="(msg, index) in messages"
        :key="index"
        :content="msg.content"
        :is-ai="msg.isAi"
      />
      <div v-if="loading" class="thinking">AI 正在思考...</div>
    </div>

    <div class="input-area">
      <el-input
        v-model="userInput"
        placeholder="请输入你的回答..."
        @keyup.enter="handleSubmit"
        :disabled="loading"
        clearable
      />
      <el-button
        type="primary"
        @click="handleSubmit"
        :disabled="!userInput.trim() || loading"
        style="margin-left: 10px"
      >
        发送
      </el-button>
    </div>

    <div class="action-buttons">
      <el-button @click="confirmEndInterview" type="danger" :disabled="loading">
        结束面试
      </el-button>
      <el-button @click="restartInterview" type="warning" :disabled="loading">
        重新开始
      </el-button>
      <el-button @click="goToReport" type="success" :disabled="!messages.length">
        查看成长报告
      </el-button>
    </div>

    <!-- 结束面试确认对话框 -->
    <el-dialog
      v-model="showEndDialog"
      title="确认结束面试"
      width="30%"
    >
      <span>确定要结束当前面试吗？</span>
      <template #footer>
        <el-button @click="showEndDialog = false">取消</el-button>
        <el-button type="primary" @click="endInterview">确认结束</el-button>
      </template>
    </el-dialog>


  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import { useInterview } from '@/composables/useInterview'
import ChatMessage from '@/components/ChatMessage.vue'
import { ElMessage } from 'element-plus'

const router = useRouter()
const userStore = useUserStore()
const { messages, loading, startInterview, sendAnswer, endInterview: endInterviewApi, clearMessages } = useInterview()
const userInput = ref('')
const showEndDialog = ref(false)

// 面试进度相关
const currentQuestion = ref(1)
const totalQuestions = ref(10) // 默认设置为10题，可根据实际情况调整
const progress = computed(() => {
  // 每两条消息算一个问题（AI问+用户答）
  const questionCount = Math.ceil(messages.value.length / 2)
  return Math.min(Math.round((questionCount / totalQuestions.value) * 100), 100)
})
const progressColor = computed(() => {
  if (progress.value < 30) return '#f56c6c'
  if (progress.value < 70) return '#e6a23c'
  return '#67c23a'
})

// 场景标签映射
const sceneLabel = {
  it: 'IT 技术面试',
  language: '小语种口语',
  cert: '职业考证'
}[userStore.sceneType]

// 自动滚动到聊天底部
const scrollToBottom = async () => {
  await nextTick()
  const chatBox = document.querySelector('.chat-box') as HTMLElement
  if (chatBox) {
    chatBox.scrollTop = chatBox.scrollHeight
  }
}

// 监听消息变化，自动滚动到底部
watch(messages, (_) => {
  scrollToBottom()
}, { deep: true })

// 提交回答
const handleSubmit = () => {
  if (!userStore.currentKbId) {
    ElMessage.error('请先上传资料！')
    router.push('/upload')
    return
  }
  
  if (!userInput.value.trim()) return
  
  sendAnswer(userInput.value, userStore.currentKbId, userStore.sceneType)
  userInput.value = ''
}





// 结束面试
const confirmEndInterview = () => {
  showEndDialog.value = true
}

const endInterview = async () => {
  showEndDialog.value = false
  await endInterviewApi()
  goToReport()
}

// 重新开始面试
const restartInterview = () => {
  clearMessages()
  if (userStore.currentKbId) {
    startInterview(userStore.currentKbId, userStore.sceneType)
  }
}

// 跳转到报告页面
const goToReport = () => {
  router.push('/report')
}

// 组件挂载时开始面试
onMounted(() => {
  if (userStore.currentKbId) {
    // 直接开始新的对话，不检查草稿
    startInterview(userStore.currentKbId, userStore.sceneType)
  } else {
    ElMessage.error('请先上传资料！')
    router.push('/upload')
  }
})
</script>

<style scoped>
.interview-container {
  max-width: 800px;
  margin: 20px auto;
  padding: 0 20px;
}

.chat-box {
  height: 500px;
  overflow-y: auto;
  border: 1px solid #ddd;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
  display: flex;
  flex-direction: column;
}

.thinking {
  color: #999;
  font-style: italic;
  padding: 8px 0;
  align-self: flex-start;
}

.input-area {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.progress-section {
  margin: 20px 0;
  background: #fafafa;
  padding: 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.progress-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
}

.progress-percentage {
  font-weight: bold;
  color: #1890ff;
}

.action-buttons {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .interview-container {
    padding: 0 10px;
    margin: 10px auto;
    max-width: 100%;
  }

  .chat-box {
    height: 400px;
    margin-bottom: 10px;
  }

  .input-area {
    flex-direction: column;
    margin-bottom: 10px;
  }

  .input-area .el-button {
    margin-left: 0;
    margin-top: 10px;
    width: 100%;
  }

  .action-buttons {
    flex-direction: column;
  }

  .action-buttons .el-button {
    width: 100%;
  }

  .progress-section {
    padding: 12px;
  }

  .progress-info {
    font-size: 12px;
  }

  .draft-info {
    font-size: 14px;
  }

  .draft-hint {
    color: #666;
    font-size: 12px;
    margin-top: 10px;
  }
}
</style>