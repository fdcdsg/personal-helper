# TaskReminder 后端

FastAPI + APScheduler 的任务提醒后端。默认使用 SQLite，开箱即可运行；后续可以把 `.env` 改成 MySQL 并部署到云服务器。

## 功能

- 创建任务、自然语言创建任务、任务列表和详情
- 完成、取消、延后任务
- 到点后持续提醒，直到任务变成 `done` 或 `cancelled`
- 钉钉群机器人 Webhook 提醒
- App 内提醒日志记录

## 安装

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## 配置

复制 `.env.example` 为 `.env`，或直接编辑已有 `.env`。

```env
DATABASE_TYPE=sqlite
SCHEDULER_INTERVAL_SECONDS=30
DINGDING_WEBHOOK=
```

如果要使用 MySQL：

```env
DATABASE_TYPE=mysql
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=task_reminder
```

钉钉 Webhook 可以写在 `.env`，也可以在客户端设置页保存。数据库中的设置优先级更高。

## 启动

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API 文档：http://127.0.0.1:8000/docs
- 电脑端客户端默认 API：http://127.0.0.1:8000
- 手机端同一 Wi-Fi 下使用电脑局域网 IP，例如 `http://192.168.1.8:8000`

## API

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/tasks` | 新增任务 |
| POST | `/api/tasks/parse-create` | 自然语言创建任务 |
| GET | `/api/tasks` | 任务列表 |
| GET | `/api/tasks/{id}` | 任务详情和提醒日志 |
| POST | `/api/tasks/{id}/done` | 完成任务 |
| POST | `/api/tasks/{id}/postpone` | 延后任务 |
| POST | `/api/tasks/{id}/cancel` | 取消任务 |
| GET | `/api/settings` | 获取设置 |
| POST | `/api/settings` | 保存设置 |

## 自然语言示例

- `10分钟后提醒我打电话`
- `明天下午三点提醒我联系客户`
- `每天晚上9点提醒我学英语`

第一版会把“每天”解析为下一次到达的时间点；真正的重复任务规则可以在后续版本扩展。
