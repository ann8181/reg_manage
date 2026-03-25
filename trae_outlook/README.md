# Trae + Outlook + Kiro Account Registration Tool

整合 Outlook 邮箱注册、Trae AI 和 Kiro CLI 账号注册的自动化工具。

## 功能特性

- 先注册真实的 Outlook 邮箱
- 使用注册的 Outlook 邮箱注册 Trae 账号
- 支持 Kiro CLI 账号注册（通过 OAuth 或临时邮箱）
- 自动领取周年礼包（Trae）
- 导出账号信息到本地文件
- 支持多种临时邮箱 API 提供者

## 支持的临时邮箱服务

| 提供者 | 配置值 | 说明 |
|--------|--------|------|
| Temp Mail Asia | `temp-mail-asia` | 快速随机邮箱生成 |
| Temp Mail Awsl | `temp-mail-awsl` | Cloudflare 版本，功能丰富 |
| Guerrilla Mail | `guerrilla-mail` | 老牌临时邮箱服务 |
| MailDrop | `maildrop` | 简洁的临时邮箱服务 |

## 环境要求

- Python 3.8+
- Windows / Linux / macOS

## 安装步骤

```bash
cd trae_outlook
pip install -r requirements.txt
playwright install chromium
```

## 配置

编辑 `config.json` 文件：

```json
{
    "browser_path": "",
    "proxy": "",
    "Bot_protection_wait": 12,
    "max_captcha_retries": 2,
    "concurrent_flows": 5,
    "max_tasks": 50,
    "outlook_results_dir": "Results",
    "trae_results_dir": "TraeAccounts",
    "kiro_results_dir": "KiroAccounts",
    "temp_email_provider": "temp-mail-asia",
    "temp_mail_awsl_url": "",
    "temp_mail_awsl_jwt": ""
}
```

### 配置说明

| 配置项 | 说明 |
|--------|------|
| `browser_path` | 指纹浏览器路径（留空使用默认Chrome） |
| `proxy` | 代理服务器地址 |
| `Bot_protection_wait` | 人机验证等待时间（秒） |
| `concurrent_flows` | 并发数量 |
| `max_tasks` | 最大任务数量 |
| `temp_email_provider` | 临时邮箱提供者：`temp-mail-asia`、`temp-mail-awsl`、`guerrilla-mail`、`maildrop` |
| `temp_mail_awsl_url` | Temp Mail Awsl 自定义部署地址（可选） |
| `temp_mail_awsl_jwt` | Temp Mail Awsl JWT 密码（可选） |

## 使用方法

### 注册 Trae + Outlook 账号

```bash
python register.py trae [total] [concurrency]
```

### 注册 Kiro 账号

```bash
python register.py kiro [total] [concurrency]
```

### 注册所有账号

```bash
python register.py all [total] [concurrency]
```

示例：
```bash
python register.py trae 1    # 注册1个 Trae 账号
python register.py kiro 10 5 # 并发注册10个 Kiro 账号，每批5个
python register.py all 50 10 # 注册50个账号，每批10个
```

## 输出文件

- `Results/outlook_accounts.txt`: Outlook 账号列表
- `TraeAccounts/accounts.txt`: Trae 账号列表
- `KiroAccounts/accounts.txt`: Kiro 账号列表

## 临时邮箱 API 使用

### Temp Mail Asia（默认）

无需配置，直接使用。API 会自动生成随机邮箱地址。

### Temp Mail Awsl（自部署）

如果使用自部署的 Cloudflare Temp Email：

```json
{
    "temp_email_provider": "temp-mail-awsl",
    "temp_mail_awsl_url": "https://your-worker.workers.dev",
    "temp_mail_awsl_jwt": "your-jwt-password"
}
```

### Guerrilla Mail

无需配置，直接使用。

### MailDrop

无需配置，直接使用。

## Kiro 注册方式

### 方式一：临时邮箱注册

使用临时邮箱 API 接收验证邮件。

### 方式二：OAuth 设备码流程

Kiro CLI 使用 OAuth 设备码认证，浏览器验证后自动完成注册。

## 注意事项

1. IP质量对注册成功率有很大影响
2. 同一IP短时间内不宜多次注册
3. 临时邮箱可能有延迟，建议增加等待时间
4. 请勿用于非法用途
