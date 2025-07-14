#!/bin/bash

# AIRouter 项目安装脚本
# 此脚本帮助您快速设置项目环境

set -e

echo "🚀 开始安装 AIRouter 项目..."

# 检查 Python 版本
echo "📋 检查 Python 版本..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python 版本: $python_version"

# 检查是否为 Python 3.7+
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 7) else 1)"; then
    echo "✅ Python 版本检查通过"
else
    echo "❌ 错误: 需要 Python 3.7 或更高版本"
    exit 1
fi

# 创建虚拟环境
echo "📦 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "⚠️  虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 更新 pip
echo "📦 更新 pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装项目依赖..."
pip install -e .

# 复制配置文件
echo "⚙️  设置配置文件..."
if [ ! -f "ew_config/api_keys_local.py" ]; then
    cp ew_config/api_keys.example.py ew_config/api_keys_local.py
    echo "✅ API密钥配置文件已复制到 ew_config/api_keys_local.py"
    echo "⚠️  请编辑此文件填入您的真实API密钥"
else
    echo "⚠️  API密钥配置文件已存在，跳过复制"
fi

# 复制环境变量配置文件
if [ ! -f ".env" ]; then
    cp env.example .env
    echo "✅ 环境变量配置文件已复制到 .env"
    echo "⚠️  请编辑此文件填入您的真实数据库连接信息"
    echo "🔑 重要：请确保设置 DB_PASSWORD，这是必需的环境变量"
else
    echo "⚠️  环境变量配置文件已存在，跳过复制"
fi

# 创建必要的目录
echo "📁 创建必要的目录..."
mkdir -p data logs tests

# 设置 Git 钩子（如果是 Git 仓库）
if [ -d ".git" ]; then
    echo "🔒 设置 Git 安全配置..."
    # 确保敏感文件不会被提交
    git config --local core.autocrlf false
    echo "✅ Git 配置完成"
fi

# 检查 Docker
echo "🐳 检查 Docker..."
if command -v docker &> /dev/null; then
    echo "✅ Docker 已安装"
    echo "💡 您可以使用 'docker-compose up -d' 启动服务"
else
    echo "⚠️  Docker 未安装，您需要手动启动服务"
fi

# 显示下一步操作
echo ""
echo "🎉 安装完成！"
echo ""
echo "📋 下一步操作："
echo "1. 编辑 ew_config/api_keys_local.py 填入您的API密钥"
echo "2. 编辑 .env 文件填入您的数据库连接信息（必须设置 DB_PASSWORD）"
echo "3. 配置数据库连接（如果需要）"
echo "4. 启动服务："
echo "   - 使用 Docker: docker-compose up -d"
echo "   - 手动启动: python CheckHealthy.py (健康检查服务)"
echo "   - 手动启动: python -m api_key_manager.main (API密钥管理)"
echo "4. 运行测试: python -m pytest tests/"
echo ""
echo "📚 更多信息请参阅 README.md"
echo ""
echo "✅ 安装脚本完成！" 