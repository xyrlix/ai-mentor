#!/bin/bash

# PostgreSQL 初始化脚本 (Ubuntu)
# 用于执行 init_pgvector.sql 创建数据库和表结构

# 配置参数
PG_USER="postgres"
PG_PASSWORD="postgres1688"  # 请根据实际情况修改
PG_HOST="localhost"
PG_PORT="5432"
SQL_FILE="init_pgvector.sql"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== PostgreSQL 初始化脚本 ===${NC}"

# 检查脚本是否存在
if [ ! -f "$SQL_FILE" ]; then
    echo -e "${RED}错误: 找不到 SQL 文件 $SQL_FILE${NC}"
    exit 1
fi

# 检查 PostgreSQL 是否已安装
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}PostgreSQL 未安装，正在安装...${NC}"
    sudo apt-get update
    sudo apt-get install -y postgresql postgresql-contrib
fi

# 检查 pgvector 扩展是否已安装
if ! psql -h $PG_HOST -p $PG_PORT -U $PG_USER -c "SELECT * FROM pg_extension WHERE extname = 'vector'" | grep -q vector; then
    echo -e "${YELLOW}pgvector 扩展未安装，正在安装...${NC}"
    
    # 尝试多种安装方式
    if sudo apt-get install -y postgresql-pgvector; then
        echo -e "${GREEN}pgvector 通过 apt 安装成功${NC}"
    elif sudo apt-get install -y postgresql-16-pgvector; then
        echo -e "${GREEN}pgvector (PostgreSQL 16) 通过 apt 安装成功${NC}"
    else
        echo -e "${YELLOW}尝试从源码编译安装 pgvector...${NC}"
        # 安装编译依赖
        sudo apt-get install -y git build-essential libpq-dev postgresql-server-dev-16
        
        # 克隆源码并编译安装
        cd /tmp
        git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
        cd pgvector
        make
        sudo make install
        echo -e "${GREEN}pgvector 从源码编译安装成功${NC}"
    fi
fi

# 检查 PostgreSQL 服务是否运行
if ! pg_isready -h $PG_HOST -p $PG_PORT &> /dev/null; then
    echo -e "${YELLOW}PostgreSQL 服务未运行，正在启动...${NC}"
    sudo systemctl start postgresql
    sudo systemctl enable postgresql
fi

# 等待服务启动
echo -e "${YELLOW}等待 PostgreSQL 服务启动...${NC}"
sleep 2

# 设置 PostgreSQL 用户密码（如果需要）
echo -e "${YELLOW}设置 PostgreSQL 用户密码...${NC}"
sudo -u $PG_USER psql -c "ALTER USER $PG_USER WITH PASSWORD '$PG_PASSWORD';" 2>/dev/null || echo -e "${GREEN}密码已设置${NC}"

# 执行 SQL 脚本
echo -e "${YELLOW}正在执行初始化 SQL 脚本...${NC}"
if sudo -u $PG_USER psql -h $PG_HOST -p $PG_PORT -f "$SQL_FILE"; then
    echo -e "${GREEN}✅ 数据库初始化成功！${NC}"
    
    # 显示创建的表
echo -e "${YELLOW}创建的表结构：${NC}"
sudo -u $PG_USER psql -h $PG_HOST -p $PG_PORT -d ai_mentor -c "\dt"p
    
else
    echo -e "${RED}❌ 数据库初始化失败！${NC}"
    exit 1
fi

echo -e "${GREEN}=== 初始化完成 ===${NC}"
