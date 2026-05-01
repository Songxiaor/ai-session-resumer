# 如何获取会话 ID

本文档介绍获取 Claude CLI / Codex 会话 ID 的所有途径。

---

## 方式 1: CC Switch（推荐，最直观）

[CC Switch](https://ccswitch.dev) 是一个 macOS 菜单栏应用，统一管理 Claude CLI、Codex、Gemini 等多个 AI 编码平台的会话。

### 安装

从官网下载：https://ccswitch.dev

### 找到会话 ID 的步骤

1. **打开 CC Switch**
   - 菜单栏右上角会出现 CC Switch 图标
   - 点击图标打开主界面

2. **进入会话列表**
   - 主界面左侧导航栏有 **Sessions**（会话）入口
   - 点击进入会话管理页面

3. **浏览会话**
   - 会话按时间倒序排列
   - 每个会话显示：
     - 会话名称（通常是第一条用户消息）
     - 平台标识（Claude / Codex / Gemini）
     - 最后活跃时间
     - 会话 ID

4. **复制会话 ID**
   - 点击目标会话，进入详情页
   - 会话 ID 显示在详情页顶部或元信息区域
   - 点击 ID 旁边的复制按钮即可

### CC Switch 的优势

- **统一视图**：同时看到 Claude 和 Codex 的会话
- **按平台筛选**：快速过滤只看某个平台的会话
- **会话搜索**：按关键词搜索会话名称
- **会话预览**：不用打开终端就能看到会话内容
- **一键恢复**：可以直接从 CC Switch 启动会话

---

## 方式 2: Claude CLI 交互式选择器

### 在终端中打开选择器

```bash
# 弹出会话选择器（交互式 TUI）
claude --resume

# 或者在 Claude 交互模式内输入斜杠命令
/resume
```

选择器会显示：
- 会话名称（第一条用户消息）
- 最后活跃时间
- 所在项目目录

用方向键选择，回车确认，会话 ID 会显示在顶部或选择后显示。

### 直接指定 ID 恢复

```bash
claude --resume <session-id>
```

---

## 方式 3: Codex CLI 交互式选择器

### 打开选择器

```bash
# 弹出会话选择器
codex resume

# 恢复最近一次会话（不弹选择器）
codex resume --last

# 显示所有会话（不过滤当前目录）
codex resume --all

# 直接指定 ID 恢复
codex resume <session-id>

# 按名称搜索恢复
codex resume "每日整理知识库网页剪藏"
```

选择器显示：
- 会话 ID
- 会话名称（thread_name）
- 最后活跃时间
- 工作目录

---

## 方式 4: AI Session Resumer 脚本（统一视图）

使用本项目的 `session_helper.py` 脚本，同时列出两个平台的会话：

```bash
SCRIPT=~/.agents/skills/resume-session/scripts/session_helper.py

# 列出最近 24 小时所有会话（Claude + Codex）
python3 $SCRIPT list --hours 24 --platform all

# 只看 Codex 会话
python3 $SCRIPT list --hours 48 --platform codex

# 只看 Claude 会话
python3 $SCRIPT list --hours 24 --platform claude

# 按 ID 前缀搜索
python3 $SCRIPT search "2d1e1ada"

# 按关键词搜索会话名称
python3 $SCRIPT search "x-ui"
```

输出示例：
```json
[
  {
    "id": "2d1e1ada-6472-4d04-903b-abf06cbbc0fa",
    "platform": "claude",
    "name": "看一下这个进度到哪了",
    "project": "-Users-song-Documents",
    "time": "2026-05-01T18:39:00"
  },
  {
    "id": "019de1eb-7da0-7351-9472-a0ef7f1912c8",
    "platform": "codex",
    "name": "每日整理知识库网页剪藏",
    "time": "2026-05-01T07:52:00"
  }
]
```

---

## 方式 5: 直接看文件（硬核方式）

### Claude CLI 会话

会话文件存储在 `~/.claude/projects/<project-name>/<session-id>.jsonl`

```bash
# 列出所有项目目录
ls ~/.claude/projects/

# 列出某个项目下的所有会话（按时间排序）
ls -lt ~/.claude/projects/-Users-song-Documents/*.jsonl | head -10

# 从文件名提取会话 ID
ls ~/.claude/projects/-Users-song-Documents/*.jsonl | while read f; do
    basename "$f" .jsonl
done

# 从 history.jsonl 提取所有唯一会话 ID（全局，共 300+ 条）
cat ~/.claude/history.jsonl | python3 -c "
import sys, json
seen = set()
for line in sys.stdin:
    try:
        d = json.loads(line.strip())
        sid = d.get('sessionId', '')
        if sid and sid not in seen:
            seen.add(sid)
            print(sid)
    except:
        pass
"
```

### Codex 会话

```bash
# 会话索引文件（有名称和时间，最方便）
cat ~/.codex/session_index.jsonl | python3 -c "
import sys, json
for line in sys.stdin:
    d = json.loads(line.strip())
    print(f\"{d['id']}  {d.get('updated_at','')[:16]}  {d.get('thread_name','')}\")"
```

会话文件位置：
- 活跃会话：`~/.codex/sessions/<year>/<month>/<day>/rollout-<timestamp>-<id>.jsonl`
- 归档会话：`~/.codex/archived_sessions/rollout-<timestamp>-<id>.jsonl`

---

## 方式对比

| 方式 | 平台 | 适合场景 | 上手难度 |
|------|------|---------|---------|
| **CC Switch** | 双平台 | 可视化浏览，最直观 | ⭐ 最简单 |
| **claude --resume** | Claude | 终端里快速选择 | ⭐⭐ 简单 |
| **codex resume** | Codex | 终端里快速选择，支持按名称搜 | ⭐⭐ 简单 |
| **session_helper.py** | 双平台 | 统一视图，脚本自动化 | ⭐⭐⭐ 中等 |
| **直接看文件** | 双平台 | 调试、批量处理 | ⭐⭐⭐⭐ 硬核 |

---

## ccswitch ID 与底层 ID 的关系

CC Switch 显示的会话 ID **就是**底层 Claude CLI / Codex 的原生会话 ID，不需要任何转换。

| CC Switch 显示 | 底层文件 |
|----------------|---------|
| `2d1e1ada-6472-4d04-903b-abf06cbbc0fa` (Claude) | `~/.claude/projects/.../2d1e1ada-6472-4d04-903b-abf06cbbc0fa.jsonl` |
| `019de1eb-7da0-7351-9472-a0ef7f1912c8` (Codex) | `~/.codex/sessions/.../rollout-...-019de1eb-7da0-7351-9472-a0ef7f1912c8.jsonl` |

所以从 CC Switch 复制的 ID 可以直接用于本 skill 的所有命令。
