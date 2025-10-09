# Docker Compose 通用权限管理指南

**版本**: v2.1.0
**日期**: 2024-01-15
**作者**: auh1@mail.com

## 概述

本指南提供了一套完整的Docker Compose权限管理方案，适用于任何服务的部署。提供了多种部署方案，包括使用当前登录用户部署和创建专用应用用户部署。核心思想是**将容器内用户映射到宿主机用户组**，通过Docker Compose配置文件实现权限管理，减少脚本依赖，提高配置的可维护性。

## 设计原则

### 1. 通用性原则
- 适用于任何Docker服务部署
- 不依赖特定的镜像或服务
- 可复用的配置模板

### 2. 简化原则
- 优先使用Docker Compose配置文件
- 最小化脚本依赖
- 便于阅读和维护

### 3. 权限映射原则
- 容器内用户映射到宿主机用户组
- 利用宿主机用户组的现有权限
- 避免复杂的用户创建和权限设置

## 部署方案

本指南提供两种主要的部署方案，适用于不同的使用场景：

### 方案一：使用当前登录用户部署（推荐用于开发环境）

适用于开发环境或单用户部署场景，使用当前登录用户的权限部署服务。

### 方案二：创建专用应用用户部署（推荐用于生产环境）

适用于生产环境或多用户协作场景，为每个服务创建专用的用户和用户组。

## 方案一：使用当前登录用户部署

### 方案概述
通过Docker Compose的`user`配置，将容器内用户映射到当前登录用户的用户组，实现权限统一管理。

### 配置模板
```yaml
services:
  service-name:
    image: your-image:tag
    # 关键配置：用户映射到当前登录用户组
    user: "${HOST_USER_ID}:${HOST_GROUP_ID}"
    volumes:
      - ./data:/container/data:rw
      - ./logs:/container/logs:rw
      - ./config:/container/config:ro
    environment:
      # 可选：设置容器内用户环境变量
      - USER_ID=${HOST_USER_ID}
      - GROUP_ID=${HOST_GROUP_ID}
```

### 环境变量配置
```bash
# .env 文件
HOST_USER_ID=1006          # 宿主机用户ID(根据实际查看用户信息决定)
HOST_GROUP_ID=2001         # 宿主机用户组ID
HOST_USER_NAME=deployer    # 宿主机用户名(默认部署专用用户，不可登录)
HOST_GROUP_NAME=developers # 宿主机用户组名
```

## 方案二：创建专用应用用户部署

### 方案概述
为每个服务创建专用的用户和用户组，通过Docker Compose的`user`配置，将容器内用户映射到专用应用用户组，实现服务隔离和权限管理。

### 配置模板
```yaml
services:
  service-name:
    image: your-image:tag
    # 关键配置：用户映射到专用应用用户组
    user: "${SERVICE_USER_ID}:${SERVICE_GROUP_ID}"
    volumes:
      - ./data:/container/data:rw
      - ./logs:/container/logs:rw
      - ./config:/container/config:ro
      # 外部目录挂载示例
      - /var/log/service:/var/log/service:rw
    environment:
      # 可选：设置容器内用户环境变量
      - USER_ID=${SERVICE_USER_ID}
      - GROUP_ID=${SERVICE_GROUP_ID}
```

### 环境变量配置
```bash
# .env 文件
# 专用应用用户信息
SERVICE_USER_ID=999        # 应用用户ID (如mysql:999, nginx:101)
SERVICE_GROUP_ID=999       # 应用用户组ID
SERVICE_USER_NAME=mysql    # 应用用户名
SERVICE_GROUP_NAME=mysql   # 应用用户组名

# 当前登录用户信息（用于管理权限）
HOST_USER_ID=1006          # 当前登录用户ID
HOST_GROUP_ID=2001         # 当前登录用户组ID
HOST_USER_NAME=deployer    # 当前登录用户名
HOST_GROUP_NAME=developers # 当前登录用户组名
```

