<!-- views/UploadView.vue -->
<template>
  <div class="upload-container">
    <h2>上传你的学习资料</h2>
    <el-upload
      drag
      :auto-upload="false"
      :on-change="handleFileChange"
      accept=".pdf,.docx,.txt,.pptx"
      :show-file-list="false"
      :before-upload="beforeUpload"
    >
      <el-icon class="el-icon--upload"><upload-filled /></el-icon>
      <div class="el-upload__text">将文件拖到此处，或<em>点击上传</em></div>
    </el-upload>

    <div v-if="selectedFile" class="file-preview">
      <el-card>
        <div class="file-info">
          <el-icon class="file-icon"><document /></el-icon>
          <div>
            <div class="file-name">{{ selectedFile.name }}</div>
            <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
          </div>
          <el-button type="danger" size="small" @click="removeFile">
            <el-icon><delete /></el-icon>
          </el-button>
        </div>
      </el-card>
    </div>

    <el-button
      type="primary"
      @click="uploadFile"
      :disabled="!selectedFile || uploading"
      style="margin-top: 20px"
      size="large"
    >
      <el-icon v-if="uploading"><loading /></el-icon>
      <span>{{ uploading ? `处理中... ${uploadProgress > 0 ? `(${uploadProgress}%)` : ''}` : "开始解析" }}</span>
    </el-button>

    <el-progress
      v-if="uploading && uploadProgress > 0"
      :percentage="uploadProgress"
      :stroke-width="8"
      style="margin-top: 15px"
      status="success"
    />

    <el-button 
      @click="testConnection" 
      type="info" 
      size="small" 
      style="margin-top: 10px"
      :loading="testing"
    >
      {{ testing ? '测试中...' : '测试后端连接' }}
    </el-button>

    <el-alert
      v-if="errorMessage"
      :title="errorMessage"
      type="error"
      style="margin-top: 20px"
      show-icon
      :closable="true"
      @close="errorMessage = ''"
    />
    
    <el-alert
      v-if="uploadResult"
      :title="`知识库创建成功！ID: ${uploadResult.kb_id}`"
      type="success"
      style="margin-top: 20px"
      description="您的资料已成功上传并处理，可以开始面试了。"
      show-icon
    >
      <template #footer>
        <div style="display: flex; gap: 10px; align-items: center;">
          <router-link to="/interview">
            <el-button type="primary" size="small" @click="cancelAutoRedirect">立即开始面试</el-button>
          </router-link>
          <span v-if="autoRedirect && countdown > 0">
            或 {{ countdown }} 秒后自动跳转
          </span>
          <el-button v-if="autoRedirect && countdown > 0" type="text" size="small" @click="cancelAutoRedirect">
            取消自动跳转
          </el-button>
        </div>
      </template>
    </el-alert>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import {
  UploadFilled,
  Document,
  Delete,
  Loading,
} from "@element-plus/icons-vue";
import { useUserStore } from "@/stores/userStore";
import apiClient from "@/utils/axios";

const userStore = useUserStore();
const selectedFile = ref<File | null>(null);
const uploading = ref(false);
const uploadResult = ref<{ kb_id: number } | null>(null);
const errorMessage = ref<string>("");
const uploadProgress = ref<number>(0);
const testing = ref<boolean>(false);
const countdown = ref<number>(5);
const autoRedirect = ref<boolean>(true);

// 检查后端连接状态
const checkBackendConnection = async () => {
  try {
    // 直接使用完整的URL进行健康检查，不通过代理
    const { default: axios } = await import('axios');
    await axios.get('http://localhost:8000/health', { timeout: 5000 });
    console.log('后端连接成功');
    return true;
  } catch (error) {
    console.error('后端连接失败:', error);
    return false;
  }
};

const handleFileChange = (file: any) => {
  errorMessage.value = "";
  selectedFile.value = file.raw;
};

