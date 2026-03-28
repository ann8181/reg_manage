# Auto Register Tasks v3.0

基于一体化内核架构的自动化任务管理平台

## 核心架构

```
┌─────────────────────────────────────────────────┐
│                    Kernel (统一内核)                │
│  - 配置管理    - 数据库管理                        │
│  - 日志系统    - 事件驱动                        │
│  - 模块注册    - 资源调度                         │
└────────────────────┬────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         ▼                         ▼
┌─────────────────┐      ┌─────────────────┐
│modules/scheduler │      │ modules/browser  │
│  Cron/Interval  │      │  Camoufox/UC/DP │
└─────────────────┘      └─────────────────┘
         ┌─────────────────┐
         │modules/workflow │
         │  任务编排引擎   │
         └─────────────────┘
         ┌─────────────────┐
         │ modules/provider │
         │  14+ Email     │
         └─────────────────┘
         ┌─────────────────┐
         │  modules/user   │
         │  用户权限管理   │
         └─────────────────┘
```

## 快速开始

```bash
# 启动API
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000

# 或使用start脚本
./start.sh api
```

## 使用方式

### Python API

```python
from kernel import get_kernel

kernel = get_kernel()

# 创建邮箱
email, password = kernel.provider.create_email("mailtm")

# 创建调度
kernel.scheduler.add_schedule(
    name="Daily Task",
    task_id="my_task",
    schedule_type="cron",
    cron_expr="0 2 * * *"
)

# 执行工作流
wf = kernel.workflow.create_workflow("注册流程")
kernel.workflow.execute_workflow(wf.id)
```

### REST API

```bash
# 健康检查
curl http://localhost:8000/health

# 创建邮箱
curl -X POST http://localhost:8000/email/create?provider=mailtm

# 创建调度
curl -X POST http://localhost:8000/schedules \
  -d "name=test&task_id=my_task&schedule_type=cron&cron_expr=0 2 * * *"

# 执行工作流
curl -X POST http://localhost:8000/workflows/my_wf_id/run
```

## 目录结构

```
auto-register-tasks/
├── kernel/              # 统一内核
│   └── __init__.py     # Kernel类
├── modules/            # 功能模块
│   ├── scheduler/      # 任务调度
│   ├── browser/        # 浏览器管理
│   ├── workflow/       # 工作流引擎
│   ├── provider/       # 服务提供商
│   ├── user/           # 用户权限
│   └── task/           # 任务定义
├── api/               # REST API
│   └── main.py
├── web/               # Web界面
├── data/               # 数据目录
├── config/             # 配置
└── requirements.txt
```

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/stats` | GET | 系统统计 |
| `/schedules` | GET/POST | 调度管理 |
| `/workflows` | GET/POST | 工作流管理 |
| `/browsers` | GET | 浏览器配置 |
| `/auth/login` | POST | 用户登录 |
| `/providers` | GET | Provider列表 |
| `/email/create` | POST | 创建邮箱 |

## 调度类型

- `cron` - Cron表达式，如 `0 2 * * *`
- `interval` - 间隔秒数
- `once` - 单次执行
- `manual` - 手动触发

## 浏览器类型

- `camoufox` - 过CF首选
- `undetected` - Undetected Chrome
- `drission` - DrissionPage
- `playwright` - Playwright
