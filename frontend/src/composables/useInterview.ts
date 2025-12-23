// composables/useInterview.ts
import { ref } from 'vue'
import apiClient from '@/utils/axios'

// 定义消息类型
interface Message {
  content: string
  isAi: boolean
}

export function useInterview() {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const sceneType = ref('it')

  /**
   * 开始面试
   * @param kbId 知识库ID
   * @param sceneType 场景类型
   */
  const startInterview = async (kbId: number, sceneType: string) => {
    messages.value = []
    loading.value = true

    try {
      // 发送初始问题请求
      const res = await apiClient.post('/api/interview/start', {
        kb_id: kbId,
        scene_type: sceneType
      })

      // 添加AI的初始问题到消息列表
      messages.value.push({
        content: res.data.initial_response || '你好！让我们开始今天的面试吧。',
        isAi: true
      })
    } catch (error) {
      console.error('开始面试失败:', error)
      messages.value.push({
        content: '抱歉，无法开始面试。请稍后重试。',
        isAi: true
      })
    } finally {
      loading.value = false
    }
  }

  /**
   * 发送回答
   * @param answer 用户回答
   * @param kbId 知识库ID
   * @param sceneType 场景类型
   */
  const sendAnswer = async (answer: string, kbId: number, sceneType: string) => {
    if (!answer.trim()) return

    // 添加用户回答到消息列表
    messages.value.push({ content: answer, isAi: false })
    loading.value = true

    try {
      // 使用 SSE 流式接收 AI 回复
      const userId = localStorage.getItem('userId') || `guest_${Date.now()}`
      const lastQuestion = messages.value[messages.value.length - 2]?.content || ''

      const eventSource = new EventSource(
        `http://localhost:8000/api/interview/stream?user_id=${encodeURIComponent(userId)}&kb_id=${kbId}&scene_type=${sceneType}&user_answer=${encodeURIComponent(answer)}&last_question=${encodeURIComponent(lastQuestion)}`
      )

      // 添加一个临时的AI消息，用于实时更新
      let aiResponse = ''
      const aiMsg = { content: '', isAi: true }
      messages.value.push(aiMsg)

      eventSource.onopen = () => {
        console.log('SSE连接已建立')
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          if (data.type === 'token') {
            // 接收到流式token，更新AI回复
            aiResponse += data.token
            aiMsg.content = aiResponse
          } else if (data.type === 'end') {
            // 流式回复结束
            eventSource.close()
            loading.value = false
            // 可在此保存记录、更新分数等
          }
        } catch (error) {
          console.error('解析SSE数据失败:', error)
        }
      }

      eventSource.onerror = (error) => {
        console.error('SSE连接错误:', error)
        eventSource.close()
        loading.value = false
        // 如果AI消息为空，替换为错误提示
        if (!aiMsg.content.trim()) {
          const index = messages.value.indexOf(aiMsg)
          if (index > -1) {
            messages.value[index] = {
              content: '抱歉，系统出错了。请稍后重试。',
              isAi: true
            }
          }
        }
      }

    } catch (error) {
      console.error('发送回答失败:', error)
      messages.value.push({
        content: '抱歉，系统出错了。请稍后重试。',
        isAi: true
      })
      loading.value = false
    }
  }

  /**
   * 结束面试
   */
  const endInterview = async () => {
    loading.value = true

    try {
      // 发送结束面试请求
      const res = await apiClient.post('/api/interview/end')

      // 添加结束消息
      messages.value.push({
        content: res.data.closing_response || '面试结束。感谢你的参与！',
        isAi: true
      })

      return res.data
    } catch (error) {
      console.error('结束面试失败:', error)
      messages.value.push({
        content: '面试结束。感谢你的参与！',
        isAi: true
      })
      return null
    } finally {
      loading.value = false
    }
  }

  /**
   * 清除消息历史
   */
  const clearMessages = () => {
    messages.value = []
  }

  /**
   * 保存面试草稿
   * @returns 是否保存成功
   */
  const saveDraft = () => {
    try {
      const draft = {
        messages: messages.value,
        sceneType: sceneType || 'it',
        timestamp: Date.now()
      }
      localStorage.setItem('interviewDraft', JSON.stringify(draft))
      return true
    } catch (error) {
      console.error('保存草稿失败:', error)
      return false
    }
  }

  /**
   * 加载面试草稿
   * @returns 是否加载成功
   */
  const loadDraft = () => {
    try {
      const draft = localStorage.getItem('interviewDraft')
      if (draft) {
        const parsedDraft = JSON.parse(draft)
        messages.value = parsedDraft.messages || []
        return true
      }
      return false
    } catch (error) {
      console.error('加载草稿失败:', error)
      return false
    }
  }

  /**
   * 删除面试草稿
   * @returns 是否删除成功
   */
  const deleteDraft = () => {
    try {
      localStorage.removeItem('interviewDraft')
      return true
    } catch (error) {
      console.error('删除草稿失败:', error)
      return false
    }
  }

  return {
    messages,
    loading,
    startInterview,
    sendAnswer,
    endInterview,
    clearMessages,
    saveDraft,
    loadDraft,
    deleteDraft
  }
}
