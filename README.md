# AIRouter

<div align="center">

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![GitHub Stars](https://img.shields.io/github/stars/your-username/AIRouter.svg?style=social)](https://github.com/your-username/AIRouter)

### 🌐 Language / 语言

**[🇨🇳 中文版](#-中文版) | [🇺🇸 English Version](#-english-version)**

---

</div>

## 🇨🇳 中文版

一个智能的AI路由器，为大型语言模型(LLM)提供高性能的统一API接口，支持多源负载均衡和智能故障转移。

### ✨ 主要特性

- **🔄 统一API接口**: 通过统一的接口访问多种LLM提供商（OpenRouter、DeepInfra、DeerAPI、TogetherAI、Google、OpenAI、Anthropic等）
- **⚡ 智能负载均衡**: 基于响应时间、成本和成功率的智能负载均衡与故障转移
- **📊 实时健康监控**: 自动监控API健康状态和性能指标
- **🔑 高性能API密钥管理**: 100倍性能提升的API密钥管理系统，支持智能失败避免
- **🎯 多模态支持**: 支持文本生成、多模态输入（图像+文本）和函数调用
- **🚀 帕累托最优选择**: 从多个模型中智能选择最优模型
- **💰 成本优化**: 健康检查屏蔽功能，避免昂贵模型的不必要检查
- **🐳 容器化部署**: 完整的Docker支持，开箱即用

### 🏗️ 系统架构

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AIRouter      │    │  LoadBalancing   │    │ Health Monitor  │
│   (Core API)    │◄──►│   (智能路由)     │◄──►│   (健康检查)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Multiple LLM    │    │  API Key Manager │    │   Performance   │
│ Providers       │    │    (Service)     │    │   Analytics     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 📦 快速开始

#### 安装

**方式一：作为Python包安装（推荐）**

```bash
git clone https://github.com/your-username/AIRouter.git
cd AIRouter
pip install -e .
```

**方式二：直接安装依赖**

```bash
git clone https://github.com/your-username/AIRouter.git
cd AIRouter  
pip install -r requirements.txt
```

#### 配置

**1. 配置API密钥**

```bash
cp ew_config/api_keys.example.py ew_config/api_keys_local.py
# 编辑 ew_config/api_keys_local.py，填入您的真实API密钥
```

**2. 数据库设置**

```sql
CREATE DATABASE airouter;
CREATE TABLE api_key_usage (
    request_id VARCHAR(50) PRIMARY KEY,
    api_key VARCHAR(100) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    source_name VARCHAR(50) NOT NULL,
    prompt_tokens INT,
    completion_tokens INT,
    create_time DATETIME NOT NULL,
    finish_time DATETIME NOT NULL,
    execution_time FLOAT NOT NULL,
    status BOOLEAN NOT NULL
);
```

**3. 环境变量**

```bash
# 复制环境变量配置文件
cp env.example .env

# 编辑 .env 文件，填入您的真实数据库信息
# 注意：请确保设置 DB_PASSWORD，这是必需的环境变量
```

#### 启动服务

**Docker部署（推荐）**

```bash
# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

**手动启动**

```bash
# 启动健康检查服务
python CheckHealthy.py

# 在另一个终端启动API密钥管理服务
python -m api_key_manager.main
```

### 🚀 使用示例

#### 基本文本生成

```python
from LLMwrapper import LLM_Wrapper

# 简单的文本生成
response = LLM_Wrapper.generate(
    model_name="gpt4o_mini",
    prompt="解释量子计算的基本原理"
)
print(response)
```

#### 多模态输入

```python
import base64

# 图像+文本输入
with open("image.jpg", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

response = LLM_Wrapper.generate_mm(
    model_name="gpt4o_mini",
    prompt="描述这张图片的内容",
    img_base64=img_base64
)
print(response)
```

#### 函数调用

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "城市名称"}
                },
                "required": ["location"]
            }
        }
    }
]

response = LLM_Wrapper.function_calling(
    model_name="gpt4o_mini",
    prompt="北京今天天气如何？",
    tools=tools
)
print(response)
```

### 🔧 高级配置

#### 负载均衡策略

```python
# 配置负载均衡模式
response = LLM_Wrapper.generate(
    model_name="gpt4o_mini",
    prompt="你好",
    mode="cost_first"  # 可选: fast_first, cost_first, balanced
)
```

#### 帕累托最优选择

```python
# 从多个模型中选择最优结果
response = LLM_Wrapper.generate_fromTHEbest(
    model_list=["gpt4o_mini", "claude35_sonnet", "gemini15_pro"],
    prompt="复杂推理任务"
)
```

### 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 📄 许可证

这个项目使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。

### 🆘 支持

如果您在使用过程中遇到问题，请：

1. 查看 [GitHub Issues](https://github.com/THESIS-AGENT/AIRouter/issues)
2. 创建新的 Issue 描述您的问题

---

## 🇺🇸 English Version

An intelligent AI router that provides high-performance unified API interfaces for Large Language Models (LLMs), supporting multi-source load balancing and intelligent failover.

### ✨ Key Features

- **🔄 Unified API Interface**: Access multiple LLM providers through a single interface (OpenRouter, DeepInfra, DeerAPI, TogetherAI, Google, OpenAI, Anthropic, etc.)
- **⚡ Smart Load Balancing**: Intelligent load balancing and failover based on response time, cost, and success rate
- **📊 Real-time Health Monitoring**: Automatic monitoring of API health status and performance metrics
- **🔑 High-performance API Key Management**: 100x performance improvement in API key management with intelligent failure avoidance
- **🎯 Multimodal Support**: Support for text generation, multimodal input (image + text), and function calling
- **🚀 Pareto Optimal Selection**: Intelligently select the optimal model from multiple options
- **💰 Cost Optimization**: Health check blacklist feature to avoid unnecessary checks on expensive models
- **🐳 Containerized Deployment**: Complete Docker support, ready to use out of the box

### 🏗️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   AIRouter      │    │  LoadBalancing   │    │ Health Monitor  │
│   (Core API)    │◄──►│ (Smart Routing)  │◄──►│ (Health Check)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                        │                        │
         ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Multiple LLM    │    │  API Key Manager │    │   Performance   │
│ Providers       │    │    (Service)     │    │   Analytics     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 📦 Quick Start

#### Installation

**Method 1: Install as Python Package (Recommended)**

```bash
git clone https://github.com/your-username/AIRouter.git
cd AIRouter
pip install -e .
```

**Method 2: Install Dependencies Directly**

```bash
git clone https://github.com/your-username/AIRouter.git
cd AIRouter  
pip install -r requirements.txt
```

#### Configuration

**1. Configure API Keys**

```bash
cp ew_config/api_keys.example.py ew_config/api_keys_local.py
# Edit ew_config/api_keys_local.py and fill in your real API keys
```

**2. Database Setup**

```sql
CREATE DATABASE airouter;
CREATE TABLE api_key_usage (
    request_id VARCHAR(50) PRIMARY KEY,
    api_key VARCHAR(100) NOT NULL,
    model_name VARCHAR(50) NOT NULL,
    source_name VARCHAR(50) NOT NULL,
    prompt_tokens INT,
    completion_tokens INT,
    create_time DATETIME NOT NULL,
    finish_time DATETIME NOT NULL,
    execution_time FLOAT NOT NULL,
    status BOOLEAN NOT NULL
);
```

**3. Environment Variables**

```bash
# Copy environment variable configuration file
cp env.example .env

# Edit .env file and fill in your real database information
# Note: Make sure to set DB_PASSWORD, this is a required environment variable
```

#### Start Services

**Docker Deployment (Recommended)**

```bash
# Start services
docker-compose up -d

# Check service status
docker-compose ps
```

**Manual Start**

```bash
# Start health check service
python CheckHealthy.py

# Start API key manager service in another terminal
python -m api_key_manager.main
```

### 🚀 Usage Examples

#### Basic Text Generation

```python
from LLMwrapper import LLM_Wrapper

# Simple text generation
response = LLM_Wrapper.generate(
    model_name="gpt4o_mini",
    prompt="Explain the basic principles of quantum computing"
)
print(response)
```

#### Multimodal Input

```python
import base64

# Image + text input
with open("image.jpg", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode()

response = LLM_Wrapper.generate_mm(
    model_name="gpt4o_mini",
    prompt="Describe the content of this image",
    img_base64=img_base64
)
print(response)
```

#### Function Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get weather information",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }
]

response = LLM_Wrapper.function_calling(
    model_name="gpt4o_mini",
    prompt="What's the weather like in Beijing today?",
    tools=tools
)
print(response)
```

### 🔧 Advanced Configuration

#### Load Balancing Strategies

```python
# Configure load balancing mode
response = LLM_Wrapper.generate(
    model_name="gpt4o_mini",
    prompt="Hello",
    mode="cost_first"  # Options: fast_first, cost_first, balanced
)
```

#### Pareto Optimal Selection

```python
# Select optimal results from multiple models
response = LLM_Wrapper.generate_fromTHEbest(
    model_list=["gpt4o_mini", "claude35_sonnet", "gemini15_pro"],
    prompt="Complex reasoning task"
)
```

### 🛠️ Development Guide

#### Project Structure

```
AIRouter/
├── LLMwrapper.py          # Core API interface
├── LoadBalancing.py       # Load balancing logic
├── CheckHealthy.py        # Health check service
├── api_key_manager/       # API key management service
├── ew_config/            # Configuration files
├── ew_api/               # API infrastructure
├── ew_decorator/         # Decorator utilities
└── unit_test/            # Test suite
```

#### Adding New LLM Providers

1. Add new provider configuration in `ew_config/source.py`
2. Configure API keys in `ew_config/api_keys.py`
3. Implement new API interface in `ew_api/`
4. Update routing logic in `LoadBalancing.py`

#### Running Tests

```bash
# Run basic tests
python unit_test.py

# Run complete test suite
python unit_test/run_all_tests.py

# Run API key manager tests
python -m api_key_manager.unit_test
```

### 🐳 Docker Deployment

#### Build Image

```bash
docker build -t airouter:latest .
```

#### Environment Configuration

Create `.env` file:

```env
DB_HOST=host.docker.internal
DB_USER=root
DB_PASSWORD=your_password_here
DB_NAME=airouter
DB_PORT=3306
```

#### Start Services

```bash
docker-compose up -d
```

### 📈 Monitoring and Logging

#### Health Check Endpoints

- **Health Check Service**: `http://localhost:8001/check_healthy`
- **API Key Manager Service**: `http://localhost:8002/check_healthy`
- **Docker Health Check**: `http://localhost:8001/docker-health`

#### View Logs

```bash
# View service logs
docker-compose logs -f airouter-health-check
docker-compose logs -f airouter-key-manager

# View real-time logs
tail -f health_check.log
```

### 🤝 Contributing

We welcome all forms of contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed information.

#### Quick Start Contributing

1. Fork this repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### 🆘 Support

If you encounter any issues during use, please:

1. Check [GitHub Issues](https://github.com/your-username/AIRouter/issues)
2. Create a new Issue describing your problem

### 🚀 Roadmap

- [ ] Support for more LLM providers
- [ ] Enhanced monitoring dashboard
- [ ] Auto-scaling capabilities
- [ ] More load balancing strategies
- [ ] Plugin system
- [ ] Web UI interface

### 🙏 Acknowledgments

Thanks to all developers who contributed to this project!

---

<div align="center">

⭐ **If this project helps you, please give us a Star!**

⭐ **如果这个项目对您有帮助，请给我们一个 Star！**

**[🔝 Back to Top](#airouter)**

</div>
