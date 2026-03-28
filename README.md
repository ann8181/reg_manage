# Auto Register Tasks v2.0

整合各种邮箱注册和 AI 服务注册任务的模块化系统，支持分层勾选执行。

## 新版本特性

- **模块化架构**：核心功能与任务实现分离
- **Provider 抽象层**：统一的邮箱服务接口，支持 14+ 提供商
- **故障转移链**：多 Provider 自动切换，保障服务可用性
- **异步执行**：支持高并发任务执行
- **插件机制**：支持任务插件的自动发现
- **数据库存储**：SQLAlchemy 持久化存储
- **REST API**：FastAPI 提供完整的 REST 接口
- **Web 管理界面**：Gradio 可视化操作界面

## 功能特性

- 模块化设计：每个任务独立模块，可按需启用/禁用
- 分层结构：Category -> Group -> Task 三层勾选
- 灵活执行：支持按分类、组或单个任务执行
- 账户管理：自动保存注册账户到数据库和文件
- 日志系统：完整的运行日志、错误日志和截图功能
- API 服务：完整的 REST API 接口
- Web 界面：可视化任务管理和监控

## 安装

```bash
pip install -r requirements.txt
playwright install chromium
```

## 配置

编辑 `.env` 文件或创建 `config.json`：

```bash
cp .env.example .env
```

## 使用方法

### 命令行

```bash
# 列出所有任务
python main.py list

# 启用任务
python main.py enable email.outlook

# 禁用任务
python main.py disable email.outlook

# 运行任务
python main.py run email.outlook
```

### 启动服务

```bash
# 启动 API 服务 (port 8000)
./start.sh api

# 启动 Web 界面 (port 7860)
./start.sh web

# 启动所有服务
./start.sh all
```

### API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务状态 |
| `/health` | GET | 健康检查 |
| `/tasks` | GET | 获取所有任务 |
| `/tasks/{task_id}/enable` | POST | 启用任务 |
| `/tasks/{task_id}/disable` | POST | 禁用任务 |
| `/run/{task_id}` | POST | 执行任务 |
| `/email/create` | POST | 创建临时邮箱 |
| `/email/{email}/messages` | GET | 获取邮件列表 |
| `/providers` | GET | 获取提供商列表 |

### Web 界面

启动后访问 http://localhost:7860

功能：
- 任务列表查看和管理
- 临时邮箱创建和邮件获取
- 任务执行和结果查看
- 统计信息展示

## 项目结构

```
auto-register-tasks/
├── api/                    # FastAPI 服务
│   └── main.py            # REST API 入口
├── core/                  # 核心框架
│   ├── providers/         # Email Provider 抽象层
│   │   ├── base.py       # 基类和异常定义
│   │   ├── factory.py    # Provider 工厂
│   │   ├── chain.py      # 故障转移链
│   │   └── *.py          # 各 Provider 实现
│   ├── base.py           # 基类定义
│   ├── task_manager.py   # 任务管理器
│   ├── executor.py       # 执行器
│   ├── async_executor.py # 异步执行器
│   ├── logger.py         # 日志系统
│   ├── config.py         # 配置管理
│   ├── database.py       # 数据库
│   └── plugin_manager.py # 插件管理
├── web/                   # Web 管理界面
│   └── app.py            # Gradio 应用
├── tests/                 # 测试
│   ├── conftest.py
│   ├── test_providers/
│   └── test_core/
├── tasks/                 # 任务模块
│   ├── email/
│   ├── ai/
│   ├── sms/
│   ├── proxy/
│   ├── captcha/
│   └── tools/
├── config/
│   └── tasks.json        # 任务配置
├── config.json           # 全局配置
├── main.py              # CLI 入口
├── start.sh             # 服务启动脚本
└── requirements.txt     # 依赖
```

## Email Provider 支持

### API Providers

| Provider | 类名 | 状态 |
|----------|------|------|
| Mail.tm | MailTmProvider | 完整支持 |
| GuerrillaMail | GuerrillaMailProvider | 完整支持 |
| GetNada | GetNadaProvider | 完整支持 |
| YopMail | YopMailProvider | 完整支持 |
| 1SecMail | OneSecMailProvider | 完整支持 |
| TempMail.org | TempMailOrgProvider | 完整支持 |
| FakeMail | FakeMailProvider | 完整支持 |
| Gmailnator | GmailnatorProvider | 完整支持 |
| Mailsac | MailsacProvider | 需 API Key |
| Temp Mail Asia | TempMailAsiaProvider | Web 转 API |
| Emailnator | EmailnatorProvider | 完整支持 |
| InboxKitten | InboxKittenProvider | 完整支持 |
| TempMail Plus | TempMailPlusProvider | 完整支持 |
| TempMail.lol | TempMailLolProvider | 完整支持 |

### 故障转移使用

```python
from core.providers.factory import ProviderFactory
from core.providers.chain import ProviderChain

# 创建故障转移链
chain = ProviderChain()
chain.add_provider(ProviderFactory.create("mailtm"))
chain.add_provider(ProviderFactory.create("guerrillamail"))
chain.add_provider(ProviderFactory.create("getnada"))

# 自动故障转移创建邮箱
email, password, provider_name = chain.create_email()
```

## 测试

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_providers/test_mailtm.py -v
```

## API 使用示例

```python
import requests

# 创建邮箱
response = requests.post("http://localhost:8000/email/create", json={
    "provider": "mailtm"
})
email_data = response.json()
print(f"Email: {email_data['email']}")

# 获取邮件
response = requests.get(f"http://localhost:8000/email/{email_data['email']}/messages", params={
    "provider": "mailtm"
})
messages = response.json()
```

## 注意事项

1. IP 质量对注册成功率有很大影响
2. 同一 IP 短时间内不宜多次注册
3. 临时邮箱可能有延迟，建议增加等待时间
4. 请勿用于非法用途

## License

MIT
