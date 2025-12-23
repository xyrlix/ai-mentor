# AI Mentor

你的私人 AI 面试教练 + 知识顾问 + 考试顾问

## 项目简介

AI Mentor 是一个基于 AI 技术的智能学习助手系统，集成了智能问答、模拟面试、考试练习三大核心功能。系统支持多种场景（IT、小语种、职业考证），提供实时流式 AI 回复，生成详细的学习报告和成长建议。

## 核心功能亮点

### 🎯 智能问答系统
- **知识库问答**：基于上传的文档进行智能问答
- **多轮对话**：支持连续问答，上下文理解
- **答案评估**：自动评估回答质量，提供改进建议
- **相关推荐**：智能推荐相关问题，深化学习

### 💼 智能模拟面试
- **多角色面试官**：技术主管、HR经理、产品总监、CTO、语言专家等
- **多场景面试**：行为面试、技术面试、案例分析、系统设计等
- **实时流式回复**：逐字输出，模拟真实面试体验
- **智能评估反馈**：多维度评分，详细反馈建议

### 📝 考试模拟系统
- **多种考试类型**：软考、PMP、CPA、教师资格证等
- **模拟考试模式**：完整考试流程，时间限制，自动评分
- **练习模式**：逐题练习，即时反馈，错题回顾
- **真题库支持**：内置丰富的考试题目资源

### 🎤 语音交互功能
- **语音识别**：支持语音输入，实时转文本
- **语音合成**：AI回复可语音播报
- **语音面试**：完整的语音面试流程
- **多语言支持**：中文、英文等多种语言

### 📊 智能报告系统
- **详细分析报告**：面试、考试、问答的综合报告
- **进度追踪**：学习进度可视化，趋势分析
- **薄弱环节分析**：智能识别知识缺口
- **个性化建议**：基于历史数据的定制化学习建议

## 技术栈

### 后端架构
- **FastAPI** - 高性能 Python Web 框架，支持异步处理和自动文档生成
- **PostgreSQL + pgvector** - 关系型数据库 + 向量数据库，支持高效的知识检索
- **LangChain** - 大模型应用开发框架，支持多模型调用和RAG流程
- **Redis** - 缓存系统，用于向量检索缓存、会话管理和任务状态跟踪
- **Celery** - 异步任务队列，用于文档处理、向量生成等后台任务
- **Docker** - 容器化部署，支持快速部署和扩展

### AI模型支持
- **多模型提供商**：通义千问、深度求索、智谱AI、OpenAI
- **向量模型**：BAAI/bge-large-zh-v1.5，支持1024维向量
- **语音服务**：Azure Speech Service，支持语音识别和合成

### 前端技术
- **Vue 3 + TypeScript** - 现代化前端框架，类型安全
- **Element Plus** - 企业级 UI 组件库，美观易用
- **Pinia** - 状态管理，支持组件间数据共享
- **Vite** - 构建工具，快速开发和热重载
- **Nginx** - 生产环境静态资源托管和反向代理

### 系统特色
- **模块化设计**：问答、面试、考试三大模块独立可扩展
- **实时交互**：流式API支持实时对话和打字机效果
- **智能缓存**：多级缓存优化，提升系统性能
- **安全可靠**：JWT认证、文件类型检查、API限流

## 目录结构

```
ai-mentor/
├── backend/                # 后端代码
│   ├── agent/             # AI 面试代理
│   ├── rag/               # 检索增强生成
│   ├── models/            # 数据模型
│   ├── schemas/           # 请求响应模型
│   ├── routes/            # API 路由
│   ├── services/          # 业务服务
│   ├── utils/             # 工具函数
│   ├── report/            # 报告生成
│   ├── voice/             # 语音处理
│   ├── config.py          # 配置文件
│   ├── main.py            # 入口文件
│   ├── requirements.txt   # 依赖列表
│   ├── tasks.py           # Celery 任务
│   └── worker.py          # Celery 工作器
├── frontend/              # 前端代码
│   ├── src/               # 源代码
│   │   ├── components/    # Vue 组件
│   │   ├── composables/   # 组合式函数
│   │   ├── stores/        # 状态管理
│   │   ├── views/         # 页面组件
│   │   ├── router/        # 路由配置
│   │   ├── App.vue        # 根组件
│   │   └── main.ts        # 入口文件
│   ├── Dockerfile         # 前端 Docker 构建文件
│   ├── nginx.conf         # Nginx 配置
│   ├── package.json       # 前端依赖
│   └── vite.config.ts     # Vite 配置
├── docker-compose.yml     # Docker Compose 配置
├── init_pgvector.sql      # PostgreSQL 初始化脚本
└── README.md              # 项目说明
```