## 方案一实施步骤

### 步骤1: 获取当前登录用户信息
```bash
# 获取当前用户ID和组ID
id

# 输出示例: uid=1001(deployer) gid=1002(developers) groups=1002(developers)
# 记录: HOST_USER_ID=1001, HOST_GROUP_ID=1002

# 获取制定部署用户(deployer)ID和组ID
id deployer
# 输出示例：uid=1006(deployer) gid=2001(developers) 组=2001(developers)
# 记录：  HOST_USER_ID=1006, HOST_GROUP_ID=2001
```

### 步骤2: 创建目录结构
```bash
# 创建服务目录
mkdir -p /opt/docker-apps/your-service/{data,logs,config,backups}

id $UERR
# 输出示例：uid=1004(deployer) gid=1004(readonly) 组=1004(readonly),1002(developers)

# 根据实际权限选择，主组或对应权限次组
# 示例中，developers 为具体权限组

# 设置目录权限（使用当前登录用户组）
chown -R deployer:developers /opt/docker-apps/your-service
chmod -R 755 /opt/docker-apps/your-service
```

### 步骤3: 配置Docker Compose文件
使用方案一的配置模板，设置正确的用户映射。

### 步骤4: 启动服务
```bash
docker compose up -d
```

## 方案二实施步骤

### 步骤1: 创建专用应用用户和用户组

#### 创建MySQL服务用户示例
```bash
# 1. 创建mysql用户组（999为docker部署mysql,其容器内默认运行的用户和用户组）
# 如：gid为其他， exp: gid=2999。 则需要修改配置文件，映射用户
sudo groupadd -g 999 mysql

# 2. 创建mysql用户
sudo useradd -r -g mysql -u 999 -d /var/lib/mysql -s /bin/false mysql

# 3. 验证用户创建
id mysql
# 输出示例: uid=999(mysql) gid=999(mysql) groups=999(mysql)
```

#### 创建Nginx服务用户示例
```bash
# 1. 创建nginx用户组
sudo groupadd -g 101 nginx

# 2. 创建nginx用户
sudo useradd -r -g nginx -u 101 -d /var/cache/nginx -s /bin/false nginx

# 3. 验证用户创建
id nginx
# 输出示例: uid=101(nginx) gid=101(nginx) groups=101(nginx)
```

### 步骤2: 设置服务目录权限

#### 设置应用目录权限
```bash
# 创建服务目录
sudo mkdir -p /opt/docker-apps/mysql/{data,logs,config,backups}

# 设置目录所有权为应用用户
sudo chown -R mysql:mysql /opt/docker-apps/mysql

# 设置目录权限（组可写）
sudo chmod -R 775 /opt/docker-apps/mysql

# 验证权限设置
ls -la /opt/docker-apps/mysql/
```

#### 设置外部目录权限（如/var/log/mysql）
```bash
# 1. 检查当前登录用户是否有/var/log目录权限
ls -la /var/log/

# 2. 创建mysql日志目录
sudo mkdir -p /var/log/mysql

# 3. 设置目录所有权
sudo chown -R mysql:mysql /var/log/mysql

# 4. 设置目录权限
sudo chmod -R 755 /var/log/mysql

# 5. 使用ACL为当前登录用户组添加管理权限
sudo setfacl -R -m g:developers:rwx /var/log/mysql
sudo setfacl -R -d -m g:developers:rwx /var/log/mysql

# 6. 验证ACL权限
getfacl /var/log/mysql
```

### 步骤3: 配置Docker Compose文件
使用方案二的配置模板，设置正确的用户映射。

### 步骤4: 启动服务
```bash
docker compose up -d
```

## 多用户协作权限管理

### 添加开发者到应用用户组
```bash
# 将开发者用户添加到mysql组
sudo usermod -aG mysql dev1
sudo usermod -aG mysql dev2

# 验证用户组成员
groups dev1
groups dev2
```

