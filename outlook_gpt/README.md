# Outlook GPT Register

基于 Outlook 邮箱的 ChatGPT 账号自动注册工具，支持获取 Codex Access Token。

## 功能

- 使用 Outlook 邮箱接收验证邮件，无需短信验证
- 自动注册真实的 Outlook 邮箱（或使用已有邮箱）
- 自动完成 ChatGPT 账号注册流程
- 自动获取 Codex OAuth Access Token
- 支持 headless 模式运行

## 环境要求

- Python 3.8+
- Chrome/Chromium 浏览器
- `playwright install chromium` 安装浏览器

## 安装

```bash
cd outlook_gpt
pip install -r requirements.txt
playwright install chromium
```

## 配置

1. 复制 `.env.example` 为 `.env`:

```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置以下信息：

| 配置项 | 说明 |
|--------|------|
| `OUTLOOK_EMAIL` | 你的 Outlook 邮箱地址（可选，不填则自动注册新邮箱） |
| `OUTLOOK_PASSWORD` | 你的 Outlook 密码 |
| `HEADLESS` | 是否使用无头模式运行（true/false） |

## 使用

```bash
python register.py
```

## 工作流程

### 模式1：使用已有 Outlook 邮箱
1. 使用 Microsoft Graph API 认证 Outlook 邮箱
2. 启动浏览器自动化，打开 ChatGPT 注册页面
3. 填写邮箱地址，触发验证邮件
4. 通过 Graph API 监控邮箱，获取验证链接
5. 完成邮箱验证
6. 填写用户名和生日信息
7. 执行 OAuth 流程获取 Codex Access Token
8. 保存结果到文件

### 模式2：自动注册新 Outlook 邮箱
1. 使用 Camoufox 自动化注册新的 Outlook 邮箱
2. 使用新邮箱注册 ChatGPT（复用模式1的后续流程）

## 输出文件

- `Results/outlook_accounts.txt` - Outlook 账号列表
- `Results/registered_accounts.txt` - ChatGPT 注册账号信息
- `CodexTokens/` - Codex OAuth Token JSON 文件
- `CodexTokens/access_tokens.txt` - Access Token 列表
- `CodexTokens/refresh_tokens.txt` - Refresh Token 列表

## 核心组件

### OutlookMailClient
- 使用 Microsoft OAuth2 认证
- 通过 Graph API 读取邮件
- 支持获取验证链接或6位验证码

### Camoufox 浏览器自动化
- 反检测浏览器自动化
- 用于 Outlook 邮箱注册
- 用于 ChatGPT 注册流程

### Codex OAuth
- PKCE 代码挑战
- OAuth2 授权码流程
- Token 交换和存储

## 注意事项

- 确保网络可以正常访问 OpenAI 和 Microsoft
- 部分地区可能需要代理才能访问
- 如果注册失败，可能是 IP 被限制，稍后重试
- 建议使用高质量 IP 以提高成功率

## 免责声明

本项目仅供学习交流使用，请遵守 OpenAI 和 Microsoft 的服务条款。