## 运行指南

### 开发环境

#### 快速启动（推荐）

使用项目根目录的启动脚本一键启动所有服务：

```bash
# 启动所有服务
./start.sh

# 停止所有服务
./stop.sh
```

#### 后端运行

1. 安装依赖
```bash
cd backend
pip install -r requirements.txt
```

2. 配置环境变量
创建 `.env` 文件，添加以下内容：
```
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_mentor

# 大模型配置
LLM_PROVIDER=qwen  # 可选：qwen, deepseek, zhipu, openai
QWEN_API_KEY=your_qwen_api_key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_MODEL=qwen-max
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
```

3. 启动后端服务
```bash
cd backend
# 激活虚拟环境
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### 前端运行

1. 安装依赖
```bash
cd frontend
npm install
```

2. 启动开发服务器
```bash
npm run dev
```

3. 访问应用
浏览器访问 http://localhost:5173

### 生产环境（Docker 部署）

1. 配置环境变量
创建 `.env` 文件，参考 "环境变量配置" 部分的详细说明。最基本的配置示例：
```
# 大模型配置
LLM_PROVIDER=qwen
QWEN_API_KEY=your_qwen_api_key

# 数据库配置（可选，默认使用 docker-compose 中的配置）
# DATABASE_URL=postgresql://postgres:password@db:5432/ai_mentor
```

2. 构建并启动所有服务
```bash
docker-compose up --build -d
```

3. 访问应用
浏览器访问 http://localhost

## 环境变量配置

### 大模型配置

| 变量名 | 说明 | 可选值 | 默认值 |
|-------|------|--------|--------|
| LLM_PROVIDER | 大模型提供商 | qwen, deepseek, zhipu, openai | qwen |
| LLM_TEMPERATURE | 大模型温度参数 | - | 0.7 |
| LLM_MAX_TOKENS | 大模型最大输出token数 | - | 2000 |
| QWEN_API_KEY | 通义千问 API Key | - | - |
| QWEN_API_BASE | 通义千问 API 地址 | - | https://dashscope.aliyuncs.com/compatible-mode/v1 |
| QWEN_MODEL | 通义千问模型名称 | - | qwen-max |
| DEEPSEEK_API_KEY | 深度求索 API Key | - | - |
| DEEPSEEK_API_BASE | 深度求索 API 地址 | - | https://api.deepseek.com/v1 |
| DEEPSEEK_MODEL | 深度求索模型名称 | - | deepseek-chat |
| ZHIPU_API_KEY | 智谱 AI API Key | - | - |
| ZHIPU_API_BASE | 智谱 AI API 地址 | - | https://open.bigmodel.cn/api/paas/v4 |
| ZHIPU_MODEL | 智谱 AI 模型名称 | - | glm-4 |
| OPENAI_API_KEY | OpenAI API Key | - | - |
| OPENAI_API_BASE | OpenAI API 地址 | - | https://api.openai.com/v1 |
| OPENAI_MODEL | OpenAI 模型名称 | - | gpt-3.5-turbo |

### 数据库配置

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| DATABASE_URL | 数据库连接字符串 | postgresql://postgres:password@db:5432/ai_mentor |

### 缓存和队列配置

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| REDIS_URL | Redis 连接字符串 | redis://redis:6379/0 |
| CELERY_BROKER_URL | Celery 消息代理 | redis://redis:6379/0 |
| CELERY_RESULT_BACKEND | Celery 结果存储 | redis://redis:6379/0 |

### 支付配置

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| STRIPE_API_KEY | Stripe API 密钥 | - |
| STRIPE_WEBHOOK_SECRET | Stripe 支付回调密钥 | - |

### 语音服务配置

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| AZURE_SPEECH_KEY | Azure Speech Service 密钥 | - |
| AZURE_SPEECH_REGION | Azure Speech Service 区域 | eastasia |

### 向量模型配置

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| EMBEDDING_MODEL | 向量嵌入模型 | BAAI/bge-large-zh-v1.5 |
| VECTOR_DIMENSION | 向量维度 | 1024 |

### 文件上传配置

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| MAX_FILE_SIZE | 最大文件大小（字节） | 104857600（100MB） |
| ALLOWED_EXTENSIONS | 允许的文件扩展名 | .pdf, .docx, .txt |

### 其他配置

| 变量名 | 说明 | 默认值 |
|-------|------|--------|
| DEBUG | 调试模式 | True |
| SECRET_KEY | JWT 密钥 | - |
| ALGORITHM | JWT 算法 | HS256 |
| ACCESS_TOKEN_EXPIRE_MINUTES | JWT 过期时间（分钟） | 30 |
| RATE_LIMIT | API 速率限制（每分钟请求数） | 100 |
| CACHE_EXPIRE_MINUTES | 缓存过期时间（分钟） | 30 |

## API 接口说明

### 基本路由

- `GET /` - API 根路径
- `GET /health` - 健康检查接口

### 认证相关接口

- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息

### 智能问答系统接口

- `POST /api/qna/ask` - 智能问答，基于知识库回答问题
- `POST /api/qna/evaluate` - 评估用户回答质量
- `GET /api/qna/related-questions` - 获取相关问题推荐
- `GET /api/qna/history` - 获取问答历史记录

### 模拟面试系统接口

- `POST /api/interview/start` - 开始面试
- `GET /api/interview/stream` - 流式获取面试回复
- `POST /api/interview/end` - 结束面试
- `POST /api/interview/text` - 文本面试接口
- `POST /api/interview/ask` - 根据用户回答生成下一个问题
- `GET /api/interview/history` - 获取面试历史记录
- `POST /api/interview/voice` - 语音面试接口

### 考试模拟系统接口

- `GET /api/exam/types` - 获取支持的考试类型
- `POST /api/exam/simulate-exam` - 模拟考试
- `POST /api/exam/practice-mode` - 练习模式
- `POST /api/exam/submit-exam` - 提交考试
- `GET /api/exam/questions` - 获取考试题目
- `GET /api/exam/statistics` - 获取考试统计信息

### 文档上传和知识库接口

- `POST /api/upload` - 上传单个文档
- `POST /api/upload/batch` - 批量上传文档
- `GET /api/task/{task_id}` - 查询文档处理任务状态
- `POST /api/knowledge-bases` - 创建知识库
- `GET /api/knowledge-bases/{user_id}` - 获取用户知识库列表

### 报告生成接口

- `POST /api/report/generate-interview` - 生成面试报告
- `POST /api/report/generate-exam` - 生成考试报告
- `POST /api/report/generate-qna` - 生成问答报告
- `POST /api/report/generate-comprehensive` - 生成综合报告
- `GET /api/report/history` - 获取报告历史

### 语音交互接口

- `POST /api/speech/to-text` - 语音转文本
- `POST /api/speech/to-speech` - 文本转语音
- `POST /api/speech/stream-text-to-speech` - 流式文本转语音
- `POST /api/speech/stream-speech-to-text` - 流式语音转文本
- `GET /api/speech/voices` - 获取可用语音列表
- `POST /api/speech/voice-interview` - 语音面试处理

### 用户历史追踪接口

- `GET /api/history/activities` - 获取用户活动记录
- `GET /api/history/stats` - 获取用户活动统计
- `GET /api/history/trend` - 获取用户进度趋势
- `GET /api/history/weak-areas` - 获取薄弱环节分析
- `DELETE /api/history/clear` - 清除用户历史记录

### 支付相关接口

- `GET /api/payment/prices` - 获取价格列表
- `POST /api/payment/checkout` - 创建支付会话
- `POST /api/payment/webhook` - Stripe 支付回调
- `GET /api/payment/subscription` - 获取订阅状态

## 核心功能

1. **多场景支持**
   - IT 技术面试
   - 小语种口语面试
   - 职业考证面试

2. **智能面试**
   - 基于用户上传的文档生成个性化问题
   - 实时流式 AI 回复，逐字输出
   - 支持多种大模型提供商

3. **详细报告**
   - 综合评分
   - 薄弱环节分析
   - 推荐学习内容
   - 面试历史记录

4. **安全保障**
   - JWT 用户认证和授权
   - 文件上传类型和大小限制
   - API 速率限制保护

5. **性能优化**
   - Redis 缓存加速向量检索
   - Celery 异步处理文档解析
   - 优化的向量存储和检索算法

6. **支付系统**
   - Stripe 支付集成
   - 支持订阅和一次性支付
   - 支付状态管理

7. **语音功能**
   - 语音转文本（Azure Speech Service）
   - 文本转语音（Azure Speech Service）
   - 语音面试支持

8. **用户体验优化**
   - 面试进度条
   - 支持面试草稿保存
   - 移动端适配

9. **生产级部署**
   - Docker 容器化部署
   - Nginx 静态资源托管
   - PostgreSQL 数据持久化
   - 支持多用户使用


## 许可证

MIT License
