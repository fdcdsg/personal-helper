# Personal Helper TaskReminder

一个先本机运行、后续可迁移云端的多端任务提醒系统。

## 目录

- `backend/`：FastAPI 后端，负责任务、设置、钉钉提醒和定时扫描。
- `app/`：Flutter 客户端核心代码，安装 Flutter SDK 后可生成 Android、iOS、Windows、macOS、Linux、Web 平台目录。

## 快速启动后端

Windows 下可以直接双击：

```text
一键启动后端.bat
```

macOS 下可以直接双击：

```text
一键启动后端.command
```

脚本会自动创建虚拟环境、安装依赖、启动后端并打开 API 文档。macOS 脚本使用 `backend/.venv`，不会复用 Windows 的 `backend/venv`。

也可以手动启动：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档：http://127.0.0.1:8000/docs

## 快速启动客户端

安装 Flutter SDK 后，可以直接双击：

```text
启动Flutter客户端.bat
```

macOS 下可以直接双击：

```text
启动Flutter客户端.command
```

脚本会自动生成平台目录、安装依赖，并启动 Flutter Web 客户端：

```text
http://127.0.0.1:8088
```

手机和 Mac 在同一 Wi-Fi 下时，用 Mac 的局域网 IP 访问，例如：

```text
http://192.168.1.9:8088
```

Windows 下的 `启动Flutter客户端.bat` 也会构建 Web 客户端，并打印本机和手机访问地址。

也可以手动启动：

```bash
cd app
flutter create --platforms=android,ios,windows,macos,linux,web .
flutter pub get
flutter build web
cd build/web
python3 -m http.server 8088 --bind 0.0.0.0
```

## 提醒逻辑

只要任务状态不是 `done` 或 `cancelled`，并且当前时间大于等于 `next_remind_time`，后端就会发送提醒。发送后会把 `next_remind_time` 更新为当前时间加上 `remind_interval_minutes`，直到用户点击完成或取消。

## Notion 同步

可以把 Notion 作为任务整理入口，再由本应用导入并负责提醒。建议在 Notion 建一个任务数据库，至少包含这些属性：

| 属性名 | Notion 类型 | 说明 |
| --- | --- | --- |
| `Name` | Title | 任务标题 |
| `提醒时间` | Date | 必填，导入后作为提醒时间 |
| `内容` | Text / Rich text | 可选，导入为任务内容 |
| `分类` | Select / Multi-select / Text | 可选，导入为任务分类 |
| `提醒间隔` | Number | 可选，单位分钟；不填则使用默认重复提醒间隔 |
| `状态` | Status / Select | `未开始` 不进入提醒，`进行中` 进入提醒，`完成` 同步为已完成 |
| `创建时间` | Created time | 和任务标题一起作为唯一键 |

使用步骤：

1. 在 Notion 创建 Internal Integration，复制 token。
2. 把你的任务数据库分享给这个 integration。
3. 打开客户端“设置”页，在“Notion 同步”里填 token、数据库链接或数据源 ID，以及属性名。
4. 点击“从 Notion 同步任务”。

同步时不会用 Notion 页面 ID 匹配任务，而是用 `Name + 创建时间` 作为唯一键：

- `Name + 创建时间` 一样：更新客户端里的分类、提醒时间、提醒间隔、状态和内容。
- `Name` 或 `创建时间` 不一样：视为另一条任务，不会覆盖旧任务。
- 删除 Notion 某一行再写新任务时，因为创建时间会变化，所以会作为新任务导入。
