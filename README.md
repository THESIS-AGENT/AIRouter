# AIRouter

[![Python](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

一个智能的AI路由器，为大型语言模型(LLM)提供高性能的统一API接口，支持多源负载均衡和智能故障转移。

## ✨ 主要特性

- **🔄 统一API接口**: 通过统一的接口访问多种LLM提供商（OpenRouter、DeepInfra、DeerAPI、TogetherAI、Google、OpenAI、Anthropic等）
- **⚡ 智能负载均衡**: 基于响应时间、成本和成功率的智能负载均衡与故障转移
- **📊 实时健康监控**: 自动监控API健康状态和性能指标
- **🔑 高性能API密钥管理**: 100倍性能提升的API密钥管理系统，支持智能失败避免
- **🎯 多模态支持**: 支持文本生成、多模态输入（图像+文本）和函数调用
- **🚀 帕累托最优选择**: 从多个模型中智能选择最优模型
- **💰 成本优化**: 健康检查屏蔽功能，避免昂贵模型的不必要检查
- **🐳 容器化部署**: 完整的Docker支持，开箱即用

## 🏗️ 系统架构

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

## 📦 快速开始

### 安装

#### 方式一：作为Python包安装（推荐）

```bash
git clone https://github.com/your-username/AIRouter.git
cd AIRouter
pip install -e .
```

#### 方式二：直接安装依赖

```bash
git clone https://github.com/your-username/AIRouter.git
cd AIRouter  
pip install -r requirements.txt
```

### 配置

1. **配置API密钥**: 复制并编辑API密钥配置文件

```bash
cp ew_config/api_keys.py ew_config/api_keys_local.py
# 编辑 ew_config/api_keys_local.py，填入您的真实API密钥
```

2. **数据库设置**: 配置MySQL数据库用于API密钥管理

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

3. **环境变量**: 配置数据库连接

```bash
# 复制环境变量配置文件
cp env.example .env

# 编辑 .env 文件，填入您的真实数据库信息
# 注意：请确保设置 DB_PASSWORD，这是必需的环境变量
```

或者直接设置环境变量：

```bash
export DB_HOST=localhost
export DB_USER=root
export DB_PASSWORD=your_password_here  # 必须设置
export DB_NAME=airouter
export DB_PORT=3306
```

### 启动服务

#### Docker部署（推荐）

```bash
# 创建Docker网络
docker network create airouter-network

# 启动服务
docker-compose up -d

# 查看服务状态
docker-compose ps
```

#### 手动启动

```bash
# 启动健康检查服务
python CheckHealthy.py

# 在另一个终端启动API密钥管理服务
python -m api_key_manager.main
```

## 🚀 使用示例

### 基本文本生成

```python
from LLMwrapper import LLM_Wrapper

# 简单的文本生成
response = LLM_Wrapper.generate(
    model_name="gpt4o_mini",
    prompt="解释量子计算的基本原理"
)
print(response)
```

### 多模态输入

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

### 函数调用

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

## 📊 性能监控

AIRouter提供了完整的性能监控功能：

- **实时健康检查**: 监控所有API端点的可用性
- **性能统计**: 响应时间、成功率、成本分析
- **智能路由**: 基于性能指标的动态路由选择
- **故障转移**: 自动检测和切换故障节点

## 🔧 高级配置

### 负载均衡策略

```python
# 配置负载均衡模式
response = LLM_Wrapper.generate(
    model_name="gpt4o_mini",
    prompt="你好",
    mode="cost_first"  # 可选: fast_first, cost_first, balanced
)
```

### 超时设置

```python
# 自定义超时时间
response = LLM_Wrapper.generate(
    model_name="gpt4o_mini",
    prompt="长文本处理任务",
    timeout=60  # 60秒超时
)
```

### 帕累托最优选择

```python
# 从多个模型中选择最优结果
response = LLM_Wrapper.generate_fromTHEbest(
    model_list=["gpt4o_mini", "claude35_sonnet", "gemini15_pro"],
    prompt="复杂推理任务"
)
```

## 🛠️ 开发指南

### 项目结构

```
AIRouter/
├── LLMwrapper.py          # 核心API接口
├── LoadBalancing.py       # 负载均衡逻辑
├── CheckHealthy.py        # 健康检查服务
├── api_key_manager/       # API密钥管理服务
├── ew_config/            # 配置文件
├── ew_api/               # API基础设施
├── ew_decorator/         # 装饰器工具
└── unit_test/            # 测试套件
```

### 添加新的LLM提供商

1. 在 `ew_config/source.py` 中添加新的提供商配置
2. 在 `ew_config/api_keys.py` 中配置API密钥
3. 在 `ew_api/` 中实现新的API接口
4. 更新 `LoadBalancing.py` 中的路由逻辑

### 运行测试

```bash
# 运行基础测试
python unit_test.py

# 运行完整测试套件
python unit_test/run_all_tests.py

# 运行API密钥管理测试
python -m api_key_manager.unit_test
```

## 🐳 Docker 部署

### 构建镜像

```bash
docker build -t airouter:latest .
```

### 环境变量配置

创建 `.env` 文件：

```env
DB_HOST=host.docker.internal
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=airouter
DB_PORT=3306
```

### 启动服务

```bash
docker-compose up -d
```

## 📈 监控和日志

### 健康检查端点

- **健康检查服务**: `http://localhost:8001/check_healthy`
- **API密钥管理服务**: `http://localhost:8002/check_healthy`
- **Docker健康检查**: `http://localhost:8001/docker-health`

### 日志查看

```bash
# 查看服务日志
docker-compose logs -f airouter-health-check
docker-compose logs -f airouter-key-manager

# 查看实时日志
tail -f health_check.log
```

## 🤝 贡献指南

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 快速开始贡献

1. Fork 这个仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 📄 许可证

这个项目使用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详细信息。

## 🆘 支持

如果您在使用过程中遇到问题，请：

1. 查看 [GitHub Issues](https://github.com/your-username/AIRouter/issues)
2. 创建新的 Issue 描述您的问题
3. 加入我们的讨论 [GitHub Discussions](https://github.com/your-username/AIRouter/discussions)

## 🚀 路线图

- [ ] 支持更多LLM提供商
- [ ] 增强的监控仪表板
- [ ] 自动扩缩容功能
- [ ] 更多的负载均衡策略
- [ ] 插件系统
- [ ] Web UI界面

## 🙏 致谢

感谢所有为这个项目做出贡献的开发者们！

---

⭐ 如果这个项目对您有帮助，请给我们一个 Star！