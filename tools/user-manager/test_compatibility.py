#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Python 3.6 兼容性测试脚本
"""

import subprocess
import sys


def test_subprocess_compatibility():
    """测试subprocess兼容性"""
    print("🔍 测试Python 3.6兼容性...")
    print(f"Python版本: {sys.version}")

    try:
        # 测试Python 3.6兼容的subprocess调用
        result = subprocess.run(
            ["echo", "test"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )
        print(f"✅ subprocess.run 兼容性测试通过")
        print(f"输出: {result.stdout.strip()}")

        # 测试which命令
        result = subprocess.run(
            ["which", "python3"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        print(f"✅ which命令测试通过")

        return True

    except Exception as e:
        print(f"❌ 兼容性测试失败: {e}")
        return False


def test_imports():
    """测试导入"""
    print("\n🐍 测试模块导入...")

    try:
        import os
        import sys
        import json
        import logging
        import subprocess
        import getpass
        from datetime import datetime
        from pathlib import Path

        print("✅ 所有基础模块导入成功")

        # 测试colorama（可选）
        try:
            import colorama

            print("✅ colorama模块可用")
        except ImportError:
            print("⚠️  colorama模块未安装（可选）")

        return True

    except Exception as e:
        print(f"❌ 模块导入失败: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("     Python 3.6 兼容性测试")
    print("=" * 50)

    success = True

    # 测试导入
    if not test_imports():
        success = False

    # 测试subprocess
    if not test_subprocess_compatibility():
        success = False

    print("\n" + "=" * 50)
    if success:
        print("🎉 所有兼容性测试通过！")
        print("可以安全运行用户管理脚本")
    else:
        print("❌ 兼容性测试失败！")
        print("请检查Python环境")
    print("=" * 50)
