# Auto Register Tasks

整合各种邮箱注册和 AI 服务注册任务的模块化系统，支持分层勾选执行。

## 功能特性

- 模块化设计：每个任务独立模块，可按需启用/禁用
- 分层结构：Category -> Group -> Task 三层勾选
- 灵活执行：支持按分类、组或单个任务执行
- 账户管理：自动保存注册账户到结果文件

## 任务列表

### 邮箱任务 (email)

#### 临时邮箱 API (temp_email)

| 任务ID | 名称 | 说明 |
|--------|------|------|
| email.mailtm | Mail.tm API | Mail.tm 临时邮箱 API |
| email.guerrillamail | GuerrillaMail API | GuerrillaMail 临时邮箱 API |
| email.getnada | GetNada API | GetNada 临时邮箱 API |
| email.yopmail | YopMail API | YopMail 临时邮箱 API (仅收取) |

#### 真实邮箱注册 (real_email)

| 任务ID | 名称 | 说明 |
|--------|------|------|
| email.outlook | Outlook 注册 | 微软 Outlook 邮箱注册 + 邮件收取 |
| email.gmail | Gmail 邮件收取 | Gmail IMAP 邮件收取 |

#### 临时邮箱转换 (temp_convert)

| 任务ID | 名称 | 说明 |
|--------|------|------|
| email.tempmail | TempMail 转换 | Web 临时邮箱转 API 版本 |

### AI 服务任务 (ai)

#### 免费 AI API (free_ai)

| 任务ID | 名称 | 说明 |
|--------|------|------|
| ai.github | GitHub 注册 | GitHub 账号注册 (用于 Copilot 等) |
| ai.claude | Claude 注册 | Anthropic Claude AI 注册 |
| ai.gpt | GPT 注册 | OpenAI GPT API 注册 |
| ai.gemini | Gemini 注册 | Google Gemini AI 注册 |
| ai.aistudio | AI Studio 注册 | Google AI Studio 注册 |
| ai.business_gemini | Business Gemini | Google Business Gemini 注册 |
| ai.grok | Grok 注册 | xAI Grok 注册 |

#### 编程 AI 工具 (coding_ai)

| 任务ID | 名称 | 说明 |
|--------|------|------|
| ai.copilot | Copilot 注册 | GitHub Copilot 注册 |
| ai.cursor | Cursor AI 注册 | Cursor AI IDE 注册 |
| ai.augment | Augment AI 注册 | Augment AI 注册 |
| ai.windsurf | Windsurf AI 注册 | Windsurf AI IDE 注册 |
| ai.codex | Codex 授权 | OpenAI Codex API 授权 |

#### 国产 AI 工具 (chinese_ai)

| 任务ID | 名称 | 说明 |
|--------|------|------|
| ai.trae | Trae 注册 | Trae AI IDE 注册 |
| ai.opencode | OpenCode 注册 | OpenCode AI 注册 |
| ai.kiro | Kiro AI 注册 | Kiro CLI AI 注册 |
| ai.zen | Zen AI 注册 | Zen AI IDE 注册 |
| ai.nvidia | NVIDIA 注册 | NVIDIA AI 注册 |

## 安装

```bash
pip install -r requirements.txt
playwright install chromium
```

## 配置

编辑 `config.json` 文件：

```json
{
    "browser_path": "",
    "proxy": "",
    "bot_protection_wait": 12,
    "max_captcha_retries": 2,
    "concurrent_flows": 5,
    "max_tasks": 50,
    "results_base_dir": "results",
    "temp_email_provider": "temp-mail-asia"
}
```

## 使用方法

### 列出所有任务

```bash
python main.py list
```

### 启用/禁用任务

```bash
python main.py enable email              # 启用所有邮箱任务
python main.py enable email.outlook      # 启用 Outlook 注册任务
python main.py disable email.outlook     # 禁用 Outlook 注册任务
python main.py disable-all               # 禁用所有任务
```

### 运行任务

```bash
python main.py run                       # 运行所有已启用的任务
python main.py run email                 # 运行所有邮箱任务
python main.py run ai                    # 运行所有AI服务任务
python main.py run email.outlook         # 只运行 Outlook 注册任务
```

## 任务配置

任务配置存储在 `config/tasks.json` 中，可以直接编辑该文件来调整任务设置：

```json
{
    "categories": {
        "email": {
            "groups": {
                "temp_email": {
                    "tasks": {
                        "email.mailtm": {
                            "enabled": true,
                            "module": "tasks.email.mailtm",
                            "class": "MailTmTask"
                        }
                    }
                }
            }
        }
    }
}
```

## 输出结果

注册账户保存在 `results/` 目录下的各任务目录中：

```
results/
├── mailtm/accounts.txt
├── outlook/accounts.txt
├── github/accounts.txt
└── ...
```

## 项目结构

```
auto-register-tasks/
├── config/
│   └── tasks.json          # 任务配置清单
├── core/
│   ├── __init__.py
│   ├── base.py              # 基类定义
│   ├── task_manager.py      # 任务管理器
│   └── executor.py          # 执行器
├── tasks/
│   ├── email/               # 邮箱任务模块
│   │   ├── mailtm.py
│   │   ├── guerrillamail.py
│   │   ├── getnada.py
│   │   ├── yopmail.py
│   │   ├── outlook.py
│   │   ├── gmail.py
│   │   └── tempmail.py
│   └── ai/                  # AI服务任务模块
│       ├── github.py
│       ├── claude.py
│       ├── copilot.py
│       └── ...
├── results/                 # 账户结果存储
├── config.json              # 全局配置
├── main.py                  # 主入口
└── README.md
```

## 参考项目

本项目整合参考了以下开源工具：

- [trae_outlook](https://github.com/your-repo/trae_outlook) - Outlook + Trae 账号注册
- Mail.tm API
- GuerrillaMail API
- GetNada API
- YopMail API
- 各种 AI 服务的官方注册流程

## 注意事项

1. IP 质量对注册成功率有很大影响
2. 同一 IP 短时间内不宜多次注册
3. 临时邮箱可能有延迟，建议增加等待时间
4. 请勿用于非法用途
