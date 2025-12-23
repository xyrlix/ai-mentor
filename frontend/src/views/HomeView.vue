<!-- views/HomeView.vue -->
<template>
  <div class="home">
    <h1>AI Mentor - 你的智能面试教练</h1>
    <p>选择你的学习场景：</p>
    
    <div class="scene-grid">
      <el-card @click="selectScene('it')" class="scene-card">
        <h3>💻 IT 技术</h3>
        <p>后端/前端/算法/测试/产品/设计</p>
      </el-card>
      
      <el-card @click="selectScene('language')" class="scene-card">
        <h3>🌍 小语种</h3>
        <p>雅思 / 粤语 / 日语 / 英语口语</p>
      </el-card>
      
      <el-card @click="selectScene('cert')" class="scene-card">
        <h3>📜 职业考证</h3>
        <p>软考 / PMP / 会计 / 法律 / 教师资格</p>
      </el-card>
    </div>
    
    <div class="action-buttons">
      <router-link to="/upload">
        <el-button type="primary" size="large">开始上传资料</el-button>
      </router-link>
      <router-link to="/qna" v-if="userStore.kbId">
        <el-button type="success" size="large">智能问答</el-button>
      </router-link>
      <router-link to="/interview" v-if="userStore.kbId">
        <el-button type="warning" size="large">开始面试</el-button>
      </router-link>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useUserStore } from '@/stores/userStore'
import type { SceneType } from '@/stores/userStore'

const userStore = useUserStore()

const selectScene = (scene: SceneType) => {
  userStore.setScene(scene)
  // 保存用户ID到本地存储
  userStore.saveUserId()
}
</script>

<style scoped>
.home {
  text-align: center;
  padding: 40px 20px;
}

.home h1 {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #1890ff;
}

.home p {
  font-size: 1.2rem;
  margin-bottom: 2rem;
  color: #666;
}

.scene-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin: 30px 0;
  max-width: 800px;
  margin-left: auto;
  margin-right: auto;
}

.scene-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  border-radius: 12px;
  border: 2px solid #e8e8e8;
}

.scene-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-color: #1890ff;
}

.scene-card h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: #333;
}

.scene-card p {
  font-size: 0.9rem;
  color: #666;
  margin: 0;
}

:deep(.el-card__body) {
  padding: 20px;
}
</style>
