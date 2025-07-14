# 贡献指南

感谢您对 AIRouter 项目的关注！我们欢迎所有形式的贡献。

## 🚀 如何贡献

### 报告问题

如果您发现了 bug 或有功能建议，请：

1. 搜索现有的 [Issues](https://github.com/your-username/AIRouter/issues) 确认问题未被报告
2. 创建新的 Issue，提供详细信息：
   - 问题描述
   - 复现步骤
   - 预期行为
   - 实际行为
   - 环境信息（Python版本、操作系统等）

### 提交代码

1. **Fork 项目**
   ```bash
   git clone https://github.com/your-username/AIRouter.git
   cd AIRouter
   ```

2. **创建功能分支**
   ```bash
   git checkout -b feature/amazing-feature
   ```

3. **设置开发环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -e .
   pip install -r requirements-dev.txt
   ```

4. **进行更改**
   - 编写代码
   - 添加测试
   - 更新文档

5. **运行测试**
   ```bash
   pytest tests/
   python -m pytest tests/test_basic.py -v
   ```

6. **提交更改**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```

7. **创建 Pull Request**
   - 在 GitHub 上创建 Pull Request
   - 填写 PR 模板
   - 等待代码审查

## 📋 开发规范

### 代码风格

- 使用 Python 3.7+ 语法
- 遵循 PEP 8 编码规范
- 使用有意义的变量和函数名
- 添加适当的注释和文档字符串

### 提交信息

使用清晰的提交信息：
- `feat: 添加新功能`
- `fix: 修复bug`
- `docs: 更新文档`
- `test: 添加测试`
- `refactor: 重构代码`
- `style: 代码格式化`

### 测试

- 为新功能添加测试
- 确保所有测试通过
- 测试覆盖率应保持在合理水平

## 🔧 开发设置

### 环境要求

- Python 3.7+
- MySQL 5.7+
- Docker（可选）

### 数据库设置

```sql
CREATE DATABASE airouter_dev;
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

### 配置文件

复制并配置API密钥：
```bash
cp ew_config/api_keys.py ew_config/api_keys_local.py
# 编辑 api_keys_local.py 填入测试用的API密钥
```

## 🧪 测试指南

### 运行测试

```bash
# 单元测试
pytest tests/unit/

# 集成测试
pytest tests/integration/

# 性能测试
python tests/performance_test.py

# 所有测试
pytest tests/
```

### 测试覆盖率

```bash
pip install pytest-cov
pytest --cov=AIRouter tests/
```

## 📝 文档

### 更新文档

- 为新功能添加文档
- 更新 README.md
- 添加代码示例
- 更新 API 文档

### 文档风格

- 使用清晰的中文
- 提供代码示例
- 包含参数说明
- 添加使用场景

## 🔒 安全注意事项

- 不要在代码中硬编码API密钥
- 使用环境变量管理敏感信息
- 不要提交包含真实API密钥的文件
- 遵循安全最佳实践

## 📦 发布流程

1. 更新版本号
2. 更新 CHANGELOG.md
3. 创建 GitHub Release
4. 发布到 PyPI（维护者）

## 🤝 社区准则

- 尊重他人
- 友好交流
- 建设性反馈
- 包容多样性

## 📞 联系方式

- 创建 Issue：[GitHub Issues](https://github.com/your-username/AIRouter/issues)
- 讨论：[GitHub Discussions](https://github.com/your-username/AIRouter/discussions)

## 🙏 致谢

感谢所有贡献者的努力！您的贡献使这个项目更加完善。 