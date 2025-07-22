#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux登录用户权限管理脚本
功能：创建登录用户、系统权限管理、ACL控制、sudo配置等
说明：此脚本专门用于管理登录用户权限，不涉及应用程序运行权限
作者：User Manager Script
版本：2.0
"""

import os
import sys
import json
import logging
import subprocess
import getpass
from datetime import datetime
from pathlib import Path

# 新增：导入argparse
import argparse

# 新增：导入yaml
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


# 依赖检查和安装
def check_and_install_dependencies():
    """检查并安装依赖"""
    print("🔍 检查系统依赖...")

    # 检查系统依赖
    system_deps = {
        "setfacl": "acl",
        "visudo": "sudo",
        "useradd": "shadow-utils",
        "groupadd": "shadow-utils",
    }

    missing_system_deps = []
    for cmd, package in system_deps.items():
        try:
            subprocess.run(
                ["which", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            print(f"✅ {cmd} 已安装")
        except subprocess.CalledProcessError:
            missing_system_deps.append((cmd, package))
            print(f"❌ {cmd} 未安装")

    if missing_system_deps:
        print(f"\n⚠️  发现缺失的系统依赖:")
        for cmd, package in missing_system_deps:
            print(f"   - {cmd} (包: {package})")

        print(f"\n请运行以下命令安装系统依赖:")

        # 检测系统类型并提供相应的安装命令
        try:
            # 检查是否是Ubuntu/Debian系统
            subprocess.run(
                ["which", "apt"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
            packages = " ".join([pkg for _, pkg in missing_system_deps])
            print(f"sudo apt-get update && sudo apt-get install -y {packages}")
        except subprocess.CalledProcessError:
            try:
                # 检查是否是CentOS/RHEL系统
                subprocess.run(
                    ["which", "yum"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=True,
                )
                packages = " ".join([pkg for _, pkg in missing_system_deps])
                print(f"sudo yum install -y {packages}")
            except subprocess.CalledProcessError:
                try:
                    # 检查是否是较新的CentOS/RHEL系统
                    subprocess.run(
                        ["which", "dnf"],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        check=True,
                    )
                    packages = " ".join([pkg for _, pkg in missing_system_deps])
                    print(f"sudo dnf install -y {packages}")
                except subprocess.CalledProcessError:
                    print("请根据您的系统类型手动安装上述软件包")

        print("\n安装完成后请重新运行此脚本")
        sys.exit(1)

    # 检查Python依赖
    print("\n🐍 检查Python依赖...")

    python_deps = ["colorama"]
    missing_python_deps = []

    for dep in python_deps:
        try:
            __import__(dep)
            print(f"✅ {dep} 已安装")
        except ImportError:
            missing_python_deps.append(dep)
            print(f"❌ {dep} 未安装")

    if missing_python_deps:
        print(f"\n⚠️  发现缺失的Python依赖: {', '.join(missing_python_deps)}")

        # 询问是否自动安装
        auto_install = input("是否自动安装Python依赖？[Y/n]: ").strip().lower()
        if auto_install != "n" and auto_install != "no":
            try:
                print("正在安装Python依赖...")
                for dep in missing_python_deps:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", dep], check=True
                    )
                    print(f"✅ {dep} 安装成功")
                print("所有Python依赖安装完成")
            except subprocess.CalledProcessError as e:
                print(f"❌ 自动安装失败: {e}")
                print("请手动运行以下命令安装:")
                print(f"pip install {' '.join(missing_python_deps)}")
                print("或者:")
                print("pip install -r requirements.txt")
                sys.exit(1)
        else:
            print("请手动安装Python依赖:")
            print(f"pip install {' '.join(missing_python_deps)}")
            print("或者:")
            print("pip install -r requirements.txt")
            sys.exit(1)

    print("✅ 所有依赖检查完成")


# 尝试导入colorama用于彩色输出
try:
    from colorama import init, Fore, Style, Back

    init(autoreset=True)
    COLORS_AVAILABLE = True
except ImportError:
    COLORS_AVAILABLE = False

    # 如果没有colorama，定义空的颜色常量
    class Fore:
        RED = GREEN = YELLOW = CYAN = BLUE = MAGENTA = WHITE = ""

    class Style:
        RESET_ALL = BRIGHT = ""

    class Back:
        RED = GREEN = YELLOW = ""


class Config:
    """配置管理类"""

    # 用户组配置 - 专门用于登录用户权限管理
    GROUP_CONFIGS = {
        "developers": {
            "name": "开发人员",
            "description": "开发人员用户组，拥有代码开发和调试权限",
            "directories": {
                "/usr/local/src": {"name": "源码目录", "default": "write"},
                "/opt": {"name": "第三方软件目录", "default": "read"},
                "/var/log": {"name": "系统日志目录", "default": "read"},
                "/tmp": {"name": "临时目录", "default": "write"},
            },
            "sudo_commands": [
                "/bin/systemctl status *",
                "/bin/systemctl restart *",
                "/bin/systemctl stop *",
                "/bin/systemctl start *",
                "/bin/top",
                "/bin/htop",
                "/bin/ps",
                "/bin/kill",
                "/bin/killall",
                "/usr/bin/tail",
                "/bin/less",
                "/bin/cat",
                "/bin/grep",
                "/bin/find",
                "/bin/ls",
                "/bin/dmesg",
                "/bin/journalctl",
                "/usr/bin/lsof",
                "/bin/netstat",
                "/bin/ss",
                "/bin/mount",
                "/bin/umount",
                "/usr/bin/docker",
                "/usr/local/bin/docker-compose",
                "/usr/bin/docker-compose",
                "/usr/bin/dnf",
            ],
        },
        "operations": {
            "name": "运维人员",
            "description": "运维人员用户组，拥有系统管理和维护权限",
            "directories": {
                "/usr/local/src": {"name": "源码目录", "default": "write"},
                "/opt": {"name": "第三方软件目录", "default": "write"},
                "/var/log": {"name": "系统日志目录", "default": "write"},
                "/etc": {"name": "系统配置目录", "default": "read"},
                "/etc/yum.repos.d": {"name": "YUM源配置目录", "default": "write"},
                "/etc/docker": {"name": "Docker配置目录", "default": "write"},
                "/tmp": {"name": "临时目录", "default": "write"},
                "/data": {"name": "数据目录", "default": "write"},
                "/backup": {"name": "备份目录", "default": "write"},
            },
            "sudo_commands": [
                "/bin/systemctl",
                "/usr/bin/service",
                "/sbin/iptables",
                "/sbin/ufw",
                "/bin/mount",
                "/bin/umount",
                "/sbin/fdisk",
                "/sbin/parted",
                "/bin/top",
                "/bin/htop",
                "/bin/ps",
                "/bin/kill",
                "/bin/killall",
                "/usr/bin/tail",
                "/bin/less",
                "/bin/cat",
                "/bin/grep",
                "/bin/find",
                "/bin/ls",
                "/bin/dmesg",
                "/bin/journalctl",
                "/usr/bin/lsof",
                "/bin/netstat",
                "/bin/ss",
                "/bin/crontab",
                "/usr/bin/rsync",
                "/bin/tar",
                "/bin/gzip",
                "/bin/gunzip",
                "/usr/bin/docker",
                "/usr/local/bin/docker-compose",
                "/usr/bin/docker-compose",
                "/usr/bin/dnf",
            ],
        },
        "security": {
            "name": "安全管理员",
            "description": "安全管理员用户组，拥有安全审计和配置权限",
            "directories": {
                "/var/log": {"name": "系统日志目录", "default": "write"},
                "/etc": {"name": "系统配置目录", "default": "read"},
                "/usr/local/src": {"name": "源码目录", "default": "read"},
                "/opt": {"name": "第三方软件目录", "default": "read"},
            },
            "sudo_commands": [
                "/bin/systemctl",
                "/sbin/iptables",
                "/sbin/ufw",
                "/usr/bin/fail2ban-client",
                "/bin/top",
                "/bin/htop",
                "/bin/ps",
                "/usr/bin/tail",
                "/bin/less",
                "/bin/cat",
                "/bin/grep",
                "/bin/find",
                "/bin/ls",
                "/bin/dmesg",
                "/bin/journalctl",
                "/usr/bin/lsof",
                "/bin/netstat",
                "/bin/ss",
                "/usr/bin/last",
                "/usr/bin/lastlog",
                "/usr/bin/who",
                "/usr/bin/w",
                "/usr/bin/id",
                "/bin/chmod",
                "/bin/chown",
                "/bin/chgrp",
            ],
        },
        "readonly": {
            "name": "只读用户",
            "description": "只读用户组，仅拥有查看权限，适用于审计和监控",
            "directories": {
                "/var/log": {"name": "系统日志目录", "default": "read"},
                "/etc": {"name": "系统配置目录", "default": "read"},
                "/usr/local/src": {"name": "源码目录", "default": "read"},
                "/opt": {"name": "第三方软件目录", "default": "read"},
            },
            "sudo_commands": [
                "/bin/systemctl status *",
                "/bin/top",
                "/bin/htop",
                "/bin/ps",
                "/usr/bin/tail",
                "/bin/less",
                "/bin/cat",
                "/bin/grep",
                "/bin/find",
                "/bin/ls",
                "/bin/dmesg",
                "/bin/journalctl",
                "/usr/bin/lsof",
                "/bin/netstat",
                "/bin/ss",
                "/usr/bin/last",
                "/usr/bin/lastlog",
                "/usr/bin/who",
                "/usr/bin/w",
                "/usr/bin/id",
            ],
        },
    }

    # 默认配置
    DEFAULT_GROUP = "developers"

    # 权限类型
    PERMISSION_TYPES = {"read": "r-x", "write": "rwx"}

    # 日志和备份目录
    LOG_DIR = Path("/var/log/user_manager")
    BACKUP_DIR = Path("/opt/user_manager_backup")


class Logger:
    """日志管理类"""

    def __init__(self):
        self.setup_logging()

    def setup_logging(self):
        """设置日志"""
        try:
            Config.LOG_DIR.mkdir(parents=True, exist_ok=True)
            log_file = (
                Config.LOG_DIR / f"user_manager_{datetime.now().strftime('%Y%m%d')}.log"
            )

            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[logging.FileHandler(log_file), logging.StreamHandler()],
            )
            self.logger = logging.getLogger(__name__)
        except Exception as e:
            print(f"警告：无法创建日志文件：{e}")
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)

    def warning(self, message):
        self.logger.warning(message)


class SystemUtils:
    """系统工具类"""

    @staticmethod
    def run_command(command, capture_output=True, check=True):
        """执行系统命令"""
        try:
            if isinstance(command, str):
                command = command.split()

            # Python 3.6兼容性：使用stdout和stderr参数替代capture_output
            if capture_output:
                result = subprocess.run(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    check=check,
                )
            else:
                result = subprocess.run(command, universal_newlines=True, check=check)
            return result
        except subprocess.CalledProcessError as e:
            stderr_msg = getattr(e, "stderr", "未知错误")
            raise Exception(f"命令执行失败：{' '.join(command)}\n错误：{stderr_msg}")
        except Exception as e:
            raise Exception(f"命令执行异常：{e}")

    @staticmethod
    def check_root():
        """检查是否为root用户"""
        return os.geteuid() == 0

    @staticmethod
    def user_exists(username):
        """检查用户是否存在"""
        try:
            result = SystemUtils.run_command(f"id {username}")
            return True
        except:
            return False

    @staticmethod
    def group_exists(groupname):
        """检查用户组是否存在"""
        try:
            result = SystemUtils.run_command(f"getent group {groupname}")
            return True
        except:
            return False

    @staticmethod
    def get_user_groups(username):
        """获取用户所属组"""
        try:
            result = SystemUtils.run_command(f"groups {username}")
            groups = result.stdout.strip().split(":")[1].strip().split()
            return groups
        except:
            return []

    @staticmethod
    def check_acl_support():
        """检查系统是否支持ACL"""
        try:
            SystemUtils.run_command("which setfacl")
            return True
        except:
            return False


class UserManager:
    """用户管理核心类"""

    def __init__(self):
        self.logger = Logger()
        if not SystemUtils.check_root():
            self.print_error("错误：此脚本需要root权限运行！")
            sys.exit(1)

        if not SystemUtils.check_acl_support():
            self.print_error("错误：系统不支持ACL，请安装acl工具包")
            sys.exit(1)

    def print_success(self, message):
        """打印成功信息"""
        if COLORS_AVAILABLE:
            print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        else:
            print(f"✅ {message}")

    def print_error(self, message):
        """打印错误信息"""
        if COLORS_AVAILABLE:
            print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
        else:
            print(f"❌ {message}")

    def print_warning(self, message):
        """打印警告信息"""
        if COLORS_AVAILABLE:
            print(f"{Fore.YELLOW}⚠️  {message}{Style.RESET_ALL}")
        else:
            print(f"⚠️ {message}")

    def print_info(self, message):
        """打印信息"""
        if COLORS_AVAILABLE:
            print(f"{Fore.CYAN}ℹ️  {message}{Style.RESET_ALL}")
        else:
            print(f"ℹ️ {message}")

    def print_header(self, title):
        """打印标题"""
        if COLORS_AVAILABLE:
            print(f"\n{Fore.BLUE}{Style.BRIGHT}{'='*60}")
            print(f"{title:^60}")
            print(f"{'='*60}{Style.RESET_ALL}\n")
        else:
            print(f"\n{'='*60}")
            print(f"{title:^60}")
            print(f"{'='*60}\n")

    def create_group_if_not_exists(self, groupname):
        """创建用户组（如果不存在）"""
        if not SystemUtils.group_exists(groupname):
            try:
                SystemUtils.run_command(f"groupadd {groupname}")
                self.print_success(f"用户组 '{groupname}' 创建成功")
                self.logger.info(f"创建用户组：{groupname}")
                return True
            except Exception as e:
                self.print_error(f"创建用户组失败：{e}")
                return False
        else:
            self.print_info(f"用户组 '{groupname}' 已存在")
            return True

    def create_user(self, username, groupname):
        """创建登录用户"""
        if SystemUtils.user_exists(username):
            self.print_error(f"用户 '{username}' 已存在！")
            return False

        try:
            # 创建用户，禁用密码登录
            cmd = [
                "useradd",
                "-m",  # 创建家目录
                "-g",
                groupname,  # 主用户组
                "-s",
                "/bin/bash",  # 默认shell
                username,
            ]
            SystemUtils.run_command(cmd)

            # 禁用密码登录
            SystemUtils.run_command(f"passwd -l {username}")

            # 创建.ssh目录
            ssh_dir = Path(f"/home/{username}/.ssh")
            ssh_dir.mkdir(mode=0o700, exist_ok=True)

            # 创建authorized_keys文件
            auth_keys = ssh_dir / "authorized_keys"
            auth_keys.touch(mode=0o600)

            # 设置所有者
            SystemUtils.run_command(
                f"chown -R {username}:{groupname} /home/{username}/.ssh"
            )

            self.print_success(f"登录用户 '{username}' 创建成功")
            self.logger.info(f"创建登录用户：{username}，组：{groupname}")
            return True

        except Exception as e:
            self.print_error(f"创建用户失败：{e}")
            return False

    def set_directory_permissions(self, username, directories_config):
        """设置目录权限"""
        success_count = 0

        for directory, permission in directories_config.items():
            try:
                # 检查目录是否存在
                if not Path(directory).exists():
                    self.print_warning(f"目录 {directory} 不存在，跳过")
                    continue

                # 设置ACL权限
                perm_str = Config.PERMISSION_TYPES[permission]
                cmd = f"setfacl -m u:{username}:{perm_str} {directory}"
                SystemUtils.run_command(cmd)

                # 设置默认ACL权限（对新建文件生效）
                if permission == "write":
                    default_cmd = f"setfacl -m d:u:{username}:{perm_str} {directory}"
                    SystemUtils.run_command(default_cmd)

                perm_desc = "读写" if permission == "write" else "只读"
                self.print_success(
                    f"为用户 '{username}' 设置目录 '{directory}' {perm_desc}权限"
                )
                self.logger.info(
                    f"设置目录权限：{username} -> {directory} ({permission})"
                )
                success_count += 1

            except Exception as e:
                self.print_error(f"设置目录 '{directory}' 权限失败：{e}")

        return success_count

    def set_sudo_permissions(self, username, groupname):
        """设置sudo权限"""
        try:
            # 获取用户组配置
            if groupname not in Config.GROUP_CONFIGS:
                self.print_error(f"未知的用户组：{groupname}")
                return False

            group_config = Config.GROUP_CONFIGS[groupname]

            # 创建sudoers文件
            sudoers_file = Path(f"/etc/sudoers.d/{groupname}")

            # 构建sudo命令列表
            commands_str = ", ".join(group_config["sudo_commands"])

            # 创建sudoers配置内容
            sudoers_content = f"""# Sudoers rules for {groupname} group ({group_config['name']})
