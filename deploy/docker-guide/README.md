# Docker Compose 通用权限管理指南

## 项目概述

本项目提供了一套通用的Docker Compose权限管理方案，适用于任何服务的部署。核心思想是**将容器内用户映射到宿主机用户组**，通过Docker Compose配置文件实现权限管理，减少脚本依赖，提高配置的可维护性。

## 项目结构

```
deploy/docker-guide/
├── docs/                           # 文档目录
│   ├── docker-compose-permissions-guide.md  # 通用权限管理指南
│   ├── manual-operations.md        # 手动操作指导
│   └── testing-guide.md            # 测试验证指南
├── examples/                       # 示例配置
│   ├── universal/                  # 通用配置模板
│   │   ├── docker-compose.yml      # 通用Docker Compose模板
│   │   ├── env.example             # 通用环境变量模板
│   │   └── README.md               # 通用模板说明
│   └── mysql/                      # MySQL 服务示例
│       ├── docker-compose.yml      # MySQL Docker Compose 配置
│       ├── env.example             # MySQL 环境变量示例
│       ├── config/                 # 配置文件目录
│       │   └── my.cnf              # MySQL 配置文件
│       └── README.md               # MySQL 服务说明
├── scripts/                        # 脚本目录
│   ├── setup-directories.sh        # 通用目录权限设置脚本
│   └── verify-permissions.sh       # 通用权限验证脚本
└── README.md                       # 项目说明文档
```

## 快速开始

### 1. 环境准备

确保您的系统满足以下要求：
- Linux 系统 (Ubuntu 20.04+ / CentOS 7+)
- Docker Engine 20.10+
- Docker Compose 2.0+
- 部署用户具有适当的权限

### 2. 获取用户信息

```bash
# 获取当前用户信息
id

# 输出示例: uid=1001(deployer) gid=1002(developers) groups=1002(developers)
# 记录: HOST_USER_ID=1001, HOST_GROUP_ID=1002
```

### 3. 使用通用模板部署服务

```bash
# 复制通用模板
cp examples/universal/docker-compose.yml /opt/docker-apps/your-service/
cp examples/universal/env.example /opt/docker-apps/your-service/.env

# 编辑环境变量
nano /opt/docker-apps/your-service/.env

# 设置必要的用户信息
HOST_USER_ID=1001
HOST_GROUP_ID=1002
HOST_USER_NAME=deployer
HOST_GROUP_NAME=developers

# 创建目录结构
mkdir -p /opt/docker-apps/your-service/{data,logs,config,backups,tmp}

# 设置目录权限
chown -R $USER:$(id -gn) /opt/docker-apps/your-service
chmod -R 755 /opt/docker-apps/your-service

# 启动服务
cd /opt/docker-apps/your-service
docker compose up -d
```

### 4. 验证部署

```bash
# 运行权限验证脚本
cd deploy/docker-guide/scripts
./verify-permissions.sh your-service

# 检查服务状态
docker compose ps

# 查看日志
docker compose logs
```

## 核心特性

### 1. 通用性
- 适用于任何Docker服务部署
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

### 4. 标准化
- 统一的目录结构
- 标准化的配置格式
- 完整的文档说明

## 使用场景

### 场景1: 新服务部署
适用于部署任何新的Docker服务。

**步骤**:
1. 使用通用模板创建配置
2. 设置环境变量
3. 创建目录结构
4. 启动服务并验证

### 场景2: 权限问题排查
当遇到权限相关错误时，使用验证脚本快速定位问题。

**步骤**:
1. 运行 `verify-permissions.sh` 检查权限配置
2. 根据错误信息调整权限设置
3. 重新验证配置

### 场景3: 生产环境部署
在生产环境部署前，先在测试环境验证配置。

**步骤**:
1. 在测试环境完成所有测试
2. 记录测试结果和问题
3. 在生产环境应用相同的配置
4. 进行生产环境验证

## 配置说明

### 核心配置

#### 用户映射配置
```yaml
user: "${HOST_USER_ID}:${HOST_GROUP_ID}"
```
这是核心配置，将容器内用户映射到宿主机用户组。

#### 环境变量配置
```bash
HOST_USER_ID=1001          # 宿主机用户ID
HOST_GROUP_ID=1002         # 宿主机用户组ID
HOST_USER_NAME=deployer    # 宿主机用户名
HOST_GROUP_NAME=developers # 宿主机用户组名
```

### 目录权限配置

| 目录                                  | 权限 | 所有者 | 用户组    | 说明     |
| ------------------------------------- | ---- | ------ | --------- | -------- |
| /opt/docker-apps                      | 755  | $USER  | $(id -gn) | 主目录   |
| /opt/docker-apps/your-service         | 755  | $USER  | $(id -gn) | 服务目录 |
| /opt/docker-apps/your-service/data    | 755  | $USER  | $(id -gn) | 数据目录 |
| /opt/docker-apps/your-service/logs    | 755  | $USER  | $(id -gn) | 日志目录 |
| /opt/docker-apps/your-service/config  | 755  | $USER  | $(id -gn) | 配置目录 |
| /opt/docker-apps/your-service/backups | 755  | $USER  | $(id -gn) | 备份目录 |

### 不同服务的用户映射参考

| 服务       | 默认用户 | 默认UID | 推荐映射     |
| ---------- | -------- | ------- | ------------ |
| MySQL      | mysql    | 999     | 宿主机用户组 |
| PostgreSQL | postgres | 999     | 宿主机用户组 |
| Redis      | redis    | 999     | 宿主机用户组 |
| Nginx      | nginx    | 101     | 宿主机用户组 |
| Node.js    | node     | 1000    | 宿主机用户组 |

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
4. 检查环境变量配置

### Q3: 如何验证权限配置？
```bash
# 进入容器检查用户信息
docker compose exec your-service id

# 检查文件访问权限
docker compose exec your-service ls -la /var/lib/your-service
```

### Q4: 权限拒绝错误怎么解决？
1. 检查目录权限: `ls -la /opt/docker-apps/your-service/`
2. 重新设置权限: `sudo chown -R $USER:$(id -gn) /opt/docker-apps/your-service/`
3. 检查用户组: `groups`

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

### 4. 安全考虑
- 使用非特权用户运行容器
- 限制敏感目录的访问
- 定期审查权限配置

## 贡献指南

### 报告问题
如果您发现问题或有改进建议，请：
1. 检查现有文档和常见问题
2. 提供详细的错误信息和环境信息
3. 描述复现步骤

### 提交改进
欢迎提交改进建议：
1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 许可证

本项目采用 MIT 许可证。详情请参阅 LICENSE 文件。

## 相关文件

- `examples/universal/` - 通用配置模板
- `examples/mysql/` - MySQL 服务配置示例
- `scripts/setup-directories.sh` - 通用目录权限设置脚本
- `scripts/verify-permissions.sh` - 通用权限验证脚本
- `docs/docker-compose-permissions-guide.md` - 通用权限管理指南
- `docs/manual-operations.md` - 手动操作指导
- `docs/testing-guide.md` - 测试验证指南

## 更新日志

### v2.0.0 (2024-01-XX)
- 重新设计为通用权限管理方案
- 支持任何Docker服务的部署
- 简化配置，减少脚本依赖
- 提供通用配置模板
- 完善文档和示例

## 联系方式

如有问题或建议，请通过以下方式联系：
- 创建 Issue
- 发送邮件
- 参与讨论

---

**注意**: 在生产环境使用前，请务必在测试环境完成所有测试，确保配置的正确性和稳定性。