const beforeUpload = (file: File) => {
  const isValidType = ['.pdf', '.docx', '.txt', '.pptx'].some(ext => file.name.toLowerCase().endsWith(ext));
  if (!isValidType) {
    errorMessage.value = "仅支持 PDF、DOCX、TXT 格式的文件";
    return false;
  }
  
  const isLt100M = file.size / 1024 / 1024 < 100;
  if (!isLt100M) {
    errorMessage.value = "文件大小不能超过 100MB";
    return false;
  }
  
  return true;
};

const removeFile = () => {
  selectedFile.value = null;
};

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
};

const testConnection = async () => {
  testing.value = true;
  const isConnected = await checkBackendConnection();
  testing.value = false;
  
  if (isConnected) {
    errorMessage.value = "";
    alert('后端连接正常！');
  } else {
    errorMessage.value = "无法连接到后端服务，请确保后端已启动 (http://localhost:8000)";
  }
};

// 自动跳转倒计时
const startCountdown = () => {
  console.log("倒计时开始，初始值:", countdown.value);
  const timer = setInterval(() => {
    countdown.value--;
    console.log("倒计时:", countdown.value);
    if (countdown.value <= 0) {
      clearInterval(timer);
      console.log("倒计时结束，准备跳转");
      redirectToInterview();
    }
  }, 1000);
};

// 跳转到面试页面
const redirectToInterview = () => {
  window.location.href = '/interview';
};

// 取消自动跳转
const cancelAutoRedirect = () => {
  autoRedirect.value = false;
  countdown.value = 0;
};

const uploadFile = async () => {
  if (!selectedFile.value) return;
  
  errorMessage.value = "";
  
  // 先检查后端连接
  const isConnected = await checkBackendConnection();
  if (!isConnected) {
    errorMessage.value = "无法连接到后端服务，请确保后端已启动 (http://localhost:8000)";
    return;
  }

  const formData = new FormData();
  formData.append("user_id", userStore.userId);
  formData.append("file", selectedFile.value);

  uploading.value = true;
  uploadProgress.value = 0;
  try {
    // 使用直接的URL而不是代理，避免网络错误
    const { default: axios } = await import('axios');
    const res = await axios.post("http://localhost:8000/api/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000, // 60秒超时
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          uploadProgress.value = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        }
      },
    });
    uploadResult.value = res.data;
    console.log("上传响应:", res.data);
    console.log("kb_id:", res.data.kb_id);
    
    if (res.data.kb_id) {
      userStore.setKbId(res.data.kb_id);
      
      // 启动自动跳转倒计时
      if (autoRedirect.value) {
        console.log("开始倒计时");
        startCountdown();
      }
    } else {
      console.error("响应中缺少 kb_id:", res.data);
    }
  } catch (error: any) {
    console.error("上传失败:", error);
    uploadResult.value = null;
    
    if (error.response) {
      // 服务器返回的错误
      const status = error.response.status;
      const detail = error.response.data?.detail || "未知错误";
      
      switch (status) {
        case 400:
          errorMessage.value = `请求错误: ${detail}`;
          break;
        case 413:
          errorMessage.value = "文件过大，请选择小于100MB的文件";
          break;
        case 429:
          errorMessage.value = "上传频率过高，请稍后再试";
          break;
        case 500:
          errorMessage.value = `服务器错误: ${detail}`;
          break;
        default:
          errorMessage.value = `上传失败: ${detail}`;
      }
    } else if (error.code === 'ECONNABORTED') {
      errorMessage.value = "上传超时，请检查网络连接或重试";
    } else if (error.message) {
      errorMessage.value = `网络错误: ${error.message}`;
    } else {
      errorMessage.value = "上传失败，请稍后重试";
    }
  } finally {
    uploading.value = false;
    uploadProgress.value = 0;
  }
};
</script>

<style scoped>
.upload-container {
  max-width: 600px;
  margin: 40px auto;
  text-align: center;
}

.upload-container h2 {
  font-size: 2rem;
  margin-bottom: 2rem;
  color: #1890ff;
}

.file-preview {
  margin-top: 20px;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-icon {
  font-size: 24px;
  color: #1890ff;
}

.file-name {
  font-weight: 500;
  font-size: 16px;
  color: #333;
}

.file-size {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

:deep(.el-card__body) {
  padding: 16px;
}
</style>
