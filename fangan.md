可以，下面这份你可以 **直接复制给 Codex**，让它按你的需求生成项目。
你的项目定位是：

> **一个跨平台语音任务提醒 App：手机/电脑同步，本地后端运行，到点提醒，钉钉推送，未完成无限催办，可延期，可写入手机日历。**

Flutter 适合做 Android / iOS / Windows / macOS / Linux 多端应用，官方也支持桌面端构建；FastAPI 可做本地后端，APScheduler 适合做定时任务调度；钉钉自定义机器人支持通过 Webhook 向群聊发送消息。([Flutter 文档](https://docs.flutter.dev/platform-integration/desktop?utm_source=chatgpt.com))

------

# 一、给 Codex 的总提示词

你可以直接复制这一段：

```text
你是一个资深全栈开发工程师，请帮我从零开发一个“跨平台语音任务提醒系统”。

项目目标：
开发一个 Flutter 全平台 App，支持 Android、iOS、Windows、macOS，后端先运行在本地电脑，后期可以迁移到云服务器。用户可以通过文字或手机系统语音输入创建任务，例如“明天下午三点提醒我给客户发接线图”。系统需要解析任务内容和提醒时间，保存到数据库，到点后通过 App、本地通知和钉钉群机器人进行提醒。如果用户没有标记完成，系统必须一直重复提醒，直到用户点击完成或者选择延期。

技术栈要求：
1. 前端使用 Flutter。
2. 后端使用 Python FastAPI。
3. 数据库使用 MySQL。
4. 定时提醒使用 APScheduler。
5. 钉钉通知使用企业内部群自定义机器人 Webhook。
6. 手机语音输入第一版不做语音识别 SDK，直接使用系统输入法语音转文字。
7. 后期预留 AI 解析接口，但第一版先用规则解析中文时间。
8. 后期预留云服务器部署能力，但第一版支持本地电脑运行。

核心功能：
1. 用户可以新增任务。
2. 用户可以输入任务标题、任务内容、提醒时间、提醒间隔。
3. 用户可以通过一句自然语言创建任务，例如：
   - 明天下午三点提醒我联系客户
   - 10分钟后提醒我打电话
   - 每天晚上9点提醒我学英语
4. 后端需要解析自然语言，提取任务内容和提醒时间。
5. 任务保存到 MySQL。
6. 到达提醒时间后，系统发送提醒。
7. 提醒渠道包括：
   - App 内任务状态更新
   - 钉钉机器人消息
   - 预留手机本地通知接口
   - 预留手机日历写入接口
8. 如果任务没有完成，系统按照 remind_interval_minutes 字段持续重复提醒。
9. 用户可以点击：
   - 完成
   - 延迟10分钟
   - 延迟30分钟
   - 延迟1小时
   - 延迟到明天
   - 取消任务
10. 只有任务状态为 done 或 cancelled 时才停止提醒。
11. 如果任务状态不是 done，也不是 cancelled，并且当前时间大于等于 next_remind_time，就必须继续提醒。
12. 需要提供 Flutter 前端、FastAPI 后端、MySQL 建表 SQL、接口文档、项目目录结构和运行说明。

提醒逻辑必须严格遵守：
只要 status != done 且 status != cancelled，并且 now >= next_remind_time，就发送提醒。发送完成后，如果任务仍未完成，则把 next_remind_time 更新为 now + remind_interval_minutes。

请先生成完整项目结构，然后分别生成：
1. 后端 FastAPI 代码
2. MySQL 数据库 SQL
3. APScheduler 定时任务代码
4. 钉钉 Webhook 通知代码
5. Flutter 前端页面代码
6. API 调用封装
7. 任务列表页面
8. 新增任务页面
9. 任务详情页面
10. 设置页面
11. README 运行文档

代码要求：
1. 代码要能直接运行。
2. 后端配置项写入 .env。
3. 不要把钉钉 Webhook 写死在代码里。
4. 所有接口返回统一 JSON 格式。
5. Flutter 前端使用清晰的目录结构。
6. 后端使用 SQLAlchemy 操作 MySQL。
7. 时间统一使用本地时间，后期预留 timezone 字段。
8. 中文注释清楚。
9. 先做最小可用版本，不要一次性做太复杂。
```

------

# 二、项目功能说明

## 1. 项目名称

```text
智能语音任务提醒系统
```

也可以叫：

```text
TaskReminder
```

或者：

```text
语音秘书
```

------

## 2. 系统架构

```text
Flutter App
Android / iOS / Windows / macOS
        ↓
FastAPI 本地后端
        ↓
MySQL 数据库
        ↓
APScheduler 定时扫描任务
        ↓
钉钉机器人 / App通知 / 日历写入
```

------

## 3. 核心流程

```text
用户输入：
明天下午三点提醒我给客户发接线图

↓ 后端解析

title = 给客户发接线图
remind_time = 2026-05-25 15:00:00
next_remind_time = 2026-05-25 15:00:00
status = pending

↓ 到点

钉钉提醒 + App提醒

↓ 用户没点完成

10分钟后继续提醒

↓ 用户点击延期30分钟

next_remind_time = 当前时间 + 30分钟

↓ 用户点击完成

status = done
停止提醒
```

------

# 三、数据库设计

让 Codex 按这个表来写。

```sql
CREATE DATABASE IF NOT EXISTS task_reminder DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE task_reminder;

CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',

    title VARCHAR(255) NOT NULL COMMENT '任务标题',
    content TEXT NULL COMMENT '任务详细内容',

    raw_input TEXT NULL COMMENT '用户原始输入，例如：明天下午三点提醒我联系客户',

    remind_time DATETIME NOT NULL COMMENT '第一次提醒时间',
    next_remind_time DATETIME NOT NULL COMMENT '下一次提醒时间',

    status VARCHAR(30) NOT NULL DEFAULT 'pending' COMMENT '任务状态：pending/reminding/postponed/done/cancelled',
    
    remind_interval_minutes INT NOT NULL DEFAULT 10 COMMENT '未完成时重复提醒间隔，默认10分钟',
    remind_count INT NOT NULL DEFAULT 0 COMMENT '已经提醒次数',

    dingding_enabled TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用钉钉提醒',
    app_notify_enabled TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用App提醒',
    calendar_enabled TINYINT NOT NULL DEFAULT 0 COMMENT '是否写入日历',

    priority VARCHAR(20) NOT NULL DEFAULT 'normal' COMMENT '优先级：low/normal/high/urgent',

    completed_at DATETIME NULL COMMENT '完成时间',
    cancelled_at DATETIME NULL COMMENT '取消时间',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
);

CREATE TABLE IF NOT EXISTS remind_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '提醒日志ID',

    task_id BIGINT NOT NULL COMMENT '任务ID',
    channel VARCHAR(50) NOT NULL COMMENT '提醒渠道：dingding/app/calendar',
    message TEXT NOT NULL COMMENT '提醒内容',
    result VARCHAR(30) NOT NULL DEFAULT 'success' COMMENT '发送结果：success/failed',
    error_message TEXT NULL COMMENT '失败原因',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_settings (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '设置ID',

    user_name VARCHAR(100) DEFAULT 'default' COMMENT '用户名',
    dingding_webhook TEXT NULL COMMENT '钉钉机器人Webhook',
    default_remind_interval_minutes INT NOT NULL DEFAULT 10 COMMENT '默认重复提醒间隔',

    enable_dingding TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用钉钉',
    enable_app_notify TINYINT NOT NULL DEFAULT 1 COMMENT '是否启用App通知',
    enable_calendar TINYINT NOT NULL DEFAULT 0 COMMENT '是否启用日历',

    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

------

# 四、后端接口设计

让 Codex 按这个接口写。

## 1. 新增任务

```http
POST /api/tasks
```

请求：

```json
{
  "title": "给客户发接线图",
  "content": "PCIe-1230 NPN/PNP 接线说明",
  "remind_time": "2026-05-25 15:00:00",
  "remind_interval_minutes": 10,
  "dingding_enabled": true,
  "calendar_enabled": false
}
```

------

## 2. 自然语言新增任务

```http
POST /api/tasks/parse-create
```

请求：

```json
{
  "text": "明天下午三点提醒我给客户发接线图"
}
```

返回：

```json
{
  "code": 200,
  "message": "任务创建成功",
  "data": {
    "id": 1,
    "title": "给客户发接线图",
    "remind_time": "2026-05-25 15:00:00",
    "next_remind_time": "2026-05-25 15:00:00",
    "status": "pending"
  }
}
```

------

## 3. 获取任务列表

```http
GET /api/tasks
```

支持参数：

```text
status=pending
status=done
status=cancelled
date=2026-05-25
```

------

## 4. 任务详情

```http
GET /api/tasks/{task_id}
```

------

## 5. 完成任务

```http
POST /api/tasks/{task_id}/done
```

效果：

```text
status = done
completed_at = 当前时间
停止提醒
```

------

## 6. 延期任务

```http
POST /api/tasks/{task_id}/postpone
```

请求：

```json
{
  "minutes": 30
}
```

效果：

```text
next_remind_time = 当前时间 + 30分钟
status = postponed
```

------

## 7. 取消任务

```http
POST /api/tasks/{task_id}/cancel
```

------

## 8. 修改设置

```http
POST /api/settings
```

请求：

```json
{
  "dingding_webhook": "https://oapi.dingtalk.com/robot/send?access_token=xxx",
  "default_remind_interval_minutes": 10,
  "enable_dingding": true,
  "enable_app_notify": true,
  "enable_calendar": false
}
```

------

# 五、提醒规则

这是整个项目最核心的逻辑，让 Codex 必须按这个写：

```python
if task.status not in ["done", "cancelled"] and now >= task.next_remind_time:
    send_reminder(task)
    task.remind_count += 1
    task.status = "reminding"
    task.next_remind_time = now + timedelta(minutes=task.remind_interval_minutes)
    save(task)
```

也就是说：

```text
未完成 = 一直提醒
完成 = 停止
取消 = 停止
延期 = 改下次提醒时间
```

------

# 六、钉钉提醒消息格式

钉钉群里可以发这种：

```text
⏰ 任务提醒

事项：给客户发接线图
时间：2026-05-25 15:00
状态：未完成
提醒次数：第 3 次

请在 App 中选择：
完成 / 延迟10分钟 / 延迟30分钟 / 延迟1小时 / 取消
```

给 Codex 的要求：

```text
钉钉机器人第一版只负责发消息，不做回调交互。
完成、延期、取消操作先在 App 内完成。
后期再扩展钉钉消息按钮或钉钉应用交互。
```

------

# 七、Flutter 页面说明

## 页面 1：首页 / 今日任务

显示：

```text
今天待办
逾期任务
即将提醒任务
已完成任务
```

每个任务卡片显示：

```text
任务标题
提醒时间
状态
提醒次数
完成按钮
延期按钮
```

------

## 页面 2：新增任务

包含两种方式：

```text
1. 自然语言输入框
2. 手动输入表单
```

自然语言输入框：

```text
请输入：明天下午三点提醒我给客户发接线图
```

按钮：

```text
创建任务
```

说明：

```text
手机端用户可以点击输入框，然后使用系统输入法的语音输入。
第一版不单独开发语音识别。
```

------

## 页面 3：任务详情

显示：

```text
标题
内容
原始输入
提醒时间
下一次提醒时间
提醒间隔
提醒次数
状态
提醒日志
```

操作：

```text
完成
延期10分钟
延期30分钟
延期1小时
明天提醒
取消
```

------

## 页面 4：设置页

配置：

```text
后端地址
钉钉 Webhook
默认重复提醒间隔
是否启用钉钉提醒
是否启用 App 通知
是否启用日历写入
```

------

# 八、项目目录结构

让 Codex 按这个结构生成：

```text
task_reminder_project/

├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── crud.py
│   │   ├── scheduler.py
│   │   ├── dingding.py
│   │   ├── time_parser.py
│   │   ├── config.py
│   │   └── routers/
│   │       ├── tasks.py
│   │       └── settings.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── lib/
│   │   ├── main.dart
│   │   ├── models/
│   │   │   └── task.dart
│   │   ├── services/
│   │   │   └── api_service.dart
│   │   ├── pages/
│   │   │   ├── home_page.dart
│   │   │   ├── add_task_page.dart
│   │   │   ├── task_detail_page.dart
│   │   │   └── settings_page.dart
│   │   ├── widgets/
│   │   │   └── task_card.dart
│   │   └── config/
│   │       └── app_config.dart
│   └── pubspec.yaml
│
├── sql/
│   └── init.sql
│
└── README.md
```

------

# 九、第一版开发范围

你告诉 Codex：

```text
第一版只做最小可用版本，不要做复杂权限登录，不要做多用户，不要做云同步，不要做复杂AI。

第一版必须完成：
1. Flutter App 能新增任务
2. Flutter App 能查看任务列表
3. Flutter App 能完成任务
4. Flutter App 能延期任务
5. FastAPI 能保存任务
6. FastAPI 能定时扫描任务
7. 到点后能发钉钉消息
8. 未完成能持续提醒
9. MySQL 能保存数据
10. 设置页能保存钉钉 Webhook
```

------

# 十、第二版再做的功能

```text
第二版功能：
1. 接入 AI 解析自然语言
2. 写入手机系统日历
3. App 本地通知
4. Windows/macOS 桌面通知
5. 多设备登录同步
6. 云服务器部署
7. 钉钉消息按钮交互
8. 任务分类
9. 重复任务
10. 每日总结
11. 每周统计
12. Notion 同步
```

------

# 十一、你给 Codex 的分阶段指令

你不要一次让 Codex 写全部，可以分 5 次让它生成。

## 第 1 次：生成后端

```text
请先根据上面的需求，只生成 backend 后端项目代码，包括 FastAPI、SQLAlchemy、MySQL、APScheduler、钉钉通知、任务接口、设置接口。要求代码完整可运行，并提供 requirements.txt、.env.example 和 README。
```

## 第 2 次：生成数据库

```text
请生成 MySQL 初始化 SQL，包括 tasks、remind_logs、user_settings 三张表，并插入一条默认 user_settings 数据。
```

## 第 3 次：生成 Flutter 前端

```text
请根据上面的接口，生成 Flutter 前端项目代码，包括首页、添加任务页、任务详情页、设置页、API 服务封装。要求 UI 简洁，适合手机和桌面端。
```

## 第 4 次：联调

```text
请帮我检查 Flutter 前端和 FastAPI 后端的接口是否一致，包括字段名、接口路径、请求方式、返回格式，并修复不一致的地方。
```

## 第 5 次：优化提醒逻辑

```text
请重点检查 APScheduler 的提醒逻辑，确保任务未完成时会一直提醒，直到 status 为 done 或 cancelled。提醒后必须写入 remind_logs，并更新 remind_count 和 next_remind_time。
```

------

# 十二、你这个项目的核心判断

你这个 App **可以自己写**，而且很适合你练手和后期做成自己的工作工具。

不过第一版一定不要贪多。

你先实现这条主线：

```text
输入任务 → 保存任务 → 到点钉钉提醒 → 未完成继续提醒 → 点完成停止
```

只要这条跑通，你这个系统就已经有价值了。后面再慢慢加语音、日历、桌面端、AI 解析。