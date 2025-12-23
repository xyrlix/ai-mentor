<!-- components/ChatMessage.vue -->
<template>
  <div class="message" :class="{ 'ai': isAi, 'user': !isAi }">
    <div class="avatar">{{ isAi ? '🤖' : '👤' }}</div>
    <div class="content" v-html="formatContent(content)"></div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  content: string
  isAi: boolean
}>()

const formatContent = (text: string) => {
  return text.replace(/\n/g, '<br>')
}
</script>

<style scoped>
.message {
  display: flex;
  margin: 12px 0;
  max-width: 80%;
}
.ai { 
  align-self: flex-start; 
}
.user { 
  align-self: flex-end; 
  flex-direction: row-reverse; 
}
.avatar {
  font-size: 20px;
  margin: 0 8px;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.content {
  padding: 10px 14px;
  border-radius: 12px;
  background: #f0f2f5;
  line-height: 1.6;
  word-wrap: break-word;
}
.user .content {
  background: #1890ff;
  color: white;
}
</style>