### 使用ACL进行精细权限控制
```bash
# 为特定开发者用户设置权限
sudo setfacl -R -m u:dev1:rwx /opt/docker-apps/mysql
sudo setfacl -R -m u:dev2:rwx /opt/docker-apps/mysql

# 设置默认ACL（新创建的文件继承权限）
sudo setfacl -R -d -m u:dev1:rwx /opt/docker-apps/mysql
sudo setfacl -R -d -m u:dev2:rwx /opt/docker-apps/mysql

# 验证ACL权限
getfacl /opt/docker-apps/mysql
```

## 不同服务的用户映射参考

### 数据库服务
| 服务       | 默认用户 | 默认UID | 方案一映射     | 方案二映射        |
| ---------- | -------- | ------- | -------------- | ----------------- |
| MySQL      | mysql    | 999     | 当前登录用户组 | mysql:mysql       |
| PostgreSQL | postgres | 999     | 当前登录用户组 | postgres:postgres |
| Redis      | redis    | 999     | 当前登录用户组 | redis:redis       |
| MongoDB    | mongodb  | 999     | 当前登录用户组 | mongodb:mongodb   |

### Web服务
| 服务    | 默认用户 | 默认UID | 方案一映射     | 方案二映射        |
| ------- | -------- | ------- | -------------- | ----------------- |
| Nginx   | nginx    | 101     | 当前登录用户组 | nginx:nginx       |
| Apache  | www-data | 33      | 当前登录用户组 | www-data:www-data |
| Node.js | node     | 1000    | 当前登录用户组 | node:node         |

## 外部目录权限管理

### 常见外部目录挂载场景

#### MySQL日志目录
```bash
# 挂载到/var/log/mysql
volumes:
  - /var/log/mysql:/var/log/mysql:rw
```

#### Nginx日志目录
```bash
# 挂载到/var/log/nginx
volumes:
  - /var/log/nginx:/var/log/nginx:rw
```

#### 系统配置文件目录
```bash
# 挂载到/etc/nginx
volumes:
  - /etc/nginx:/etc/nginx:ro
```

### 外部目录权限设置步骤

#### 1. 检查当前用户权限
```bash
# 检查当前登录用户是否有目标目录权限
ls -la /var/log/
ls -la /etc/

# 检查当前用户组
groups $USER
```

#### 2. 创建外部目录
```bash
# 创建外部目录
sudo mkdir -p /var/log/mysql
sudo mkdir -p /var/log/nginx
sudo mkdir -p /etc/nginx
```

#### 3. 设置目录权限
```bash
# 设置目录所有权
sudo chown -R mysql:mysql /var/log/mysql
sudo chown -R nginx:nginx /var/log/nginx
sudo chown -R nginx:nginx /etc/nginx

# 设置目录权限
sudo chmod -R 755 /var/log/mysql
sudo chmod -R 755 /var/log/nginx
sudo chmod -R 755 /etc/nginx
```

#### 4. 使用ACL设置管理权限
```bash
# 为developers组添加管理权限
sudo setfacl -R -m g:developers:rwx /var/log/mysql
sudo setfacl -R -m g:developers:rwx /var/log/nginx
sudo setfacl -R -m g:developers:rwx /etc/nginx

# 设置默认ACL
sudo setfacl -R -d -m g:developers:rwx /var/log/mysql
sudo setfacl -R -d -m g:developers:rwx /var/log/nginx
sudo setfacl -R -d -m g:developers:rwx /etc/nginx

# 验证ACL权限
getfacl /var/log/mysql
getfacl /var/log/nginx
getfacl /etc/nginx
```

## 完整配置示例

### MySQL服务完整配置示例

