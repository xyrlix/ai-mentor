-- 创建数据库（如果不存在）
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'ai_mentor') THEN
        CREATE DATABASE ai_mentor;
    END IF;
END $$;

\c ai_mentor;

-- 尝试安装 pgvector 扩展（如果可用）
DO $$
BEGIN
    CREATE EXTENSION IF NOT EXISTS vector;
    EXCEPTION
        WHEN OTHERS THEN
            RAISE NOTICE 'pgvector 扩展不可用，将使用替代方案';
END $$;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 知识库表
CREATE TABLE IF NOT EXISTS knowledge_bases (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(20) NOT NULL, -- 'it', 'language', 'cert'
    sub_domain VARCHAR(50), -- 'backend', 'ielts', 'soft_high'
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 文档表
CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    kb_id INT NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    file_type TEXT NOT NULL,
    content TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 文档片段表
DO $$
BEGIN
    -- 检查表是否已存在
    IF NOT EXISTS (SELECT 1 FROM pg_tables WHERE tablename = 'chunks') THEN
        -- 检查向量扩展是否可用
        IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
            -- 支持向量的表结构
            CREATE TABLE chunks (
                id BIGSERIAL PRIMARY KEY,
                kb_id INT NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                document_id INT REFERENCES documents(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                metadata JSONB,
                embedding VECTOR(1024), -- bge-large-zh-v1.5 输出维度
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
            
            -- 创建向量索引
            CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
        ELSE
            -- 不支持向量的替代表结构
            CREATE TABLE chunks (
                id BIGSERIAL PRIMARY KEY,
                kb_id INT NOT NULL REFERENCES knowledge_bases(id) ON DELETE CASCADE,
                document_id INT REFERENCES documents(id) ON DELETE CASCADE,
                content TEXT NOT NULL,
                metadata JSONB,
                embedding BYTEA, -- 使用字节数组作为替代
                embedding_dim INT DEFAULT 1024,
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        END IF;
    END IF;
END $$;

-- 创建关键词搜索索引
CREATE INDEX IF NOT EXISTS idx_chunks_content ON chunks USING GIN (to_tsvector('english', content));

-- 面试题库
CREATE TABLE IF NOT EXISTS interview_questions (
    id SERIAL PRIMARY KEY,
    domain VARCHAR(20) NOT NULL,
    sub_domain VARCHAR(50),
    question TEXT NOT NULL,
    answer TEXT,
    source VARCHAR(50), -- 'leetcode', 'manual', 'llm'
    difficulty VARCHAR(10)
);

-- 面试记录
CREATE TABLE IF NOT EXISTS interviews (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    kb_id INT NOT NULL,
    domain VARCHAR(20) NOT NULL,
    role TEXT,
    transcript JSONB,
    score NUMERIC(3,2),
    feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 面试对话表
CREATE TABLE IF NOT EXISTS interview_conversations (
    id SERIAL PRIMARY KEY,
    interview_id INTEGER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    speaker TEXT NOT NULL CHECK (speaker IN ('interviewer', 'candidate')),
    content TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(interview_id, sequence_number)
);

-- 面试报告表
CREATE TABLE IF NOT EXISTS interview_reports (
    id SERIAL PRIMARY KEY,
    report_id TEXT NOT NULL UNIQUE,
    interview_id INTEGER NOT NULL REFERENCES interviews(id) ON DELETE CASCADE,
    feedback TEXT NOT NULL,
    score INTEGER NOT NULL,
    conclusion TEXT,
    improvement_suggestions TEXT[],
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建技术技能评分表
CREATE TABLE IF NOT EXISTS technical_skills (
    id SERIAL PRIMARY KEY,
    report_id INTEGER NOT NULL REFERENCES interview_reports(id) ON DELETE CASCADE,
    skill_name TEXT NOT NULL,
    skill_score INTEGER NOT NULL,
    UNIQUE(report_id, skill_name)
);
