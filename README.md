# SubLedger - 自托管中文订阅管理工具

一个轻量级的自托管订阅管理工具，帮助你追踪和管理各种订阅服务（流媒体、云存储、会员等），支持多货币、汇率换算、支出统计和到账提醒。

## 功能

- **订阅管理**：CRUD 管理订阅，支持月/季/年计费周期
- **多货币**：支持 CNY、USD、EUR 等多种货币，自动汇率换算
- **仪表盘**：月度支出统计、分类图表、扣款日历
- **通知提醒**：应用内提示、邮件（SMTP）、Bark 推送、Server酱推送
- **数据导入导出**：CSV/JSON 导出，CSV 导入（列名映射）
- **单用户认证**：静态密码 + JWT + CSRF 保护
- **全中文界面**
- **Docker 一键部署**

## 快速开始

### Docker 部署（推荐）

1. 克隆仓库：
```bash
git clone https://github.com/blue060/SubLedger.git
cd SubLedger
```

2. 创建 `.env` 文件：
```bash
cp .env.example .env
# 编辑 .env，设置 ADMIN_PASSWORD
```

3. 启动：
```bash
docker compose up -d
```

4. 访问 http://localhost:8080

### 手动运行

**后端：**

```bash
cd backend
pip install -r requirements.txt
export ADMIN_PASSWORD=your-password
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

**前端：**

```bash
cd frontend
npm install
npm run build
# 将 dist/ 目录内容复制到 backend 的 static/ 目录
```

## 环境变量

| 变量 | 必需 | 默认值 | 说明 |
|------|------|--------|------|
| `ADMIN_PASSWORD` | 是 | - | 管理员密码 |
| `SECRET_KEY` | 否 | `change-me-in-production` | JWT 签名密钥 |
| `ENV` | 否 | `production` | 运行环境 |
| `DATABASE_URL` | 否 | `sqlite:///./data/subledger.db` | 数据库连接 |
| `DEFAULT_CURRENCY` | 否 | `CNY` | 默认首选货币 |
| `REMINDER_DAYS` | 否 | `7` | 提前提醒天数 |
| `SMTP_HOST` | 否 | - | SMTP 服务器地址 |
| `SMTP_PORT` | 否 | `465` | SMTP 端口 |
| `SMTP_USER` | 否 | - | SMTP 用户名 |
| `SMTP_PASSWORD` | 否 | - | SMTP 密码 |
| `SMTP_FROM` | 否 | - | 发件人地址 |
| `SMTP_TLS` | 否 | `true` | 启用 TLS |
| `BARK_URL` | 否 | - | Bark 推送地址 |
| `SERVERCHAN_KEY` | 否 | - | Server酱 Key |

## 技术栈

- **后端**：Python 3.12 + FastAPI + SQLAlchemy + SQLite
- **前端**：Vue 3 + TypeScript + Element Plus + ECharts
- **认证**：bcrypt + JWT (HttpOnly Cookie) + CSRF
- **部署**：Docker + docker-compose

## 开发

```bash
# 后端
cd backend
pip install -r requirements.txt
export ADMIN_PASSWORD=dev
uvicorn app.main:app --reload --port 8080

# 前端
cd frontend
npm install
npm run dev
```

前端开发服务器代理 API 请求到后端（见 `vite.config.ts`）。

## 许可

MIT