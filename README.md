# Auto Register Tasks v2.0

整合各种邮箱注册和 AI 服务注册任务的模块化系统，支持分层勾选执行。

## 核心特性

- **统一Agent接口** - `agent.py` 提供一站式API
- **Persona系统** - 身份、代理、账号管理
- **Provider抽象层** - 14+ 临时邮箱服务
- **结构化日志** - 浏览器操作追踪、截图、性能指标
- **REST API** - FastAPI 提供完整的 REST 接口
- **Web管理界面** - Gradio 可视化操作界面

## 项目结构

```
auto-register-tasks/
├── agent.py                  # 统一Agent接口 (新建)
├── api/                      # FastAPI 服务
│   └── main.py              # REST API
├── core/                    # 核心框架
│   ├── persona/             # Persona系统 (身份/代理/账号)
│   │   ├── generator.py    # 身份生成
│   │   ├── proxy_pool.py   # 代理池
│   │   ├── manager.py      # 账号管理
│   │   └── selector.py     # 身份选择
│   ├── providers/           # Email Providers (API调用)
│   │   ├── factory.py      # Provider工厂
│   │   ├── chain.py       # 故障转移链
│   │   └── *.py           # 14+ Provider实现
│   ├── base.py             # 任务基类
│   ├── browser_task.py     # 浏览器任务基类
│   ├── task_manager.py     # 任务管理
│   ├── executor.py         # 执行器
│   ├── logger.py           # 日志系统
│   └── log_analyzer.py     # 日志分析
├── tasks/                   # 任务模块
│   ├── register/           # 注册任务 (浏览器)
│   │   ├── ai/            # 31个AI服务注册
│   │   └── email/          # 2个邮箱注册
│   ├── provider/           # 服务提供商 (API)
│   │   ├── email/          # 14个临时邮箱
│   │   └── sms/            # 短信服务
│   └── tools/              # 工具
│       ├── generator/       # 数据生成
│       └── captcha/        # 验证码
├── web/                     # Web管理界面
│   └── app.py              # Gradio应用
├── main.py                  # CLI入口
├── start.sh                # 服务启动脚本
└── requirements.txt        # 依赖
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 启动API服务 (port 8000)
./start.sh api

# 启动Web界面 (port 7860)
./start.sh web
```

## Agent API

```python
from agent import Agent, create_agent

agent = create_agent()

# 创建临时邮箱
result = agent.create_email("mailtm")
print(result)  # {"success": True, "email": "xxx@mail.tm", "password": "xxx"}

# 获取邮件
messages = agent.get_messages(result["email"], "mailtm")

# 生成身份
identity = agent.generate_identity("US")

# 获取代理
proxy = agent.get_proxy("US")

# 注册账号
account = agent.register_account("github", email, password)

# 运行任务
agent.run_task("register.ai.github")
```

## 日志系统

```
logs/
└── {task_id}/
    ├── {task_id}.log           # 文本日志
    ├── {task_id}.jsonl         # JSON日志
    ├── screenshots/             # 浏览器截图
    │   └── browser_actions/     # 每步操作截图
    └── metrics/                 # 性能指标
```

## Email Providers (14+)

| Provider | 状态 |
|----------|------|
| Mail.tm | 完整支持 |
| GuerrillaMail | 完整支持 |
| GetNada | 完整支持 |
| YopMail | 完整支持 |
| 1SecMail | 完整支持 |
| TempMail.org | 完整支持 |
| FakeMail | 完整支持 |
| Gmailnator | 完整支持 |
| Mailsac | 需API Key |
| Temp Mail Asia | 完整支持 |
| Emailnator | 完整支持 |
| InboxKitten | 完整支持 |
| TempMail Plus | 完整支持 |
| TempMail.lol | 完整支持 |

## License

MIT
