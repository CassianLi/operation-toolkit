# Ansible（ASL）

合并后的唯一 Ansible 工程：普通用户组/账户与 root 权限用户。

## 本地准备

```bash
cp inventory/hosts.yml.example inventory/hosts.yml   # 填入本地域名与密钥路径
cp vars/users.yml.example vars/users.yml             # 按需
cp vars/groups.yml.example vars/groups.yml
cp vars/root_users.yml.example vars/root_users.yml
cp vars/ssh_keys.yml.example vars/ssh_keys.yml
```

敏感实配文件已 gitignore，勿提交。

## 推荐入口

在仓库根目录：

```bash
make help
make ping TARGET_ENV=dev
make users TARGET_ENV=dev
make root-users TARGET_ENV=pro
```

详情见 [docs/tech/ansible.md](../../docs/tech/ansible.md)。