#### docker-compose.yml
```yaml
version: '3.8'

services:
  mysql:
    image: mysql:5.7.44
    container_name: mysql
    # 方案二：使用专用应用用户
    user: "999:999"  # mysql:mysql
    environment:
      # 传递用户信息到容器内
      - USER_ID=999
      - GROUP_ID=999
      - USER_NAME=mysql
      - GROUP_NAME=mysql

      # MySQL 配置
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_USER=${MYSQL_USER}
      - MYSQL_PASSWORD=${MYSQL_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}

      # 系统配置
      - TZ=Asia/Shanghai
    ports:
      - "${MYSQL_PORT:-3306}:3306"
    volumes:
      # 应用目录挂载
      - ./data:/var/lib/mysql:rw
      - ./logs:/var/log/mysql:rw
      - ./config:/etc/mysql/conf.d:ro
      - ./backups:/backups:rw
      # 外部目录挂载
      - /var/log/mysql:/var/log/mysql:rw
    restart: unless-stopped
    networks:
      - mysql-network

networks:
  mysql-network:
    driver: bridge
```

#### .env文件
```bash
# 应用用户信息（方案二）
SERVICE_USER_ID=999
SERVICE_GROUP_ID=999
SERVICE_USER_NAME=mysql
SERVICE_GROUP_NAME=mysql

# 当前登录用户信息（用于管理权限）
HOST_USER_ID=1006
HOST_GROUP_ID=2001
HOST_USER_NAME=deployer
HOST_GROUP_NAME=developers

# MySQL 配置
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_USER=app
MYSQL_PASSWORD=your_app_password
MYSQL_DATABASE=app_db
MYSQL_PORT=3306

# 系统配置
TZ=Asia/Shanghai
```

## 常见问题与解决方案

### 问题1: 容器启动失败
**错误**: `container failed to start`

**原因**: 用户映射配置错误

**解决方案**:
1. 检查用户ID和组ID是否正确
2. 验证目录权限设置
3. 查看容器日志: `docker compose logs`

### 问题2: 文件权限错误
**错误**: `Permission denied`

**原因**: 容器内用户无法访问挂载目录

**解决方案**:
1. 确认用户映射配置
2. 检查宿主机目录权限
3. 验证用户组设置

### 问题3: 外部目录访问权限错误
**错误**: `Can't create/write to file '/var/log/mysql/error.log' (Permission denied)`

**原因**: 外部目录权限配置不当

**解决方案**:
1. 检查外部目录权限: `ls -la /var/log/mysql/`
2. 设置正确的目录所有权: `sudo chown -R mysql:mysql /var/log/mysql`
3. 使用ACL设置管理权限: `sudo setfacl -R -m g:developers:rwx /var/log/mysql`

### 问题4: 多用户协作权限问题
**错误**: 开发者用户无法管理服务目录

**原因**: 用户组权限配置不完整

**解决方案**:
1. 将开发者添加到应用用户组: `sudo usermod -aG mysql dev1`
2. 使用ACL设置精细权限: `sudo setfacl -R -m u:dev1:rwx /opt/docker-apps/mysql`
3. 验证用户组成员: `groups dev1`

### 问题5: ACL权限不生效
**错误**: ACL设置后权限仍然不正确

**原因**: 文件系统不支持ACL或ACL配置错误

**解决方案**:
1. 检查文件系统ACL支持: `mount | grep acl`
2. 重新挂载文件系统启用ACL: `sudo mount -o remount,acl /`
3. 验证ACL权限: `getfacl /path/to/directory`

### 问题6: 服务功能异常
**错误**: 服务无法正常读写文件

**原因**: 权限配置不完整

**解决方案**:
1. 检查所有挂载点的权限
2. 验证容器内用户环境
3. 测试文件访问权限

## 最佳实践

### 1. 方案选择
- **开发环境**: 推荐使用方案一（当前登录用户部署）
- **生产环境**: 推荐使用方案二（专用应用用户部署）
- **多用户协作**: 必须使用方案二配合ACL权限控制

### 2. 配置管理
- 使用环境变量管理用户映射
- 保持配置文件的简洁性
- 文档化配置说明
- 版本控制配置文件

### 3. 权限管理
- 最小权限原则
- 定期验证权限配置
- 避免使用root用户
- 使用ACL进行精细权限控制

