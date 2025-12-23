<template>
  <div class="report-container">
    <h2>你的成长报告</h2>
    
    <el-skeleton :loading="loading" animated>
      <template #template>
        <div class="report-skeleton">
          <el-skeleton-item variant="h3" style="width: 50%" />
          <el-skeleton-item variant="p" style="width: 100%" />
          <el-skeleton-item variant="p" style="width: 100%" />
          <el-skeleton-item variant="p" style="width: 80%" />
        </div>
      </template>
      
      <template v-if="report">
        <el-card>
          <div class="report-header">
            <div class="report-title">
              <h3>{{ report.title || 'AI面试成长报告' }}</h3>
              <div class="report-info">
                <span>生成时间: {{ formatDate(report.generated_at) }}</span>
                <span>场景类型: {{ sceneLabel }}</span>
              </div>
            </div>
            <div class="report-actions">
              <el-button type="primary" @click="printReport">
                <el-icon><printer /></el-icon>
                打印报告
              </el-button>
              <el-button type="success" @click="downloadReport">
                <el-icon><download /></el-icon>
                下载报告
              </el-button>
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 20px;">
          <h3>综合评分</h3>
          <div class="score-section">
            <div class="score-circle">
              <span class="score-value">{{ report.avg_score }}</span>
              <span class="score-max">/ 5.0</span>
            </div>
            <div class="score-info">
              <div class="score-item">
                <span class="label">平均分：</span>
                <span class="value">{{ report.avg_score }} / 5.0</span>
              </div>
              <div class="score-item">
                <span class="label">进步趋势：</span>
                <span class="value">{{ report.progress_tracking }}</span>
              </div>
              <el-progress :percentage="report.avg_score * 20" :color="progressColor" />
            </div>
          </div>
        </el-card>

        <el-card style="margin-top: 20px;">
          <h3>薄弱环节</h3>
          <div class="weak-points">
            <el-tag v-for="(point, i) in report.weak_points" :key="i" type="danger" effect="dark" style="margin: 5px;">
              {{ point }}
            </el-tag>
          </div>
        </el-card>

        <el-card style="margin-top: 20px;">
          <h3>推荐真题</h3>
          <div class="real-questions">
            <el-timeline>
              <el-timeline-item v-for="(q, i) in report.real_questions" :key="i" type="success">
                <div class="question-item">
                  <h4>{{ Number(i) + 1 }}. {{ q.question }}</h4>
                  <div v-if="q.suggested_answer" class="suggested-answer">
                    <strong>参考答案：</strong>
                    <p>{{ q.suggested_answer }}</p>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>

        <el-card style="margin-top: 20px;">
          <h3>面试总结</h3>
          <div class="conclusion" v-html="formatContent(report.conclusion || '')"></div>
        </el-card>

        <div class="report-footer">
          <el-button @click="goBack" type="primary" style="margin-right: 10px;">
            返回面试
          </el-button>
          <el-button @click="goHome">返回首页</el-button>
        </div>
      </template>
    </el-skeleton>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/userStore'
import apiClient from '@/utils/axios'
import { ElMessage } from 'element-plus'
import { Printer, Download } from '@element-plus/icons-vue'

const router = useRouter()
const userStore = useUserStore()
const report = ref<any>(null)
const loading = ref(true)

// 场景标签映射
const sceneLabel = {
  it: 'IT 技术面试',
  language: '小语种口语',
  cert: '职业考证'
}[userStore.sceneType]

// 进度条颜色
const progressColor = computed(() => {
  const score = report.value?.avg_score || 0
  if (score >= 4.0) return '#67C23A'
  if (score >= 3.0) return '#E6A23C'
  return '#F56C6C'
})

// 格式化日期
const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 格式化内容，处理换行
const formatContent = (text: string) => {
  return text.replace(/\n/g, '<br>')
}

// 从后端获取报告数据
const fetchReport = async () => {
  loading.value = true
  try {
    const res = await apiClient.get('/api/report', {
      params: {
        user_id: userStore.userId,
        domain: userStore.sceneType
      }
    })
    
    if (res.data.status === 'success') {
      report.value = res.data.report
    } else {
      ElMessage.error('获取报告失败')
    }
  } catch (error) {
    console.error('获取报告失败:', error)
    ElMessage.error('获取报告失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 打印报告
const printReport = () => {
  window.print()
}

// 下载报告
const downloadReport = () => {
  if (!report.value) return
  
  try {
    const reportJson = JSON.stringify(report.value, null, 2)
    const blob = new Blob([reportJson], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ai_interview_report_${new Date().getTime()}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
    ElMessage.success('报告下载成功')
  } catch (error) {
    console.error('下载报告失败:', error)
    ElMessage.error('下载报告失败')
  }
}

// 返回面试页面
const goBack = () => {
  router.push('/interview')
}

// 返回首页
const goHome = () => {
  router.push('/')
}

// 组件挂载时获取报告数据
onMounted(() => {
  fetchReport()
})
</script>

<style scoped>
.report-container {
  max-width: 700px;
  margin: 40px auto;
  padding: 0 20px;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.report-title h3 {
  margin: 0 0 10px 0;
  color: #333;
}

.report-info {
  display: flex;
  gap: 20px;
  font-size: 14px;
  color: #666;
}

.report-actions {
  display: flex;
  gap: 10px;
}

.score-section {
  display: flex;
  align-items: center;
  gap: 30px;
}

.score-circle {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.score-value {
  font-size: 36px;
  font-weight: bold;
}

.score-max {
  font-size: 18px;
  opacity: 0.8;
}

.score-info {
  flex: 1;
}

.score-item {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-item .label {
  color: #666;
  font-weight: 500;
}

.score-item .value {
  color: #333;
  font-weight: bold;
}

.weak-points {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.question-item {
  margin-bottom: 20px;
}

.question-item h4 {
  margin: 0 0 10px 0;
  color: #333;
}

.suggested-answer {
  background: #f0f9eb;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #67c23a;
}

.suggested-answer p {
  margin: 5px 0 0 0;
  color: #333;
  line-height: 1.6;
}

.conclusion {
  line-height: 1.8;
  color: #333;
  white-space: pre-wrap;
}

.report-footer {
  margin-top: 30px;
  text-align: center;
}

.report-skeleton {
  padding: 20px;
}

/* 打印样式 */
@media print {
  .report-actions,
  .report-footer {
    display: none;
  }
}
</style>