# Created by user_manager.py on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Description: {group_config['description']}
# Note: This is for login users management, not application runtime permissions

# Allow {groupname} group to run specific system commands
%{groupname} ALL=(ALL) NOPASSWD: {commands_str}
"""

            # 写入sudoers文件
            sudoers_file.write_text(sudoers_content)
            sudoers_file.chmod(0o440)  # 设置正确的权限

            # 验证sudoers文件语法
            result = SystemUtils.run_command(f"visudo -c -f {sudoers_file}")

            self.print_success(f"为用户组 '{groupname}' 设置sudo权限成功")
            self.logger.info(f"设置sudo权限：组 {groupname}")
            return True

        except Exception as e:
            self.print_error(f"设置sudo权限失败：{e}")
            # 如果失败，删除可能创建的文件
            try:
                sudoers_file.unlink()
            except:
                pass
            return False

    def get_directory_permissions_input(self, groupname):
        """获取目录权限配置输入"""
        directories_config = {}

        # 获取用户组配置
        if groupname not in Config.GROUP_CONFIGS:
            self.print_error(f"未知的用户组：{groupname}")
            return {}

        group_config = Config.GROUP_CONFIGS[groupname]
        target_directories = group_config["directories"]

        print(
            f"\n{Fore.CYAN if COLORS_AVAILABLE else ''}📁 配置目录权限{Style.RESET_ALL if COLORS_AVAILABLE else ''}"
        )
        print(f"为 {group_config['name']} 配置以下目录权限：")

        for directory, info in target_directories.items():
            print(f"\n目录：{directory} ({info['name']})")
            print("1. 只读权限 (r-x)")
            print("2. 读写权限 (rwx)")
            print("3. 跳过此目录")

            while True:
                choice = input(f"请选择权限类型 [默认: {info['default']}]: ").strip()

                if choice == "" or choice == "2":
                    directories_config[directory] = "write"
                    break
                elif choice == "1":
                    directories_config[directory] = "read"
                    break
                elif choice == "3":
                    break
                else:
                    self.print_error("无效选择，请输入 1、2 或 3")

        return directories_config

    def get_group_selection(self):
        """获取用户组选择"""
        print(
            f"\n{Fore.YELLOW if COLORS_AVAILABLE else ''}👥 选择用户组类型{Style.RESET_ALL if COLORS_AVAILABLE else ''}"
        )

        groups = list(Config.GROUP_CONFIGS.keys())
        for i, (group_key, group_config) in enumerate(Config.GROUP_CONFIGS.items(), 1):
            print(f"{i}. {group_config['name']} ({group_key})")
            print(f"   {group_config['description']}")
        print(f"{len(groups)+1}. 自定义组（自行管理）/ Custom group (manual)")
        while True:
            try:
                choice = input(f"\n请选择用户组 [1-{len(groups)+1}]: ").strip()
                if choice == "":
                    # 默认选择开发人员组
                    return Config.DEFAULT_GROUP
                choice_num = int(choice)
                if 1 <= choice_num <= len(groups):
                    selected_group = groups[choice_num - 1]
                    return selected_group
                elif choice_num == len(groups) + 1:
                    custom_group = input(
                        "请输入自定义组名（Custom group name）: "
                    ).strip()
                    print(f"[WARN] 该组不是内置组，请手动为其配置权限：")
                    print("- 编辑 /etc/sudoers.d/{0} 添加sudo规则".format(custom_group))
                    print(
                        "- 使用 setfacl 授权，如：setfacl -m g:{0}:rwx /your/dir".format(
                            custom_group
                        )
                    )
                    print(
                        "- 示例 sudoers: %{0} ALL=(ALL) NOPASSWD: /bin/systemctl, /bin/ls".format(
                            custom_group
                        )
                    )
                    return custom_group
                else:
                    self.print_error(f"请输入 1-{len(groups)+1} 之间的数字")
            except ValueError:
                self.print_error("请输入有效的数字")

    def get_multiple_group_selection(self):
        """获取多个用户组选择"""
        print(
            f"\n{Fore.YELLOW if COLORS_AVAILABLE else ''}👥 选择用户组类型（可多选）{Style.RESET_ALL if COLORS_AVAILABLE else ''}"
        )
        groups = list(Config.GROUP_CONFIGS.keys())
        for i, (group_key, group_config) in enumerate(Config.GROUP_CONFIGS.items(), 1):
            print(f"{i}. {group_config['name']} ({group_key})")
            print(f"   {group_config['description']}")
        print(f"\n请输入组序号，用逗号分隔（如：1,3,4）或输入 'all' 选择所有组")
        while True:
            choice = input(f"请选择用户组: ").strip()
            selected_groups = []
            if choice.lower() == "all":
                selected_groups = groups
                break
            elif choice:
                try:
                    choices = [int(x.strip()) for x in choice.split(",")]
                    for choice_num in choices:
                        if 1 <= choice_num <= len(groups):
                            selected_groups.append(groups[choice_num - 1])
                        else:
                            self.print_error(f"无效的组序号: {choice_num}")
                            selected_groups = []
                            break
                    if selected_groups:
                        break
                except ValueError:
                    self.print_error("请输入有效的数字，用逗号分隔")
            else:
                self.print_error("请至少选择一个用户组")
        return selected_groups

    def add_user_to_multiple_groups(self, username, groupnames):
        """添加用户到多个组"""
        success_count = 0
        for groupname in groupnames:
            self.create_group_if_not_exists(groupname)
            groups = SystemUtils.get_user_groups(username)
            if groupname not in groups:
                try:
                    SystemUtils.run_command(f"usermod -a -G {groupname} {username}")
                    self.print_success(f"将用户 '{username}' 添加到组 '{groupname}'")
                    self.logger.info(f"添加用户到组：{username} to {groupname}")
                    success_count += 1
                except Exception as e:
                    self.print_error(f"添加用户到组 '{groupname}' 失败：{e}")
            else:
                self.print_info(f"用户 '{username}' 已在组 '{groupname}' 中")
        self.print_success(f"成功将用户 '{username}' 添加到 {success_count} 个新组")
        return success_count

    def display_user_permissions(self, username):
        """显示用户权限信息"""
        self.print_header(f"用户 '{username}' 权限信息")

        if not SystemUtils.user_exists(username):
            self.print_error(f"用户 '{username}' 不存在")
            return

        try:
            # 显示基本用户信息
            result = SystemUtils.run_command(f"id {username}")
            print(f"用户信息：{result.stdout.strip()}")

            # 显示用户组
            groups = SystemUtils.get_user_groups(username)
            print(f"所属组：{', '.join(groups)}")

            # 显示目录ACL权限
            print("\n📁 目录权限：")

            # 获取用户所属的已知组
            user_groups = SystemUtils.get_user_groups(username)
            relevant_directories = set()

            # 收集所有相关目录
            for group in user_groups:
                if group in Config.GROUP_CONFIGS:
                    relevant_directories.update(
                        Config.GROUP_CONFIGS[group]["directories"].keys()
                    )

            # 如果没有找到相关目录，显示所有可能的目录
            if not relevant_directories:
                for group_config in Config.GROUP_CONFIGS.values():
                    relevant_directories.update(group_config["directories"].keys())

            for directory in relevant_directories:
                if Path(directory).exists():
                    try:
                        result = SystemUtils.run_command(f"getfacl {directory}")
                        # 解析ACL输出，查找用户权限
                        acl_lines = result.stdout.split("\n")
                        user_perms = []
                        for line in acl_lines:
                            if f"user:{username}:" in line:
                                perm = line.split(":")[-1]
                                user_perms.append(f"{directory}: {perm}")

                        if user_perms:
                            for perm in user_perms:
                                print(f"  {perm}")
                        else:
                            print(f"  {directory}: 无特殊权限")
                    except:
                        print(f"  {directory}: 无法获取权限信息")
                else:
                    print(f"  {directory}: 目录不存在")

            # 显示sudo权限
            print(f"\n🔧 Sudo权限：")
            for group in groups:
                sudoers_file = Path(f"/etc/sudoers.d/{group}")
                if sudoers_file.exists():
                    print(f"  通过组 '{group}' 拥有sudo权限")
                    break
            else:
                print("  无sudo权限")

        except Exception as e:
            self.print_error(f"获取用户权限信息失败：{e}")

    def remove_user_permissions(self, username):
        """回收用户权限"""
        self.print_header(f"回收用户 '{username}' 权限")

        if not SystemUtils.user_exists(username):
            self.print_error(f"用户 '{username}' 不存在")
            return

        print("请选择要回收的权限：")
        print("1. 回收目录ACL权限")
        print("2. 从用户组移除用户")
        print("3. 删除用户账户")
        print("4. 全部回收")
        print("5. 返回主菜单")

        choice = input("请选择操作 [1-5]: ").strip()

        if choice == "1" or choice == "4":
            self._remove_acl_permissions(username)

        if choice == "2" or choice == "4":
            # 显示用户当前所属的组，让用户选择要移除的组
            user_groups = SystemUtils.get_user_groups(username)
            managed_groups = [g for g in user_groups if g in Config.GROUP_CONFIGS]

            if managed_groups:
                print(f"用户 '{username}' 当前所属的管理组：")
                for i, group in enumerate(managed_groups, 1):
                    group_config = Config.GROUP_CONFIGS[group]
                    print(f"{i}. {group_config['name']} ({group})")

                try:
                    group_choice = input(
                        "请选择要移除的组序号 [直接回车移除所有]: "
                    ).strip()
                    if group_choice == "":
                        # 移除所有管理组
                        for group in managed_groups:
                            self._remove_from_group(username, group)
                    else:
                        group_idx = int(group_choice) - 1
                        if 0 <= group_idx < len(managed_groups):
                            self._remove_from_group(username, managed_groups[group_idx])
                        else:
                            self.print_error("无效的组序号")
                except ValueError:
                    self.print_error("请输入有效的数字")
            else:
                self.print_info(f"用户 '{username}' 不在任何管理组中")

        if choice == "3" or choice == "4":
            self._delete_user(username)

    def _remove_acl_permissions(self, username):
        """移除ACL权限"""
        try:
            # 收集所有可能的目录
            all_directories = set()
            for group_config in Config.GROUP_CONFIGS.values():
                all_directories.update(group_config["directories"].keys())

            for directory in all_directories:
                if Path(directory).exists():
                    # 移除用户ACL权限
                    try:
                        SystemUtils.run_command(f"setfacl -x u:{username} {directory}")
                        # 移除默认ACL权限
                        try:
                            SystemUtils.run_command(
                                f"setfacl -x d:u:{username} {directory}"
                            )
                        except:
                            pass  # 如果没有默认权限，忽略错误

                        self.print_success(
                            f"移除用户 '{username}' 对目录 '{directory}' 的权限"
                        )
                    except Exception as e:
                        # 如果用户没有该目录的权限，跳过
                        if "No such file or directory" not in str(e):
                            self.print_warning(
                                f"移除目录 '{directory}' 权限时出现警告：{e}"
                            )

            self.logger.info(f"移除ACL权限：{username}")

        except Exception as e:
            self.print_error(f"移除ACL权限失败：{e}")

    def _remove_from_group(self, username, groupname):
        """从用户组移除用户"""
        try:
            groups = SystemUtils.get_user_groups(username)
            if groupname in groups:
                SystemUtils.run_command(f"gpasswd -d {username} {groupname}")
                self.print_success(f"从组 '{groupname}' 移除用户 '{username}'")
                self.logger.info(f"从组移除用户：{username} from {groupname}")
            else:
                self.print_info(f"用户 '{username}' 不在组 '{groupname}' 中")
        except Exception as e:
            self.print_error(f"从组移除用户失败：{e}")

    def _delete_user(self, username):
        """删除用户"""
        confirm = (
            input(f"确定要删除用户 '{username}' 吗？这将删除用户和家目录 [y/N]: ")
            .strip()
            .lower()
        )
        if confirm == "y" or confirm == "yes":
            try:
                SystemUtils.run_command(f"userdel -r {username}")
                self.print_success(f"用户 '{username}' 删除成功")
                self.logger.info(f"删除用户：{username}")
            except Exception as e:
                self.print_error(f"删除用户失败：{e}")
        else:
            self.print_info("取消删除操作")

    def modify_user_permissions(self, username):
        """修改现有用户权限"""
        self.print_header(f"修改用户 '{username}' 权限")

        if not SystemUtils.user_exists(username):
            self.print_error(f"用户 '{username}' 不存在")
            return

        print("请选择要修改的权限：")
        print("1. 修改目录权限")
        print("2. 更改用户组")
        print("3. 重新配置sudo权限")
        print("4. 全部重新配置")
        print("5. 添加多个权限组")
        print("6. 返回主菜单")

        choice = input("请选择操作 [1-6]: ").strip()

        if choice == "1":
            groupname = self.get_group_selection()
            directories_config = self.get_directory_permissions_input(groupname)
            if directories_config:
                self.set_directory_permissions(username, directories_config)
        elif choice == "2":
            groupname = self.get_group_selection()
            self._add_to_group(username, groupname)
        elif choice == "3":
            groupname = self.get_group_selection()
            self.set_sudo_permissions(username, groupname)
        elif choice == "4":
            groupname = self.get_group_selection()
            self._add_to_group(username, groupname)
            directories_config = self.get_directory_permissions_input(groupname)
            if directories_config:
                self.set_directory_permissions(username, directories_config)
            self.set_sudo_permissions(username, groupname)
        elif choice == "5":
            groupnames = self.get_multiple_group_selection()
            self.add_user_to_multiple_groups(username, groupnames)
        elif choice == "6":
            return
        else:
            self.print_error("无效选择，请输入 1-6")

    def _add_to_group(self, username, groupname):
        """添加用户到组"""
        try:
            self.create_group_if_not_exists(groupname)
            groups = SystemUtils.get_user_groups(username)
            if groupname not in groups:
                SystemUtils.run_command(f"usermod -a -G {groupname} {username}")
                self.print_success(f"将用户 '{username}' 添加到组 '{groupname}'")
                self.logger.info(f"添加用户到组：{username} to {groupname}")
            else:
                self.print_info(f"用户 '{username}' 已在组 '{groupname}' 中")
        except Exception as e:
            self.print_error(f"添加用户到组失败：{e}")

    def display_group_permissions(self):
        """显示所有权限组的详细权限配置"""
        self.print_header("系统权限组配置一览")
        for group_key, group_config in Config.GROUP_CONFIGS.items():
            print(
                f"{Fore.BLUE + Style.BRIGHT if COLORS_AVAILABLE else ''}■ {group_config['name']} ({group_key}){Style.RESET_ALL if COLORS_AVAILABLE else ''}"
            )
            print(f"  描述: {group_config['description']}")
            print(f"  目录权限:")
            for directory, info in group_config["directories"].items():
                perm = info["default"]
                perm_str = "读写(rwx)" if perm == "write" else "只读(r-x)"
                print(f"    - {directory} ({info['name']}): {perm_str}")
            print(f"  Sudo命令:")
            for cmd in group_config["sudo_commands"]:
                print(f"    - {cmd}")
            print("\n" + ("-" * 50))

    def group_permission_management_menu(self):
        """用户组权限管理菜单"""
        while True:
            self.print_header("用户组权限管理")
            print("1. 查看所有脚本定义用户组的系统状态")
            print("2. 为用户组增加/删除目录权限")
            print("3. 为用户组增加/删除sudo命令权限")
            print("4. 一键为用户组设置脚本预设权限")
            print("5. 返回主菜单")
            choice = input("\n请输入选择 [1-5]: ").strip()
            if choice == "1":
                self.check_all_groups_status()
            elif choice == "2":
                self.modify_group_directory_permission()
            elif choice == "3":
                self.modify_group_sudo_permission()
            elif choice == "4":
                self.apply_script_permissions_to_group()
            elif choice == "5":
                break
            else:
                self.print_error("无效选择，请输入 1-5")
            input("\n按回车键继续...")

    def check_all_groups_status(self):
        """检查所有脚本定义用户组的系统状态（是否存在、ACL、sudoers）"""
        self.print_header("用户组系统状态检查")
        for group_key, group_config in Config.GROUP_CONFIGS.items():
            print(
                f"{Fore.BLUE + Style.BRIGHT if COLORS_AVAILABLE else ''}■ {group_config['name']} ({group_key}){Style.RESET_ALL if COLORS_AVAILABLE else ''}"
            )
            # 检查组是否存在
            group_exists = SystemUtils.group_exists(group_key)
            print(f"  用户组存在: {'是' if group_exists else '否'}")
            # 检查目录ACL
            print(f"  目录ACL权限:")
            for directory in group_config["directories"].keys():
                if not Path(directory).exists():
                    print(f"    - {directory}: 目录不存在")
                    continue
                try:
                    result = SystemUtils.run_command(f"getfacl {directory}")
                    acl_lines = result.stdout.split("\n")
                    group_acl = [
                        line for line in acl_lines if f"group:{group_key}:" in line
                    ]
                    if group_acl:
                        for acl in group_acl:
                            print(f"    - {directory}: {acl}")
                    else:
                        print(f"    - {directory}: 无特殊组权限")
                except Exception as e:
                    print(f"    - {directory}: 获取ACL失败: {e}")
            # 检查sudoers
            sudoers_file = Path(f"/etc/sudoers.d/{group_key}")
            if sudoers_file.exists():
                print(f"  Sudoers文件: 存在")
                try:
                    content = sudoers_file.read_text(errors="ignore")
                    print(
                        f"    内容摘要: {content.strip().splitlines()[-1] if content.strip() else '空'}"
                    )
                except Exception as e:
                    print(f"    读取失败: {e}")
            else:
                print(f"  Sudoers文件: 不存在")
            print("\n" + ("-" * 50))

    def modify_group_directory_permission(self):
        """为用户组增加/删除目录权限"""
        self.print_header("为用户组增加/删除目录权限")
        groups = list(Config.GROUP_CONFIGS.keys())
        print("可用用户组：")
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group}")
        choice = input(f"请选择要操作的用户组 [1-{len(groups)}] (示例: 2): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(groups):
                group_key = groups[idx]
            else:
                self.print_error("无效选择")
                return
        except ValueError:
            self.print_error("请输入有效数字")
            return
        group_config = Config.GROUP_CONFIGS[group_key]
        print("\n可操作目录：")
        for i, directory in enumerate(group_config["directories"].keys(), 1):
            print(f"{i}. {directory}")
        print(f"{len(group_config['directories'])+1}. 自定义目录")
        dir_choice = input(
            f"请选择目录 [1-{len(group_config['directories'])+1}] (示例: 3): "
        ).strip()
        try:
            dir_idx = int(dir_choice) - 1
            if 0 <= dir_idx < len(group_config["directories"]):
                directory = list(group_config["directories"].keys())[dir_idx]
            elif dir_idx == len(group_config["directories"]):
                directory = input("请输入自定义目录路径 (示例: /data/mydir): ").strip()
            else:
                self.print_error("无效选择")
                return
        except ValueError:
            self.print_error("请输入有效数字")
            return
        op = input("请选择操作: 1. 增加权限  2. 删除权限 (示例: 1): ").strip()
        if op == "1":
            perm = input(
                "请选择权限类型: 1. 只读(r-x)  2. 读写(rwx) (示例: 2): "
            ).strip()
            if perm == "1":
                perm_str = "r-x"
            elif perm == "2":
                perm_str = "rwx"
            else:
                self.print_error("无效权限类型")
                return
            try:
                SystemUtils.run_command(
                    f"setfacl -m g:{group_key}:{perm_str} {directory}"
                )
                if perm_str == "rwx":
                    SystemUtils.run_command(
                        f"setfacl -d -m g:{group_key}:{perm_str} {directory}"
                    )
                self.print_success(
                    f"已为组 '{group_key}' 增加目录 '{directory}' 权限: {perm_str}"
                )
            except Exception as e:
                self.print_error(f"设置目录权限失败: {e}")
        elif op == "2":
            try:
                SystemUtils.run_command(f"setfacl -x g:{group_key} {directory}")
                SystemUtils.run_command(f"setfacl -x d:g:{group_key} {directory}")
                self.print_success(
                    f"已为组 '{group_key}' 删除目录 '{directory}' 的ACL权限"
                )
            except Exception as e:
                self.print_error(f"删除目录权限失败: {e}")
        else:
            self.print_error("无效操作类型")

    def modify_group_sudo_permission(self):
        """为用户组增加/删除sudo命令权限"""
        self.print_header("为用户组增加/删除sudo命令权限")
        groups = list(Config.GROUP_CONFIGS.keys())
        print("可用用户组：")
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group}")
        choice = input(f"请选择要操作的用户组 [1-{len(groups)}] (示例: 2): ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(groups):
                group_key = groups[idx]
            else:
                self.print_error("无效选择")
                return
        except ValueError:
            self.print_error("请输入有效数字")
            return
        sudoers_file = Path(f"/etc/sudoers.d/{group_key}")
        if not sudoers_file.exists():
            self.print_warning(f"sudoers文件不存在，将为组 '{group_key}' 创建新文件")
            sudoers_content = (
                f"# Sudoers rules for {group_key}\n%{group_key} ALL=(ALL) NOPASSWD: \n"
            )
            sudoers_file.write_text(sudoers_content)
            sudoers_file.chmod(0o440)
        op = input("请选择操作: 1. 增加命令  2. 删除命令 (示例: 1): ").strip()
        try:
            content = sudoers_file.read_text(errors="ignore")
        except Exception as e:
            self.print_error(f"读取sudoers文件失败: {e}")
            return
        lines = content.splitlines()
        # 找到命令行
        for i, line in enumerate(lines):
            if line.strip().startswith(f"%{group_key} "):
                cmd_line_idx = i
                break
        else:
            # 没有命令行，添加一行
            lines.append(f"%{group_key} ALL=(ALL) NOPASSWD: ")
            cmd_line_idx = len(lines) - 1
        cmd_line = lines[cmd_line_idx]
        if op == "1":
            new_cmd = input("请输入要增加的命令绝对路径 (示例: /usr/bin/dnf): ").strip()
            if new_cmd in cmd_line:
                self.print_info("该命令已存在")
                return
            if cmd_line.strip().endswith(":"):
                cmd_line += f" {new_cmd}"
            else:
                cmd_line += f", {new_cmd}"
            lines[cmd_line_idx] = cmd_line
            try:
                sudoers_file.write_text("\n".join(lines) + "\n")
                sudoers_file.chmod(0o440)
                SystemUtils.run_command(f"visudo -c -f {sudoers_file}")
                self.print_success(f"已为组 '{group_key}' 增加sudo命令: {new_cmd}")
            except Exception as e:
                self.print_error(f"写入sudoers文件失败: {e}")
        elif op == "2":
            del_cmd = input("请输入要删除的命令绝对路径 (示例: /usr/bin/dnf): ").strip()
            if del_cmd not in cmd_line:
                self.print_info("该命令不在sudoers中")
                return
            # 删除命令（支持逗号分隔和空格分隔）
            cmds = [
                c.strip()
                for c in cmd_line.split(":", 1)[1].replace(",", " ").split()
                if c.strip()
            ]
            cmds = [c for c in cmds if c != del_cmd]
            new_cmd_line = (
                f"%{group_key} ALL=(ALL) NOPASSWD: {', '.join(cmds)}"
                if cmds
                else f"%{group_key} ALL=(ALL) NOPASSWD:"
            )
            lines[cmd_line_idx] = new_cmd_line
            try:
                sudoers_file.write_text("\n".join(lines) + "\n")
                sudoers_file.chmod(0o440)
                SystemUtils.run_command(f"visudo -c -f {sudoers_file}")
                self.print_success(f"已为组 '{group_key}' 删除sudo命令: {del_cmd}")
            except Exception as e:
                self.print_error(f"写入sudoers文件失败: {e}")
        else:
            self.print_error("无效操作类型")

    def apply_script_permissions_to_group(self):
        """一键为用户组设置脚本预设权限"""
        self.print_header("一键设置用户组脚本预设权限")
        groups = list(Config.GROUP_CONFIGS.keys())
        print("可用用户组：")
        for i, group in enumerate(groups, 1):
            print(f"{i}. {group}")
        print(f"{len(groups)+1}. 全部用户组")
        choice = input(f"请选择要设置的用户组 [1-{len(groups)+1}]: ").strip()
        if choice == str(len(groups) + 1):
            selected_groups = groups
        else:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(groups):
                    selected_groups = [groups[idx]]
                else:
                    self.print_error("无效选择")
                    return
            except ValueError:
                self.print_error("请输入有效数字")
                return
        for group_key in selected_groups:
            group_config = Config.GROUP_CONFIGS[group_key]
            # 1. 创建组
            if not SystemUtils.group_exists(group_key):
                try:
                    SystemUtils.run_command(f"groupadd {group_key}")
                    self.print_success(f"用户组 '{group_key}' 创建成功")
                except Exception as e:
                    self.print_error(f"创建用户组失败: {e}")
                    continue
            else:
                self.print_info(f"用户组 '{group_key}' 已存在")
            # 2. 设置目录ACL
            for directory, info in group_config["directories"].items():
                if not Path(directory).exists():
                    self.print_warning(f"目录 {directory} 不存在，跳过")
                    continue
                perm = info["default"]
                perm_str = Config.PERMISSION_TYPES[perm]
                try:
                    SystemUtils.run_command(
                        f"setfacl -m g:{group_key}:{perm_str} {directory}"
                    )
                    if perm == "write":
                        SystemUtils.run_command(
                            f"setfacl -d -m g:{group_key}:{perm_str} {directory}"
                        )
                    self.print_success(
                        f"为组 '{group_key}' 设置目录 '{directory}' {perm} 权限"
                    )
                except Exception as e:
                    self.print_error(f"设置目录 {directory} 权限失败: {e}")
            # 3. 设置sudoers
            sudoers_file = Path(f"/etc/sudoers.d/{group_key}")
            commands_str = ", ".join(group_config["sudo_commands"])
            sudoers_content = f"""# Sudoers rules for {group_key} group ({group_config['name']})\n# Created by user_manager.py\n# Description: {group_config['description']}\n# Note: This is for login users management, not application runtime permissions\n\n%{group_key} ALL=(ALL) NOPASSWD: {commands_str}\n"""
            try:
                sudoers_file.write_text(sudoers_content)
                sudoers_file.chmod(0o440)
                SystemUtils.run_command(f"visudo -c -f {sudoers_file}")
                self.print_success(f"为组 '{group_key}' 设置sudoers文件成功")
            except Exception as e:
                self.print_error(f"设置sudoers文件失败: {e}")
        self.print_info("一键设置完成！")

    def load_ssh_keys_from_yaml(self, yaml_path):
        """从yaml文件加载ssh公钥，返回{username: pubkey}字典"""
        if not YAML_AVAILABLE:
            self.print_error(
                "未安装PyYAML库，无法解析yaml文件。请先运行: pip install pyyaml"
            )
            return {}
        if not Path(yaml_path).exists():
            self.print_error(f"公钥文件 {yaml_path} 不存在")
            return {}
        try:
            with open(yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            result = {}
            for item in data.get("ssh-keys", []):
                account = item.get("account")
                pub = item.get("pub-secret")
                if account and pub:
                    result[account] = pub
            return result
        except Exception as e:
            self.print_error(f"解析yaml文件失败: {e}")
            return {}

    def create_new_user_workflow(self):
        """创建新用户工作流"""
        self.print_header("创建登录用户并配置权限")

        # 获取用户名，支持批量输入
        while True:
            usernames_input = input("请输入用户名（支持逗号分隔批量创建）: ").strip()
            if not usernames_input:
                self.print_error("用户名不能为空")
                continue
            usernames = [u.strip() for u in usernames_input.split(",") if u.strip()]
            if not usernames:
                self.print_error("用户名不能为空")
                continue
            break

        # 询问是否导入ssh公钥yaml文件
        ssh_key_map = {}
        use_yaml = input("是否为用户批量导入ssh公钥？(y/N): ").strip().lower()
        if use_yaml == "y" or use_yaml == "yes":
            yaml_path = input("请输入yaml文件路径（如user-pub.yaml）: ").strip()
            ssh_key_map = self.load_ssh_keys_from_yaml(yaml_path)

        # 选择用户组类型
        groupname = self.get_group_selection()
        group_config = Config.GROUP_CONFIGS[groupname]

        self.print_info(f"已选择：{group_config['name']} ({groupname})")
        self.print_info(f"描述：{group_config['description']}")

        # 检查用户组是否存在，若不存在则提示批量创建
        if not SystemUtils.group_exists(groupname):
            print(f"用户组 '{groupname}' 不存在。")
            print("请选择：")
            print("1. 只创建当前所选用户组")
            print("2. 一次性创建全部预设的用户组")
            while True:
                choice = input("请输入选择 [1-2] (默认1): ").strip()
                if choice == "2":
                    # 批量创建所有预设组
                    for g in Config.GROUP_CONFIGS.keys():
                        self.create_group_if_not_exists(g)
                    break
                elif choice == "1" or choice == "":
                    self.create_group_if_not_exists(groupname)
                    break
                else:
                    self.print_error("无效选择，请输入1或2")
        else:
            self.create_group_if_not_exists(groupname)

        # 配置目录权限（只需配置一次，应用于所有用户）
        directories_config = self.get_directory_permissions_input(groupname)

        # 依次创建用户并配置权限
        for username in usernames:
            if SystemUtils.user_exists(username):
                self.print_error(f"用户 '{username}' 已存在，跳过！")
                continue
            # 创建用户
            if not self.create_user(username, groupname):
                continue
            # 配置目录权限
            if directories_config:
                success_count = self.set_directory_permissions(
                    username, directories_config
                )
                self.print_info(
                    f"成功为 '{username}' 配置 {success_count} 个目录的权限"
                )
            # 配置sudo权限
            if self.set_sudo_permissions(username, groupname):
                self.print_success(f"为 '{username}' Sudo权限配置完成")
            # 自动写入ssh公钥
            if ssh_key_map.get(username):
                try:
                    ssh_dir = Path(f"/home/{username}/.ssh")
                    auth_keys = ssh_dir / "authorized_keys"
                    with open(auth_keys, "a", encoding="utf-8") as f:
                        f.write(ssh_key_map[username].strip() + "\n")
                    self.print_success(f"已为 '{username}' 自动写入ssh公钥")
                except Exception as e:
                    self.print_error(f"自动写入ssh公钥失败: {e}")
            # 提示SSH密钥配置
            self.print_info(f"🔑 SSH密钥配置提示（{username}）：")
            print(f"1. 用户SSH目录：/home/{username}/.ssh/")
            print(f"2. 请将用户的公钥添加到：/home/{username}/.ssh/authorized_keys")
            print(f"3. 用户已禁用密码登录，只能使用密钥登录")
            print(
                f"4. 示例命令：echo 'ssh-rsa AAAAB3...' >> /home/{username}/.ssh/authorized_keys"
            )
            self.print_success(f"登录用户 '{username}' 创建和配置完成！")

        # 显示用户组特定的提示信息（只显示一次）
        if groupname == "developers":
            self.print_info("💻 开发人员提示：")
            print("1. 可以访问源码目录：/usr/local/src/")
            print("2. 可以查看系统日志：/var/log/")
            print("3. 可以管理服务：sudo systemctl restart service-name")
            print("4. 可以查看系统状态：sudo top, sudo ps, sudo netstat")
        elif groupname == "operations":
            self.print_info("🔧 运维人员提示：")
            print("1. 拥有系统管理权限：sudo systemctl")
            print("2. 可以管理防火墙：sudo ufw, sudo iptables")
            print("3. 可以管理存储：sudo mount, sudo fdisk")
            print("4. 可以管理容器：sudo docker, sudo docker-compose")
        elif groupname == "security":
            self.print_info("🔒 安全管理员提示：")
            print("1. 可以查看所有日志：/var/log/")
            print("2. 可以管理防火墙和安全工具")
            print("3. 可以查看用户登录记录：sudo last, sudo lastlog")
            print("4. 可以管理文件权限：sudo chmod, sudo chown")
        elif groupname == "readonly":
            self.print_info("👁️ 只读用户提示：")
            print("1. 只能查看系统信息和日志")
            print("2. 不能修改系统配置")
            print("3. 适用于审计和监控需求")
            print("4. 可以查看系统状态但不能修改")

        self.print_info("注意：此脚本仅管理登录用户权限，不涉及应用程序运行权限")

    def modify_user_workflow(self):
        """修改用户权限工作流"""
        username = input("请输入要修改的用户名: ").strip()
        if not username:
            self.print_error("用户名不能为空")
            return

        self.modify_user_permissions(username)

    def view_user_permissions_workflow(self):
        """查看用户权限工作流"""
        username = input("请输入要查看的用户名: ").strip()
        if not username:
            self.print_error("用户名不能为空")
            return

        self.display_user_permissions(username)

    def remove_permissions_workflow(self):
        """回收权限工作流"""
        username = input("请输入要回收权限的用户名: ").strip()
        if not username:
            self.print_error("用户名不能为空")
            return

        self.remove_user_permissions(username)


def main():
    """主函数"""
    try:
        # 首先检查并安装依赖
        check_and_install_dependencies()

        # 新增：命令行参数解析
        parser = argparse.ArgumentParser(
            description="Linux登录用户权限管理 User Manager Tool"
        )
        subparsers = parser.add_subparsers(dest="command", help="主命令 Main Command")

        # add-group
        parser_add_group = subparsers.add_parser(
            "add-group", help="创建用户组 Create user group"
        )
        parser_add_group.add_argument(
            "groups", type=str, help="用户组名，逗号分隔 Group names, comma separated"
        )
        parser_add_group.add_argument(
            "--force",
            action="store_true",
            help="无需确认，全部执行 No confirmation, force all",
        )

        # add-user
        parser_add_user = subparsers.add_parser(
            "add-user", help="创建登录账户 Create login user"
        )
        parser_add_user.add_argument(
            "users", type=str, help="用户名，逗号分隔 Usernames, comma separated"
        )
        parser_add_user.add_argument(
            "-g", "--group", type=str, help="指定用户组 User group"
        )
        parser_add_user.add_argument(
            "-k", "--keyfile", type=str, help="公钥yaml文件 SSH key yaml file"
        )
        parser_add_user.add_argument(
            "--force",
            action="store_true",
            help="无需确认，全部执行 No confirmation, force all",
        )

        # mod-group
        parser_mod_group = subparsers.add_parser(
            "mod-group", help="修改用户组权限 Modify group permissions"
        )
        parser_mod_group.add_argument("group", type=str, help="用户组名 Group name")
        parser_mod_group.add_argument(
            "--add-dir", type=str, help="增加目录权限 Add directory permission"
        )
        parser_mod_group.add_argument(
            "--perm", type=str, choices=["r-x", "rwx"], help="权限类型 Permission type"
        )
        parser_mod_group.add_argument(
            "--force",
            action="store_true",
            help="无需确认，全部执行 No confirmation, force all",
        )

        args = parser.parse_args()

        # 初始化用户管理器
        manager = UserManager()

        # 命令分发
        if args.command == "add-group":
            # 参数齐全，直接批量创建
            groupnames = [g.strip() for g in args.groups.split(",") if g.strip()]
            if not groupnames:
                print("[ERROR] 请输入有效的用户组名 (Please input valid group names)")
                sys.exit(1)
            for g in groupnames:
                manager.create_group_if_not_exists(g)
            print(f"[SUCCESS] 用户组创建完成 Groups created: {', '.join(groupnames)}")
            return
        elif args.command == "add-user":
            # 检查参数是否齐全
            if args.users and args.group:
                usernames = [u.strip() for u in args.users.split(",") if u.strip()]
                groupname = args.group
                keyfile = args.keyfile
                # 判断是否为内置组
                builtin_groups = set(Config.GROUP_CONFIGS.keys())
                if groupname not in builtin_groups:
                    print(
                        f"[WARN] 用户组 {groupname} 不是脚本内置组。请手动为其配置权限："
                    )
                    print("- 编辑 /etc/sudoers.d/{0} 添加sudo规则".format(groupname))
                    print(
                        "- 使用 setfacl 为目录授权，如：setfacl -m g:{0}:rwx /your/dir".format(
                            groupname
                        )
                    )
                    print(
                        "- 示例 sudoers 内容: %{0} ALL=(ALL) NOPASSWD: /bin/systemctl, /bin/ls".format(
                            groupname
                        )
                    )
                else:
                    print(f"[INFO] 选择的用户组为内置组: {groupname}")
                # 导入公钥
                ssh_key_map = {}
                if keyfile:
                    if not YAML_AVAILABLE:
                        print(
                            "[ERROR] 未安装PyYAML库，无法解析yaml文件。请先运行: pip install pyyaml"
                        )
                        sys.exit(1)
                    if not Path(keyfile).exists():
                        print(f"[ERROR] 公钥文件 {keyfile} 不存在")
                        sys.exit(1)
                    try:
                        with open(keyfile, "r", encoding="utf-8") as f:
                            data = yaml.safe_load(f)
                        for item in data.get("ssh-keys", []):
                            account = item.get("account")
                            pub = item.get("pub-secret")
                            if account and pub:
                                ssh_key_map[account] = pub
                    except Exception as e:
                        print(f"[ERROR] 解析yaml文件失败: {e}")
                        sys.exit(1)
                # 创建用户组（如为自定义组则只尝试创建，不配置权限）
                manager.create_group_if_not_exists(groupname)
                # 配置目录权限（内置组才自动配置）
                directories_config = {}
                if groupname in builtin_groups:
                    directories_config = manager.get_directory_permissions_input(
                        groupname
                    )
                # 依次创建用户
                for username in usernames:
                    if SystemUtils.user_exists(username):
                        print(f"[WARN] 用户 '{username}' 已存在，跳过！")
                        continue
                    if not manager.create_user(username, groupname):
                        continue
                    if directories_config:
                        success_count = manager.set_directory_permissions(
                            username, directories_config
                        )
                        print(
                            f"[INFO] 成功为 '{username}' 配置 {success_count} 个目录的权限"
                        )
                    if groupname in builtin_groups and manager.set_sudo_permissions(
                        username, groupname
                    ):
                        print(f"[SUCCESS] 为 '{username}' Sudo权限配置完成")
                    # 自动写入ssh公钥
                    if ssh_key_map.get(username):
                        try:
                            ssh_dir = Path(f"/home/{username}/.ssh")
                            auth_keys = ssh_dir / "authorized_keys"
                            with open(auth_keys, "a", encoding="utf-8") as f:
                                f.write(ssh_key_map[username].strip() + "\n")
                            print(f"[SUCCESS] 已为 '{username}' 自动写入ssh公钥")
                        except Exception as e:
                            print(f"[ERROR] 自动写入ssh公钥失败: {e}")
                    print(f"[SUCCESS] 登录用户 '{username}' 创建和配置完成！")
                return
            else:
                print(
                    "[WARN] 参数不全，进入交互模式 (Missing args, entering interactive mode)"
                )
                manager.create_new_user_workflow()
                return
        elif args.command == "mod-group":
            # 检查参数是否齐全
            groupname = args.group
            add_dir = args.add_dir
            perm = args.perm
            builtin_groups = set(Config.GROUP_CONFIGS.keys())
            if groupname and add_dir and perm:
                if groupname not in builtin_groups:
                    print(
                        f"[WARN] 用户组 {groupname} 不是脚本内置组。请手动为其配置目录权限："
                    )
                    print(
                        "- 使用 setfacl 授权，如：setfacl -m g:{0}:{1} {2}".format(
                            groupname, perm, add_dir
                        )
                    )
                    print("- 可用权限: r-x(只读), rwx(读写)")
                else:
                    try:
                        # setfacl -m g:groupname:perm add_dir
                        SystemUtils.run_command(
                            f"setfacl -m g:{groupname}:{perm} {add_dir}"
                        )
                        if perm == "rwx":
                            SystemUtils.run_command(
                                f"setfacl -d -m g:{groupname}:{perm} {add_dir}"
                            )
                        print(
                            f"[SUCCESS] 已为组 '{groupname}' 增加目录 '{add_dir}' 权限: {perm}"
                        )
                    except Exception as e:
                        print(f"[ERROR] 设置目录权限失败: {e}")
                return
            else:
                print(
                    "[WARN] 参数不全，进入交互模式 (Missing args, entering interactive mode)"
                )
                manager.group_permission_management_menu()
                return
        else:
            # 无参数，进入主菜单交互模式
            manager.main_menu()
    except KeyboardInterrupt:
        print(
            f"\n\n{Fore.YELLOW if COLORS_AVAILABLE else ''}程序被用户中断{Style.RESET_ALL if COLORS_AVAILABLE else ''}"
        )
        sys.exit(0)
    except Exception as e:
        print(
            f"\n{Fore.RED if COLORS_AVAILABLE else ''}程序异常：{e}{Style.RESET_ALL if COLORS_AVAILABLE else ''}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
