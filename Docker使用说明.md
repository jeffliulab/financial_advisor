# Docker 使用说明

本文档介绍如何使用 Docker 构建和运行 AI Financial Advisor 项目。

---

## 📋 前置准备

- 安装 Docker（版本 20.10+）
- 安装 Docker Compose（版本 2.0+）
- 确保 `.env` 文件已配置（特别是 `DEEPSEEK_API_KEY`）

---

## 🚀 快速启动

### 方式一：使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方式二：使用启动脚本

**Windows:**

```bash
docker-start.bat
```

**Linux/Mac:**

```bash
chmod +x docker-start.sh
./docker-start.sh
```

---

## 🔧 常用命令

### 1. 构建镜像

```bash
# 构建镜像（生产环境）
docker build -t financial-advisor:latest .

# 使用 docker-compose 构建
docker-compose build

# 强制重新构建（不使用缓存）
docker-compose build --no-cache
```

### 2. 启动服务

```bash
# 启动服务（前台运行）
docker-compose up

# 启动服务（后台运行）
docker-compose up -d

# 指定配置文件启动（开发环境）
docker-compose -f docker-compose.dev.yml up -d
```

### 3. 查看状态

```bash
# 查看运行中的容器
docker-compose ps

# 查看容器日志
docker-compose logs

# 实时查看日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs financial-advisor
```

### 4. 停止服务

```bash
# 停止服务（保留容器）
docker-compose stop

# 停止并删除容器
docker-compose down

# 停止并删除容器、网络、卷
docker-compose down -v
```

### 5. 进入容器

```bash
# 进入容器 bash
docker-compose exec financial-advisor bash

# 或使用 sh
docker-compose exec financial-advisor sh

# 执行单个命令
docker-compose exec financial-advisor ls -la
```

### 6. 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启指定服务
docker-compose restart financial-advisor
```

---

## 🐛 调试相关

### 查看详细日志

```bash
# 查看最近100行日志
docker-compose logs --tail=100

# 持续监控日志
docker-compose logs -f --tail=100
```

### 检查容器健康状态

```bash
# 查看容器状态
docker ps

# 查看容器详细信息
docker inspect financial_advisor
```

### 清理无用资源

```bash
# 清理停止的容器
docker container prune

# 清理无用镜像
docker image prune

# 清理所有无用资源（谨慎使用）
docker system prune -a
```

---

## 🔄 更新代码

```bash
# 1. 停止服务
docker-compose down

# 2. 拉取最新代码（如果使用 Git）
git pull

# 3. 重新构建镜像
docker-compose build

# 4. 启动服务
docker-compose up -d
```

---

## 📊 端口说明

| 服务        | 容器端口 | 主机端口 | 说明                    |
| ----------- | -------- | -------- | ----------------------- |
| Backend     | 8000     | 8000     | 主服务 API 端口         |
| Brain (dev) | 8001     | 8001     | AI 引擎端口（开发环境） |

访问地址：

- 主应用：http://localhost:8000
- API 文档：http://localhost:8000/docs
- Brain API（开发环境）：http://localhost:8001

---

## 📁 数据持久化

数据保存在以下目录（会自动挂载到容器）：

```
./data/              # 用户数据（生产环境）
./backend_data/      # 后端数据（开发环境）
./secure_uploads/    # 用户上传文件（开发环境）
```

**备份数据：**

```bash
# 备份 data 目录
tar -czf data_backup_$(date +%Y%m%d).tar.gz data/
```

**恢复数据：**

```bash
# 解压备份
tar -xzf data_backup_20241023.tar.gz
```

---

## 🌍 环境变量配置

在 `.env` 文件中配置：

```env
# DeepSeek API 配置
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_TEMPERATURE=0.7
DEEPSEEK_MAX_TOKENS=2000

# JWT 配置
SECRET_KEY=your_secret_key_here
```

---

## ⚙️ 开发环境 vs 生产环境

### 生产环境（docker-compose.yml）

- 单服务架构
- 不挂载源码（代码打包到镜像内）
- 适合部署到服务器

```bash
docker-compose up -d
```

### 开发环境（docker-compose.dev.yml）

- 多服务架构（brain + backend）
- 挂载源码（支持热重载）
- 适合本地开发调试

```bash
docker-compose -f docker-compose.dev.yml up -d
```

---

## 🔐 安全建议

1. **不要将 `.env` 文件提交到 Git**
2. **定期更新 Docker 镜像** 以获取安全补丁
3. **限制容器资源** 使用（可选）：
   ```yaml
   # 在 docker-compose.yml 中添加
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 1G
   ```

---

## ❓ 常见问题

### 1. 端口被占用

```bash
# 查看占用端口的进程
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac

# 修改 docker-compose.yml 中的端口映射
ports:
  - "8080:8000"  # 使用 8080 代替 8000
```

### 2. 容器启动失败

```bash
# 查看详细错误信息
docker-compose logs

# 检查 .env 文件是否存在
ls -la .env

# 检查 API Key 是否配置
docker-compose exec financial-advisor env | grep DEEPSEEK
```

### 3. 数据丢失问题

确保使用了卷挂载：

```yaml
volumes:
  - ./data:/app/data  # 数据会保存在宿主机的 ./data 目录
```

---

## 📚 更多资源

- [Docker 官方文档](https://docs.docker.com/)
- [Docker Compose 文档](https://docs.docker.com/compose/)
- [项目 README](./README.md)

---

## 🎯 快速参考

```bash
# 一键启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 进入容器
docker-compose exec financial-advisor bash

# 清理所有（包括数据卷，谨慎使用）
docker-compose down -v
```