### 4. 维护管理
- 统一的服务部署流程
- 标准化的目录结构
- 完整的配置文档
- 定期权限审计

### 5. 安全考虑
- 服务用户不可登录（/bin/false）
- 外部目录权限最小化
- 定期检查ACL权限配置
- 监控权限变更

## 部署检查清单

### 方案一部署检查清单

#### 部署前检查
- [ ] 获取当前登录用户信息
- [ ] 创建标准目录结构
- [ ] 配置Docker Compose文件
- [ ] 设置环境变量

#### 部署后验证
- [ ] 容器正常启动
- [ ] 服务功能正常
- [ ] 文件访问权限正确
- [ ] 日志输出正常

### 方案二部署检查清单

#### 部署前检查
- [ ] 创建专用应用用户和用户组
- [ ] 设置应用目录权限
- [ ] 设置外部目录权限
- [ ] 配置ACL权限
- [ ] 配置Docker Compose文件
- [ ] 设置环境变量

#### 部署后验证
- [ ] 容器正常启动
- [ ] 服务功能正常
- [ ] 应用目录访问权限正确
- [ ] 外部目录访问权限正确
- [ ] 多用户协作权限正确
- [ ] 日志输出正常

## 自动化脚本

### 权限设置脚本
```bash
#!/bin/bash
# setup_service_permissions.sh

SERVICE_NAME="${1:-mysql}"
SERVICE_USER="${2:-mysql}"
SERVICE_GROUP="${3:-mysql}"
SERVICE_UID="${4:-999}"
SERVICE_GID="${5:-999}"

# 创建应用用户和组
sudo groupadd -g "$SERVICE_GID" "$SERVICE_GROUP" 2>/dev/null || true
sudo useradd -r -g "$SERVICE_GROUP" -u "$SERVICE_UID" -d "/var/lib/$SERVICE_NAME" -s /bin/false "$SERVICE_USER" 2>/dev/null || true

# 创建目录结构
sudo mkdir -p "/opt/docker-apps/$SERVICE_NAME"/{data,logs,config,backups}

# 设置目录权限
sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "/opt/docker-apps/$SERVICE_NAME"
sudo chmod -R 775 "/opt/docker-apps/$SERVICE_NAME"

# 设置外部目录权限（如果存在）
if [[ -d "/var/log/$SERVICE_NAME" ]]; then
    sudo chown -R "$SERVICE_USER:$SERVICE_GROUP" "/var/log/$SERVICE_NAME"
    sudo chmod -R 755 "/var/log/$SERVICE_NAME"
    sudo setfacl -R -m g:developers:rwx "/var/log/$SERVICE_NAME"
    sudo setfacl -R -d -m g:developers:rwx "/var/log/$SERVICE_NAME"
fi

echo "权限设置完成: $SERVICE_NAME"
```

### 使用示例
```bash
# 设置MySQL服务权限
./setup_service_permissions.sh mysql mysql mysql 999 999

# 设置Nginx服务权限
./setup_service_permissions.sh nginx nginx nginx 101 101
```

## 相关文件

- `examples/universal/docker-compose.yml` - 通用配置模板
- `examples/mysql/docker-compose.yml` - MySQL服务示例
- `docs/manual-operations.md` - 手动操作指导
- `docs/testing-guide.md` - 测试验证指南

## 更新日志

### v2.1.0 (2024-01-15)
- 新增两种部署方案：当前登录用户部署和专用应用用户部署
- 新增外部目录权限管理指南
- 新增ACL权限控制说明
- 新增多用户协作权限管理
- 完善常见问题解决方案
- 新增自动化脚本示例

### v2.0.0 (2024-01-10)
- 重新设计为通用权限管理方案
- 支持任何Docker服务的部署
- 简化配置，减少脚本依赖
- 提供通用配置模板
- 完善文档和示例

---

**联系方式**: auh1@mail.com
**最后更新**: 2024-01-15
