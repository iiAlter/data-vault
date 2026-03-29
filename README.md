# DataVault

> 个人数据保险箱 — 收藏链接、消费记录、端口监控

![](https://img.shields.io/badge/Python-3.10+-blue) ![](https://img.shields.io/badge/Flask-3.x-green) ![](https://img.shields.io/badge/License-MIT-orange)

---

## 功能一览

| 模块 | 说明 |
|------|------|
| 📂 收藏 | 链接收藏、分类标签、来源平台、搜索过滤 |
| 💰 消费 | 消费记录、按月/分类统计、趋势图表 |
| 🔌 端口 | 实时监听端口 + 进程映射 |
| ⚙️ 设置 | 隐藏导航标签、Token 管理 |

---

## 快速开始

### 环境要求

- Python 3.10+
- SQLite3
- macOS / Linux / Windows（WSL）

### 安装

```bash
git clone git@github.com:iiAlter/data-vault.git
cd data-vault
python3 -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

### 配置 Token

Token 用于保护所有 API 和页面访问。

**方式一：自动生成（首次启动时）**
```bash
python3 app.py
# 首次启动会在 ~/.data-vault-token 生成随机 Token
```

**方式二：手动指定环境变量**
```bash
export DATA_VAULT_TOKEN="你的Token"
python3 app.py
```

### 启动

```bash
python3 app.py
# 访问 http://localhost:18001
```

---

## 远程访问

DataVault 默认只在本地监听。由于服务器端口限制，仅支持 **17000-20000** 范围。

**通过 SSH 隧道访问（推荐）：**

```bash
# 在本地执行
ssh -NfL 18001:localhost:18001 yuholy@100.91.230.121
# 然后访问 http://localhost:18001
```

---

## 项目结构

```
data-vault/
├── app.py              # Flask 路由 + 认证中间件
├── database.py         # SQLite 所有 CRUD 操作
├── schema.sql          # 数据库表结构 + 索引定义
├── requirements.txt    # Python 依赖
├── templates/          # HTML 模板
│   ├── base.html       # 公共布局 + CSS 变量
│   ├── index.html      # 总览页（服务端渲染 stats）
│   ├── links.html      # 收藏页
│   ├── expenses.html   # 消费页
│   ├── ports.html      # 端口监控页
│   ├── settings.html   # 设置页
│   └── login.html      # Token 登录页
└── static/             # 静态资源
    └── logo.svg       # 网站 Logo
```

---

## API 参考

所有 API 需要在 Header 中携带 Token：

```
Authorization: Bearer <your_token>
```

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/stats` | GET | 全局统计数据（收藏 + 消费） |
| `/api/links` | GET | 收藏列表（支持 category/search 过滤） |
| `/api/links` | POST | 添加收藏 |
| `/api/links/stats` | GET | 收藏分类统计 |
| `/api/expenses` | GET | 消费列表（支持 month/category 过滤） |
| `/api/expenses` | POST | 添加消费记录 |
| `/api/expenses/stats` | GET | 消费分类统计 |
| `/api/ports` | GET | 端口监听列表 |
| `/api/token-verify` | POST | 验证 Token（登录接口） |
| `/api/logout` | POST | 退出登录 |
| `/api/me` | GET | 当前认证状态 |

---

## 数据库

SQLite 数据库位于 `data/vault.db`。

### 主要表

**links** — 收藏链接
```
id, url, title, source, summary, category, tags(JSON),
collected_at, note, created_at
```

**expenses** — 消费记录
```
id, amount, currency, category, description, date, created_at
```

### 索引

已创建索引加速统计查询：
- `idx_links_category` / `idx_links_source`
- `idx_expenses_date` / `idx_expenses_category`
- `idx_expenses_date_category`

---

## 主题

支持浅色 / 深色模式，点击右上角「浅色 / 深色」切换。

主题偏好保存在 `localStorage` 中。

---

## 部署注意

- 数据库文件 `data/vault.db` 包含实际数据，**不要提交到 Git**
- 首次部署需要初始化数据库：
  ```bash
  sqlite3 data/vault.db < schema.sql
  ```

---

## License

MIT
