# Trae + Outlook Account Registration Tool

整合 Outlook 邮箱注册和 Trae 账号注册的自动化工具。

## 功能特性

- 先注册真实的 Outlook 邮箱
- 使用注册的 Outlook 邮箱注册 Trae 账号
- 自动领取 Trae 周年礼包
- 导出账号信息到本地文件

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
    "max_tasks": 50
}
```

- `browser_path`: 指纹浏览器路径（留空使用默认Chrome）
- `proxy`: 代理服务器地址
- `Bot_protection_wait`: 人机验证等待时间（秒）
- `concurrent_flows`: 并发数量
- `max_tasks`: 最大任务数量

## 使用方法

```bash
python register.py [total] [concurrency]
```

示例：
```bash
python register.py 1    # 注册1个账号
python register.py 10 5  # 并发注册10个账号，每批5个
```

## 输出文件

- `Results/outlook_accounts.txt`: Outlook 账号列表
- `TraeAccounts/accounts.txt`: Trae 账号列表

## 注意事项

1. IP质量对注册成功率有很大影响
2. 同一IP短时间内不宜多次注册
3. 请勿用于非法用途
