# Auto Register Tasks v3.0

企业级自动化任务管理平台，支持任务调度、工作流编排、浏览器管理和多用户协作。

## 核心特性

### 任务管理
- **单个任务执行** - 支持所有注册任务
- **批量任务执行** - 并发/串行批量运行
- **定时任务** - Cron表达式、间隔执行
- **工作流编排** - 可视化任务编排

### 浏览器管理
- **多浏览器支持** - Camoufox(过CF)、Undetected Chrome、DrissionPage、Playwright
- **版本管理** - 浏览器版本配置
- **反检测配置** - CSS/JS隐身模式

### 系统管理
- **用户权限** - 多用户、角色权限
- **模块管理** - 独立模块版本控制
- **统一API** - FastAPI REST接口
- **Web管理** - Gradio可视化界面

## 快速开始

```bash
# 启动API服务
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 启动Web管理界面
python web/app.py
```

## 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                      API / Web Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Tasks   │  │ Schedules│  │ Workflows│  │ Browsers │ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       └───────────────┴───────────┴───────────┴──────────────┘ │
│                         Manager Layer                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │Scheduler │  │ Browser  │  │  User    │  │ Module   │ │
│  │ (APScheduler)│ │ Manager │  │ Manager  │  │ Manager  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
├─────────────────────────────────────────────────────────────┤
│                        Core Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ Persona  │  │ Providers│  │ Executor │  │  Logger  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## 项目结构

```
auto-register-tasks/
├── manager/                    # 管理系统
│   ├── scheduler/             # 任务调度 (APScheduler)
│   │   ├── scheduler.py      # 调度器核心
│   │   └── trigger.py        # 触发器定义
│   ├── browser/              # 浏览器管理
│   │   ├── manager.py       # 浏览器管理器
│   │   ├── camoufox.py      # Camoufox适配器
│   │   ├── uc.py            # Undetected Chrome适配器
│   │   └── drission.py      # DrissionPage适配器
│   ├── workflow/            # 工作流引擎
│   │   ├── engine.py        # 工作流核心
│   │   └── nodes.py         # 步骤节点
│   ├── user/                # 用户权限
│   │   └── user.py          # 用户管理
│   ├── account/             # 账号管理
│   └── module/              # 模块管理
│
├── core/                     # 核心模块
│   ├── persona/             # 身份管理
│   ├── providers/            # 14+ Email Providers
│   ├── browser_task.py      # 浏览器任务基类
│   ├── logger.py            # 结构化日志
│   └── task_manager.py       # 任务管理
│
├── tasks/                    # 任务模块
│   ├── register/            # 注册任务 (浏览器)
│   │   ├── ai/             # 31个AI服务
│   │   └── email/          # 邮箱注册
│   ├── provider/            # 服务提供商 (API)
│   │   ├── email/          # 14个临时邮箱
│   │   └── sms/            # 短信服务
│   └── tools/              # 工具
│       ├── generator/       # 数据生成
│       └── captcha/         # 验证码
│
├── api/                     # FastAPI服务
│   └── main.py             # REST API
│
├── web/                     # Web管理界面
│   └── app.py              # Gradio应用
│
├── agent.py                 # 统一Agent接口
├── main.py                 # CLI入口
└── start.sh               # 启动脚本
```

## API 端点

### 任务管理
| 端点 | 方法 | 说明 |
|------|------|------|
| `/tasks` | GET | 任务列表 |
| `/tasks/{id}/enable` | POST | 启用任务 |
| `/tasks/{id}/disable` | POST | 禁用任务 |
| `/tasks/{id}/run` | POST | 执行任务 |

### 调度管理
| 端点 | 方法 | 说明 |
|------|------|------|
| `/schedules` | GET | 调度列表 |
| `/schedules` | POST | 创建调度 |
| `/schedules/{id}/run` | POST | 立即执行 |
| `/schedules/{id}/pause` | POST | 暂停 |
| `/schedules/{id}/resume` | POST | 恢复 |

### 浏览器管理
| 端点 | 方法 | 说明 |
|------|------|------|
| `/browsers` | GET | 浏览器配置列表 |
| `/browsers` | POST | 添加浏览器配置 |
| `/browsers/stats` | GET | 浏览器统计 |

### 工作流
| 端点 | 方法 | 说明 |
|------|------|------|
| `/workflows` | GET | 工作流列表 |
| `/workflows` | POST | 创建工作流 |
| `/workflows/{id}/run` | POST | 执行工作流 |

### 用户管理
| 端点 | 方法 | 说明 |
|------|------|------|
| `/users` | GET | 用户列表 |
| `/auth/login` | POST | 用户登录 |
| `/auth/logout` | POST | 用户登出 |

### 仪表盘
| 端点 | 方法 | 说明 |
|------|------|------|
| `/dashboard/stats` | GET | 系统统计 |

## 调度类型

```python
# Cron表达式调度
scheduler.create_schedule(
    name="Daily GitHub",
    task_id="register.ai.github",
    schedule_type="cron",
    cron_expr="0 2 * * *"  # 每天凌晨2点
)

# 间隔调度
scheduler.create_schedule(
    name="Every 5 minutes",
    task_id="provider.email.mailtm",
    schedule_type="interval",
    interval_seconds=300
)

# 批量执行
scheduler.create_schedule(
    name="Batch Registration",
    task_id="register.ai.github",
    schedule_type="interval",
    interval_seconds=60,
    batch_size=10,  # 每次执行10个
    batch_delay=5     # 每个间隔5秒
)
```

## 工作流示例

```python
workflow = workflow_engine.create_workflow(
    name="AI Service Registration",
    description="批量注册AI服务"
)

# 添加步骤
workflow_engine.add_step(workflow.id, WorkflowStep(
    id="1",
    name="Create Email",
    step_type=StepType.TASK,
    task_id="provider.email.mailtm"
))

workflow_engine.add_step(workflow.id, WorkflowStep(
    id="2", 
    name="Register GitHub",
    step_type=StepType.TASK,
    task_id="register.ai.github"
))

workflow_engine.add_step(workflow.id, WorkflowStep(
    id="3",
    name="Register Claude",
    step_type=StepType.TASK,
    task_id="register.ai.claude"
))

# 连接步骤
workflow_engine.add_edge(workflow.id, "1", "2")
workflow_engine.add_edge(workflow.id, "2", "3")

# 执行
workflow_engine.execute_workflow(workflow.id)
```

## 浏览器配置

```python
from manager.browser import BrowserConfig, BrowserType

# 添加自定义浏览器
browser_manager.add_config(BrowserConfig(
    id="my-cf-browser",
    name="My CF Browser",
    browser_type=BrowserType.CAMOUFOX,
    headless=False,
    css_stealth=True,
    js_stealth=True,
    proxy="http://proxy:8080",
    priority=100
))
```

## License

MIT
