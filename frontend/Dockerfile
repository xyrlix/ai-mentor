# 构建阶段
FROM node:18-alpine AS build

WORKDIR /app

# 复制依赖配置文件
COPY package*.json ./

# 安装依赖
RUN npm install --legacy-peer-deps

# 复制所有源代码
COPY . .

# 构建项目
RUN npm run build

# 生产阶段，使用Nginx托管静态文件
FROM nginx:alpine

# 复制构建好的静态文件到Nginx
COPY --from=build /app/dist /usr/share/nginx/html

# 复制自定义的Nginx配置文件
COPY nginx.conf /etc/nginx/nginx.conf

# 暴露80端口
EXPOSE 80

# 启动Nginx服务
CMD ["nginx", "-g", "daemon off;"]