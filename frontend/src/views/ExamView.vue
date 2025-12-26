<!-- ExamView.vue - 考试模拟题系统界面 -->
<template>
  <div class="exam-container">
    <!-- 考试类型选择 -->
    <div v-if="currentMode === 'select'" class="exam-selection">
      <div class="selection-header">
        <h2>考试模拟题系统</h2>
        <p>选择考试类型和模式，开始您的模拟考试</p>
      </div>

      <div class="exam-types">
        <el-card 
          v-for="(exam, type) in examTypes" 
          :key="type"
          class="exam-card"
          @click="selectExamType(type)">
          <div class="exam-card-content">
            <h3>{{ exam.name }}</h3>
            <p>{{ exam.description }}</p>
            <div class="question-types">
              <span v-for="qType in exam.question_types" :key="qType" class="question-tag">
                {{ qType }}
              </span>
            </div>
          </div>
        </el-card>
      </div>

      <div class="mode-selection">
        <h3>选择考试模式</h3>
        <div class="mode-cards">
          <el-card class="mode-card" @click="selectMode('simulation')">
            <div class="mode-icon">📝</div>
            <h4>模拟考试</h4>
            <p>完整模拟真实考试环境，包含时间限制和完整试题集</p>
          </el-card>
          
          <el-card class="mode-card" @click="selectMode('practice')">
            <div class="mode-icon">🔍</div>
            <h4>练习模式</h4>
            <p>逐题练习，即时反馈，适合重点突破和知识点巩固</p>
          </el-card>
        </div>
      </div>
    </div>

    <!-- 模拟考试界面 -->
    <div v-else-if="currentMode === 'simulation'" class="exam-simulation">
      <div class="exam-header">
        <div class="exam-info">
          <h2>{{ currentExamInfo?.exam_name }}</h2>
          <p>主题：{{ currentExamInfo?.topic }}</p>
        </div>
        <div class="exam-controls">
          <el-button @click="exitExam" type="warning" size="small">
            退出考试
          </el-button>
          <div class="timer" :class="{ warning: timeLeft < 300 }">
            {{ formatTime(timeLeft) }}
          </div>
        </div>
      </div>

      <div class="exam-content">
        <!-- 试题导航 -->
        <div class="question-nav">
          <div 
            v-for="(_, index) in currentExamInfo?.questions" 
            :key="index"
            :class="['nav-item', { 
              'current': currentQuestionIndex === index,
              'answered': userAnswers[Number(index) + 1]
            }]"
            @click="goToQuestion(Number(index))">
            {{ Number(index) + 1 }}
          </div>
        </div>

        <!-- 试题内容 -->
        <div class="question-content" v-if="currentQuestion">
          <div class="question-header">
            <h3>第 {{ currentQuestionIndex + 1 }} 题</h3>
            <span class="question-type">{{ currentQuestion.question_type }}</span>
            <span class="difficulty">难度：{{ currentQuestion.difficulty }}</span>
          </div>

          <div class="question-text">
            {{ currentQuestion.question }}
          </div>

          <!-- 选择题选项 -->
          <div v-if="currentQuestion.options && currentQuestion.options.length" class="options">
            <div 
              v-for="(option, optIndex) in currentQuestion.options" 
              :key="optIndex"
              :class="['option', { 'selected': isOptionSelected(Number(optIndex)) }]"
              @click="selectOption(Number(optIndex))">
              <span class="option-label">{{ String.fromCharCode(65 + Number(optIndex)) }}</span>
              <span class="option-text">{{ option }}</span>
            </div>
          </div>

          <!-- 主观题答案输入 -->
          <div v-else class="subjective-answer">
            <el-input
              v-model="subjectiveAnswer"
              type="textarea"
              :rows="6"
              placeholder="请输入您的答案..."
              :maxlength="1000"
              show-word-limit
            />
          </div>

          <!-- 答题控制 -->
          <div class="answer-controls">
            <el-button 
              @click="previousQuestion" 
              :disabled="currentQuestionIndex === 0">
              上一题
            </el-button>
            <el-button 
              @click="nextQuestion" 
              type="primary"
              :disabled="currentQuestionIndex === (currentExamInfo?.questions?.length || 0) - 1">
              下一题
            </el-button>
            <el-button 
              v-if="currentQuestionIndex === (currentExamInfo?.questions?.length || 0) - 1"
              @click="submitExam" 
              type="success"
              :loading="submitting">
              {{ submitting ? '提交中...' : '提交试卷' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 练习模式界面 -->
    <div v-else-if="currentMode === 'practice'" class="practice-mode">
      <div class="practice-header">
        <h2>练习模式 - {{ currentExamTypeName }}</h2>
        <p>主题：{{ practiceTopic }}</p>
        <div class="practice-progress">
          <span>进度：{{ currentPracticeIndex + 1 }} / {{ practiceQuestions.length }}</span>
          <el-progress 
            :percentage="((currentPracticeIndex + 1) / practiceQuestions.length) * 100" 
            :stroke-width="8" 
            style="width: 200px;" />
        </div>
      </div>

      <div class="practice-content" v-if="currentPracticeQuestion">
        <div class="question-section">
          <div class="question-text">
            {{ currentPracticeQuestion.question }}
          </div>

          <!-- 选择题选项 -->
          <div v-if="currentPracticeQuestion.options && currentPracticeQuestion.options.length" class="options">
            <div 
              v-for="(option, optIndex) in currentPracticeQuestion.options" 
              :key="optIndex"
              :class="['option', { 'selected': practiceAnswer === String.fromCharCode(65 + Number(optIndex)) }]"
              @click="practiceAnswer = String.fromCharCode(65 + Number(optIndex))">
              <span class="option-label">{{ String.fromCharCode(65 + Number(optIndex)) }}</span>
              <span class="option-text">{{ option }}</span>
            </div>
          </div>

          <!-- 主观题答案输入 -->
          <div v-else class="subjective-answer">
            <el-input
              v-model="practiceAnswer"
              type="textarea"
              :rows="6"
              placeholder="请输入您的答案..."
              :maxlength="1000"
              show-word-limit
            />
          </div>
        </div>

        <!-- 答案提交和反馈 -->
        <div class="practice-controls">
          <el-button 
            @click="submitPracticeAnswer" 
            type="primary"
            :loading="checkingAnswer">
            {{ checkingAnswer ? '检查中...' : '提交答案' }}
          </el-button>
          
          <div v-if="practiceFeedback" class="feedback-section">
            <el-divider />
            <h4>答案反馈</h4>
            <div class="correct-answer">
              <strong>正确答案：</strong>{{ practiceCorrectAnswer }}
            </div>
            <div class="explanation">
              <strong>解析：</strong>{{ practiceExplanation }}
            </div>
            <div class="score">
              <strong>得分：</strong>{{ practiceScore }}
            </div>
            
            <el-button @click="nextPracticeQuestion" type="success">
              下一题
            </el-button>
          </div>
        </div>
      </div>

      <!-- 练习完成 -->
      <div v-else-if="practiceCompleted" class="practice-completed">
        <div class="completion-card">
          <h3>🎉 练习完成！</h3>
          <div class="score-summary">
            <p>总题数：{{ practiceQuestions.length }}</p>
            <p>正确题数：{{ practiceCorrectCount }}</p>
            <p>准确率：{{ practiceAccuracy }}%</p>
            <p>等级：{{ practiceGrade }}</p>
          </div>
          <div class="completion-actions">
            <el-button @click="restartPractice" type="primary">重新练习</el-button>
            <el-button @click="backToSelection">返回选择</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- 考试结果界面 -->
    <div v-else-if="currentMode === 'result'" class="exam-result">
      <div class="result-card">
        <h2>考试结果</h2>
        
        <div class="result-summary">
          <div class="score-display">
            <div class="total-score">{{ examResult?.total_score }} / {{ examResult?.max_score }}</div>
            <div class="accuracy">准确率：{{ examResult?.accuracy }}%</div>
            <div class="grade">等级：{{ examResult?.grade }}</div>
          </div>
          
          <div class="result-details">
            <p>总题数：{{ examResult?.total_questions }}</p>
            <p>正确题数：{{ examResult?.correct_count }}</p>
            <p>错误题数：{{ examResult?.total_questions - examResult?.correct_count }}</p>
          </div>
        </div>

        <div class="detailed-results">
          <h3>详细结果</h3>
          <div 
            v-for="result in examResult?.detailed_results" 
            :key="result.question_id"
            class="result-item">
            <div class="question-info">
              <span class="question-id">第 {{ result.question_id }} 题</span>
              <span :class="['score-badge', { 'correct': result.is_correct, 'wrong': !result.is_correct }]">
                {{ result.score }}分
              </span>
            </div>
            <div class="question-text">{{ result.question }}</div>
            <div class="answer-comparison">
              <div><strong>您的答案：</strong>{{ result.user_answer }}</div>
              <div><strong>正确答案：</strong>{{ result.correct_answer }}</div>
              <div v-if="result.explanation"><strong>解析：</strong>{{ result.explanation }}</div>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <el-button @click="backToSelection" type="primary">返回选择</el-button>
          <el-button @click="reviewWrongAnswers">查看错题</el-button>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-overlay">
      <div class="loading-content">
        <el-icon class="loading-icon"><Loading /></el-icon>
        <p>{{ loadingText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loading } from '@element-plus/icons-vue'
import apiClient from '@/utils/axios'

// 响应式数据
const currentMode = ref<'select' | 'simulation' | 'practice' | 'result'>('select')
const examTypes = ref<any>({})
const currentExamType = ref('')
const currentExamInfo = ref<any>(null)
const currentQuestionIndex = ref(0)
const userAnswers = ref<Record<number, string>>({})
const subjectiveAnswer = ref('')
const timeLeft = ref(0)
const timer = ref<any>(null)
const submitting = ref(false)

// 练习模式相关
const practiceQuestions = ref<any[]>([])
const currentPracticeIndex = ref(0)
const practiceAnswer = ref('')
const practiceFeedback = ref('')
const practiceCorrectAnswer = ref('')
const practiceExplanation = ref('')
const practiceScore = ref(0)
const practiceCorrectCount = ref(0)
const practiceCompleted = ref(false)
const checkingAnswer = ref(false)

// 考试结果
const examResult = ref<any>(null)

// 加载状态
const loading = ref(false)
const loadingText = ref('')

// 计算属性
const currentQuestion = computed(() => {
  return currentExamInfo.value?.questions?.[currentQuestionIndex.value]
})

const currentPracticeQuestion = computed(() => {
  return practiceQuestions.value[currentPracticeIndex.value]
})

const practiceAccuracy = computed(() => {
  if (practiceQuestions.value.length === 0) return '0'
  return ((practiceCorrectCount.value / practiceQuestions.value.length) * 100).toFixed(1)
})

const practiceGrade = computed(() => {
  const accuracy = parseFloat(practiceAccuracy.value)
  if (accuracy >= 90) return '优秀'
  if (accuracy >= 80) return '良好'
  if (accuracy >= 70) return '中等'
  if (accuracy >= 60) return '及格'
  return '不及格'
})

const currentExamTypeName = computed(() => {
  return examTypes.value[currentExamType.value]?.name || ''
})

const practiceTopic = ref('技术面试准备')

// 方法
const loadExamTypes = async () => {
  try {
    const response = await apiClient.get('/api/exam/types')
    examTypes.value = response.data.exam_types
  } catch (error) {
    console.error('加载考试类型失败:', error)
    ElMessage.error('加载考试类型失败')
  }
}

const selectExamType = (type: string | number) => {
  currentExamType.value = String(type)
}

const selectMode = (mode: 'simulation' | 'practice') => {
  if (!currentExamType.value) {
    ElMessage.warning('请先选择考试类型')
    return
  }
  
  currentMode.value = mode
  
  if (mode === 'simulation') {
    startSimulationExam()
  } else {
    startPracticeMode()
  }
}

const startSimulationExam = async () => {
  try {
    loading.value = true
    loadingText.value = '正在生成模拟考试...'
    
    const response = await apiClient.post('/api/exam/simulate-exam', {
      exam_type: currentExamType.value,
      topic: '技术面试准备',
      question_count: 20,
      time_limit: 120
    })
    
    currentExamInfo.value = response.data.exam_info
    timeLeft.value = currentExamInfo.value.time_limit * 60 // 转换为秒
    
    // 开始计时器
    startTimer()
    
    ElMessage.success('模拟考试开始！')
  } catch (error: any) {
    console.error('启动模拟考试失败:', error)
    ElMessage.error(`启动失败: ${error.response?.data?.detail || error.message}`)
    backToSelection()
  } finally {
    loading.value = false
  }
}

const startPracticeMode = async () => {
  try {
    loading.value = true
    loadingText.value = '正在生成练习题目...'
    
    const response = await apiClient.post('/api/exam/practice-mode', {
      exam_type: currentExamType.value,
      topic: '技术面试准备',
      question_count: 10
    })
    
    practiceQuestions.value = response.data.questions || []
    currentPracticeIndex.value = 0
    practiceAnswer.value = ''
    practiceFeedback.value = ''
    practiceCompleted.value = false
    practiceCorrectCount.value = 0
    
    ElMessage.success('练习模式开始！')
  } catch (error: any) {
    console.error('启动练习模式失败:', error)
    ElMessage.error(`启动失败: ${error.response?.data?.detail || error.message}`)
    backToSelection()
  } finally {
    loading.value = false
  }
}

const startTimer = () => {
  timer.value = setInterval(() => {
    if (timeLeft.value > 0) {
      timeLeft.value--
    } else {
      clearInterval(timer.value)
      autoSubmitExam()
    }
  }, 1000)
}

const formatTime = (seconds: number) => {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const isOptionSelected = (optIndex: number) => {
  const currentAnswer = userAnswers.value[currentQuestionIndex.value + 1]
  return currentAnswer === String.fromCharCode(65 + optIndex)
}

const selectOption = (optIndex: number) => {
  userAnswers.value[currentQuestionIndex.value + 1] = String.fromCharCode(65 + optIndex)
  subjectiveAnswer.value = ''
}

const previousQuestion = () => {
  if (currentQuestionIndex.value > 0) {
    saveCurrentAnswer()
    currentQuestionIndex.value--
    loadCurrentAnswer()
  }
}

const nextQuestion = () => {
  if (currentQuestionIndex.value < (currentExamInfo.value?.questions?.length || 0) - 1) {
    saveCurrentAnswer()
    currentQuestionIndex.value++
    loadCurrentAnswer()
  }
}

const goToQuestion = (index: number) => {
  saveCurrentAnswer()
  currentQuestionIndex.value = index
  loadCurrentAnswer()
}

const saveCurrentAnswer = () => {
  if (currentQuestion.value?.options?.length) {
    // 选择题答案已通过selectOption保存
  } else {
    userAnswers.value[currentQuestionIndex.value + 1] = subjectiveAnswer.value
  }
  subjectiveAnswer.value = ''
}

const loadCurrentAnswer = () => {
  const answer = userAnswers.value[currentQuestionIndex.value + 1]
  if (currentQuestion.value?.options?.length) {
    subjectiveAnswer.value = ''
  } else {
    subjectiveAnswer.value = answer || ''
  }
}

const submitExam = async () => {
  try {
    submitting.value = true
    
    // 确保保存当前答案
    saveCurrentAnswer()
    
    const response = await apiClient.post('/api/exam/submit-exam', {
      exam_id: currentExamInfo.value.exam_id,
      answers: JSON.stringify(userAnswers.value)
    })
    
    examResult.value = response.data.score_report
    currentMode.value = 'result'
    
    // 清理计时器
    if (timer.value) {
      clearInterval(timer.value)
    }
    
    ElMessage.success('考试提交成功！')
  } catch (error: any) {
    console.error('提交考试失败:', error)
    ElMessage.error(`提交失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    submitting.value = false
  }
}

const autoSubmitExam = async () => {
  await ElMessageBox.confirm('考试时间已到，系统将自动提交试卷', '时间到', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
  
  await submitExam()
}

const submitPracticeAnswer = async () => {
  if (!practiceAnswer.value.trim()) {
    ElMessage.warning('请输入答案')
    return
  }
  
  try {
    checkingAnswer.value = true
    
    // 简化实现：直接显示正确答案和解析
    practiceCorrectAnswer.value = currentPracticeQuestion.value.answer
    practiceExplanation.value = currentPracticeQuestion.value.explanation
    
    // 简单评分
    const isCorrect = practiceAnswer.value.toLowerCase().includes(practiceCorrectAnswer.value.toLowerCase())
    practiceScore.value = isCorrect ? 10 : 0
    
    if (isCorrect) {
      practiceCorrectCount.value++
    }
    
    practiceFeedback.value = isCorrect ? '回答正确！' : '回答有待改进。'
    
  } catch (error: any) {
    console.error('提交答案失败:', error)
    ElMessage.error(`提交失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    checkingAnswer.value = false
  }
}

const nextPracticeQuestion = () => {
  if (currentPracticeIndex.value < practiceQuestions.value.length - 1) {
    currentPracticeIndex.value++
    practiceAnswer.value = ''
    practiceFeedback.value = ''
  } else {
    practiceCompleted.value = true
  }
}

const restartPractice = () => {
  currentPracticeIndex.value = 0
  practiceAnswer.value = ''
  practiceFeedback.value = ''
  practiceCompleted.value = false
  practiceCorrectCount.value = 0
}

const exitExam = async () => {
  try {
    await ElMessageBox.confirm('确定要退出考试吗？未完成的题目将无法保存。', '退出考试', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    if (timer.value) {
      clearInterval(timer.value)
    }
    backToSelection()
  } catch {
    // 用户取消
  }
}

const backToSelection = () => {
  currentMode.value = 'select'
  currentExamInfo.value = null
  userAnswers.value = {}
  subjectiveAnswer.value = ''
  practiceQuestions.value = []
  examResult.value = null
}

const reviewWrongAnswers = () => {
  // 实现错题回顾功能
  ElMessage.info('错题回顾功能开发中...')
}

// 生命周期
onMounted(() => {
  loadExamTypes()
})
</script>

<style scoped>
.exam-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
}

/* 选择界面样式 */
.exam-selection {
  text-align: center;
}

.selection-header h2 {
  font-size: 2.5rem;
  color: #1890ff;
  margin-bottom: 10px;
}

.selection-header p {
  font-size: 1.1rem;
  color: #666;
  margin-bottom: 30px;
}

.exam-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.exam-card {
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid #e8e8e8;
}

.exam-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #1890ff;
}

.exam-card-content h3 {
  color: #333;
  margin-bottom: 10px;
}

.exam-card-content p {
  color: #666;
  margin-bottom: 15px;
}

.question-types {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.question-tag {
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #666;
}

.mode-selection h3 {
  margin-bottom: 20px;
  color: #333;
}

.mode-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  max-width: 600px;
  margin: 0 auto;
}

.mode-card {
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
  border: 2px solid #e8e8e8;
}

.mode-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  border-color: #1890ff;
}

.mode-icon {
  font-size: 3rem;
  margin-bottom: 10px;
}

.mode-card h4 {
  color: #333;
  margin-bottom: 10px;
}

.mode-card p {
  color: #666;
  font-size: 0.9rem;
}

/* 模拟考试样式 */
.exam-simulation {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 40px);
}

.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.exam-info h2 {
  color: #333;
  margin-bottom: 5px;
}

.exam-info p {
  color: #666;
}

.exam-controls {
  display: flex;
  align-items: center;
  gap: 20px;
}

.timer {
  font-size: 1.5rem;
  font-weight: bold;
  color: #52c41a;
}

.timer.warning {
  color: #faad14;
}

.timer.danger {
  color: #f5222d;
}

.exam-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.question-nav {
  width: 200px;
  background: #fafafa;
  padding: 20px;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(40px, 1fr));
  gap: 10px;
}

.nav-item {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-item:hover {
  border-color: #1890ff;
}

.nav-item.current {
  background: #1890ff;
  color: white;
  border-color: #1890ff;
}

.nav-item.answered {
  background: #52c41a;
  color: white;
  border-color: #52c41a;
}

.question-content {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
}

.question-header h3 {
  color: #333;
  margin: 0;
}

.question-type, .difficulty {
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  color: #666;
}

.question-text {
  font-size: 1.1rem;
  line-height: 1.6;
  margin-bottom: 30px;
  color: #333;
}

.options {
  margin-bottom: 30px;
}

.option {
  display: flex;
  align-items: flex-start;
  padding: 15px;
  margin-bottom: 10px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.option:hover {
  border-color: #1890ff;
}

.option.selected {
  background: #e6f7ff;
  border-color: #1890ff;
}

.option-label {
  font-weight: bold;
  margin-right: 10px;
  min-width: 20px;
}

.option-text {
  flex: 1;
  line-height: 1.5;
}

.subjective-answer {
  margin-bottom: 30px;
}

.answer-controls {
  display: flex;
  gap: 10px;
  justify-content: center;
}

/* 练习模式样式 */
.practice-mode {
  max-width: 800px;
  margin: 0 auto;
}

.practice-header {
  text-align: center;
  margin-bottom: 30px;
}

.practice-header h2 {
  color: #333;
  margin-bottom: 10px;
}

.practice-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
  margin-top: 15px;
}

.practice-content {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.question-section {
  margin-bottom: 30px;
}

.feedback-section {
  margin-top: 30px;
}

.correct-answer, .explanation, .score {
  margin-bottom: 15px;
  padding: 10px;
  background: #f6ffed;
  border-left: 4px solid #52c41a;
}

.practice-completed {
  text-align: center;
  padding: 40px;
}

.completion-card {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.score-summary {
  margin: 20px 0;
  font-size: 1.1rem;
}

.completion-actions {
  margin-top: 20px;
}

/* 考试结果样式 */
.exam-result {
  max-width: 800px;
  margin: 0 auto;
}

.result-card {
  background: white;
  padding: 30px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.result-summary {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px;
}

.total-score {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 10px;
}

.accuracy, .grade {
  font-size: 1.2rem;
  margin-bottom: 5px;
}

.result-details {
  margin-top: 15px;
}

.detailed-results {
  margin-top: 30px;
}

.result-item {
  padding: 15px;
  margin-bottom: 15px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
}

.question-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.score-badge {
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: bold;
}

.score-badge.correct {
  background: #f6ffed;
  color: #52c41a;
}

.score-badge.wrong {
  background: #fff2f0;
  color: #f5222d;
}

.answer-comparison {
  font-size: 0.9rem;
  color: #666;
}

.result-actions {
  text-align: center;
  margin-top: 30px;
}

/* 加载状态 */
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
  .exam-types {
    grid-template-columns: 1fr;
  }
  
  .mode-cards {
    grid-template-columns: 1fr;
  }
  
  .exam-content {
    flex-direction: column;
  }
  
  .question-nav {
    width: 100%;
    order: 2;
    max-height: 150px;
  }
  
  .question-content {
    order: 1;
  }
  
  .exam-header {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }
}
</style>