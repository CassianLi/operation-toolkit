# Docker Compose 通用权限管理模板

## 概述

这是一个通用的Docker Compose权限管理模板，适用于任何服务的部署。通过将容器内用户映射到宿主机用户组，解决权限问题，无需复杂的脚本配置。

## 核心特性

### 1. 通用性
- 适用于任何Docker服务
- 不依赖特定镜像或服务
- 可复用的配置模板

### 2. 权限管理
- 容器内用户映射到宿主机用户组
- 利用宿主机用户组的现有权限
- 避免复杂的用户创建和权限设置

### 3. 配置简化
- 优先使用Docker Compose配置文件
- 最小化脚本依赖
- 便于阅读和维护

## 使用方法

### 步骤1: 获取宿主机用户信息
```bash
# 在宿主机运行以下命令
id

# 输出示例: uid=1001(deployer) gid=1002(developers) groups=1002(developers)
# 记录: HOST_USER_ID=1001, HOST_GROUP_ID=1002
```

### 步骤2: 配置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑环境变量文件
nano .env

# 设置必要的用户信息
HOST_USER_ID=1001
HOST_GROUP_ID=1002
HOST_USER_NAME=deployer
HOST_GROUP_NAME=developers
```

### 步骤3: 创建目录结构
```bash
# 创建服务目录
mkdir -p {data,logs,config,backups,tmp}

# 设置目录权限
chown -R $USER:$(id -gn) .
chmod -R 755 .
```

### 步骤4: 修改服务配置
根据实际需求修改`docker-compose.yml`文件：
- 更新镜像名称
- 修改服务名称
- 调整端口映射
- 配置环境变量

### 步骤5: 启动服务
```bash
# 启动服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs
```

## 配置说明

### 关键配置项

#### 用户映射
```yaml
user: "${HOST_USER_ID}:${HOST_GROUP_ID}"
```
这是核心配置，将容器内用户映射到宿主机用户组。

#### 卷挂载
```yaml
volumes:
  - ./data:/var/lib/your-service:rw
  - ./logs:/var/log/your-service:rw
  - ./config:/etc/your-service:ro
```
标准化的目录结构，便于权限管理。

#### 环境变量
```yaml
environment:
  - USER_ID=${HOST_USER_ID}
  - GROUP_ID=${HOST_GROUP_ID}
```
可选配置，将用户信息传递到容器内。

### 目录结构
```
your-service/
├── docker-compose.yml    # Docker Compose配置
├── .env                  # 环境变量配置
├── data/                 # 数据目录
├── logs/                 # 日志目录
├── config/               # 配置目录
├── backups/              # 备份目录
└── tmp/                  # 临时目录
```

## 不同服务的配置示例

### MySQL服务
```yaml
services:
  mysql:
    image: mysql:8.0
    user: "${HOST_USER_ID}:${HOST_GROUP_ID}"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: ${MYSQL_DATABASE}
    volumes:
      - ./data:/var/lib/mysql:rw
      - ./logs:/var/log/mysql:rw
      - ./config:/etc/mysql/conf.d:ro
```

### Nginx服务
```yaml
services:
  nginx:
    image: nginx:alpine
    user: "${HOST_USER_ID}:${HOST_GROUP_ID}"
    volumes:
      - ./config:/etc/nginx/conf.d:ro
      - ./logs:/var/log/nginx:rw
      - ./data:/usr/share/nginx/html:rw
```

### Node.js服务
```yaml
services:
  nodejs:
    image: node:18-alpine
    user: "${HOST_USER_ID}:${HOST_GROUP_ID}"
    volumes:
      - ./data:/app/data:rw
      - ./logs:/app/logs:rw
      - ./config:/app/config:ro
```

## 常见问题

### Q1: 如何获取宿主机用户信息？
```bash
# 运行id命令
id

# 输出示例: uid=1001(deployer) gid=1002(developers) groups=1002(developers)
# 对应配置: HOST_USER_ID=1001, HOST_GROUP_ID=1002
```

### Q2: 容器启动失败怎么办？
1. 检查用户ID和组ID是否正确
2. 验证目录权限设置
3. 查看容器日志: `docker compose logs`

### Q3: 如何验证权限配置？
```bash
# 进入容器检查用户信息
docker compose exec your-service id

# 检查文件访问权限
docker compose exec your-service ls -la /var/lib/your-service
```

## 最佳实践

### 1. 配置管理
- 使用环境变量管理用户映射
- 保持配置文件的简洁性
- 文档化配置说明

### 2. 权限管理
- 最小权限原则
- 定期验证权限配置
- 避免使用root用户

### 3. 维护管理
- 统一的服务部署流程
- 标准化的目录结构
- 完整的配置文档

## 注意事项

1. **用户ID映射**: 确保宿主机用户ID和组ID配置正确
2. **目录权限**: 确保宿主机目录具有适当的权限
3. **服务配置**: 根据实际需求修改服务配置
4. **环境变量**: 正确设置所有必要的环境变量
5. **网络配置**: 根据需要配置网络设置

## 相关文档

- [权限管理指南](../docs/docker-compose-permissions-guide.md)
- [手动操作指导](../docs/manual-operations.md)
- [测试验证指南](../docs/testing-guide.md)
- [MySQL服务示例](../mysql/README.md)
