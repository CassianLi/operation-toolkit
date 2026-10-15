#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库历史数据清理工具
生产环境MySQL数据库历史数据清理工具包
"""

from setuptools import setup, find_packages
import os


# 读取README文件
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return "数据库历史数据清理工具"


# 读取requirements文件
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(requirements_path):
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


setup(
    name="db-cleanup-toolkit",
    version="1.0.0",
    author="Operation Toolkit",
    author_email="admin@example.com",
    description="生产数据库历史数据清理工具",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/operation-toolkit",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Database :: Database Administration",
        "Topic :: System :: Systems Administration",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    entry_points={
        "console_scripts": [
            "db-cleanup=db_cleanup_toolkit.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "db_cleanup_toolkit": [
            "config/*.yaml",
            "config/*.yaml.example",
        ],
    },
    keywords="database cleanup mysql maintenance production",
    project_urls={
        "Bug Reports": "https://github.com/your-org/operation-toolkit/issues",
        "Source": "https://github.com/your-org/operation-toolkit",
        "Documentation": "https://github.com/your-org/operation-toolkit/blob/main/README.md",
    },
)
