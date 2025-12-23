import axios from 'axios'

const apiClient = axios.create({
  baseURL: '', // 使用空baseURL，让Vite代理处理
  timeout: 60000, // 增加到60秒，文件上传需要更长时间
  headers: {
    'Content-Type': 'application/json'
  }
})

// 添加请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    // 可以在这里添加token等认证信息
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 添加响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 统一处理错误
    console.error('API Error:', error)
    
    if (error.code === 'NETWORK_ERROR' || error.message === 'Network Error') {
      error.message = '网络连接失败，请检查后端服务是否启动 (http://localhost:8000)'
    } else if (error.code === 'ECONNABORTED') {
      error.message = '请求超时，请稍后重试'
    } else if (error.response) {
      // 服务器响应了但状态码不是2xx
      error.message = `服务器错误 ${error.response.status}: ${error.response.data?.detail || error.response.statusText}`
    } else if (error.request) {
      // 请求已发出但没有收到响应
      error.message = '无法连接到服务器，请检查后端是否启动'
    }
    
    return Promise.reject(error)
  }
)

export default apiClient
