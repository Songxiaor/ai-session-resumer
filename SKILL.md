---
name: resume-session
description: "跨平台会话续聊：从 Claude CLI 或 Codex 中提取对话历史，无缝接入上下文继续讨论。两种模式：1) 给 ID 直接续聊 2) 描述需求列出近期会话选择后续聊。触发词：resume session, continue session, 继续上次的对话, 接着聊, 恢复会话, 看看最近的会话, 找一下我在XX聊的那个."
---

# Resume Session — 跨平台会话续聊

## 核心原则

**这个 skill 的目标不是"总结会话"，而是"成为那个会话的延续"。**

用户不需要你复述历史。用户需要的是：你读完对话后，表现得像你一直在那个会话里一样，直接接着干活。

## 执行协议（严格按顺序）

### Phase 1: 定位

**有 ID 的情况：**
```bash
SCRIPT=~/.agents/skills/resume-session/scripts/session_helper.py
python3 $SCRIPT extract "<session-id>" --tail 30
```
- 返回 JSON，包含 `messages`、`platform`、`name`、`session_id`
- 如果返回 `error`，检查 `suggestions` 字段，列出给用户选

**没 ID 的情况（自然语言）：**
```bash
python3 $SCRIPT list --hours 24 --platform all
```
- 解析用户意图确定 `--hours` 和 `--platform`
  - "codex 上的" → `--platform codex`
  - "claude 里的" → `--platform claude`
  - "最近的" → `--hours 24`
  - "昨天" → `--hours 48`
  - 未指定 → `--platform all --hours 24`
- 展示列表，用户选择后 → 执行 extract

### Phase 2: 吸收（最关键的一步）

拿到 messages 数组后，**不要急着输出**。先在内部完成以下分析：

1. **识别对话主题** — 这个会话在做什么？
2. **识别最后的行动** — 最后一条有效的 user→assistant 交换在做什么？
3. **识别未完成事项** — 有没有被中断的任务？有待办？有待确认？
4. **识别关键决策** — 用户做了哪些选择（技术栈、方案、方向）？
5. **识别当前状态** — 是在等用户确认？在跑构建？还是刚完成了一个里程碑？

**过滤噪音**：跳过以下类型的消息：
- `<local-command-caveat>...</local-command-caveat>`
- `<command-name>/model</command-name>` 等命令消息
- `<local-command-stdout>...</local-command-stdout>`
- `<task-notification>...</task-notification>`
- "Continue from where you left off." + "No response requested."
- "You've hit your limit" 限流消息

只保留真正的 user 提问和 assistant 实质性回复。

### Phase 3: 注入（呈现给用户）

**❌ 不要这样做（错误示范）：**

```
## 会话摘要：xxx

### 讨论了什么
- 要点 1
- 要点 2
- 要点 3

### 最后几轮对话
（展示原文）

### 待续事项
（列清单）

---
基于以上上下文，你想从哪里继续？
```

这种格式把用户推到了"决策者"位置，用户要重新理解上下文才能告诉你做什么。

**✅ 要这样做（正确示范）：**

```
已接入会话「x-ui-yg VPS 一键安装器」（Claude CLI，~/Documents，今天 16:18）

上次我们在做：构建 macOS DMG 安装包。
✅ DMG 构建成功（5.0 MB，aarch64）
✅ 加入了「使用前必读.txt」解决未签名问题
⏸ 最后你要求总结内容，准备换个平台构建 Windows 10-11 安装包，但 Claude 到了限额。

要继续 Windows 构建的迁移说明吗？还是先处理别的？
```

**关键区别：**
- 用 ✅ ⏸ 🔴 等符号一目了然
- 只说结论，不复述过程
- 最后一句话是**基于上下文推断出的下一步**，而不是开放式问题
- 用户只需要说"好"或"不，先做XX"就能继续，不需要重新解释上下文

### Phase 4: 接续

用户回复后，**你已经在那个会话的上下文里了**。规则：

1. **不要说"根据之前的对话…"** — 你就是那个对话的延续
2. **直接回答/执行** — 用户说"继续 Windows 构建"，你就直接写迁移说明，不要再说"好的，让我回顾一下…"
3. **保持角色一致** — 如果原会话里用户叫你用中文、用某种风格，继续用
4. **引用之前的决策** — 说"之前我们选的方案是…"，而不是"我看到之前的对话中提到…"

## 提取数据格式

`extract` 命令返回的 JSON 结构：

```json
{
  "session_id": "2d1e1ada-6472-4d04-903b-abf06cbbc0fa",
  "platform": "claude",
  "name": "看一下这个进度到哪了",
  "project": "-Users-song-Documents",
  "path": "~/.claude/projects/.../2d1e1ada.jsonl",
  "total": 90,
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

- `messages` 已经过滤了系统噪音
- 每条 content 截断到 2000 字符
- `--tail N` 只返回最后 N 条

## 大型会话策略

| 消息数 | 策略 |
|--------|------|
| < 30 | 全部读取，直接吸收 |
| 30-100 | `--tail 30`，从最后 30 条推断上下文 |
| > 100 | `--tail 40`，如果上下文不够再取更多 |

如果 tail 的消息里上下文不够（比如最后几条都是在处理一个细节，看不到全局），再跑一次不带 `--tail` 的 extract，但只读 `messages` 数组的前 10 条来了解会话开头。

## 平台识别

| 来源 | ID 特征 | 文件位置 |
|------|---------|----------|
| Claude CLI | 标准 UUID（`2d1e1ada-6472-...`） | `~/.claude/projects/<project>/` |
| Codex | 019 前缀（`019de1eb-7da0-...`） | `~/.codex/sessions/` 或 `archived_sessions/` |

ccswitch 显示的 ID = 底层 Claude/Codex 会话 ID，直接用于搜索。

## 错误处理

| 情况 | 处理 |
|------|------|
| ID 不存在 | 返回 suggestions，列出来让用户选 |
| 文件损坏 | 报错 + 建议用 list 找其他会话 |
| 会话太旧（>7天） | 提示可能不完整，仍然尝试 |
| 两个平台都没找到 | 扩大时间范围重试 |

## 触发词 → 动作映射

| 用户说 | 动作 |
|--------|------|
| "resume session XXXX" | Phase 1-4 |
| "基于这个会话继续" + ID | Phase 1-4 |
| "继续上次的对话" | list → 选择 → Phase 1-4 |
| "看看 codex 最近的" | list codex → 选择 → Phase 1-4 |
| "找一下我昨天聊的那个" | list 48h → 选择 → Phase 1-4 |
| "接着那个 x-ui 的话题聊" | search + list → 选择 → Phase 1-4 |
