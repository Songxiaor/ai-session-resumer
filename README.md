# AI Session Resumer

> **跨平台 AI 会话续聊 Skill** — 从 Claude CLI / Codex 提取对话历史，无缝接入上下文继续讨论。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-Craft%20Agents-blue)](https://craftagents.com)

---

## 🤔 解决什么问题？

你同时使用多个 AI 编码平台（Claude CLI、Codex 等），遇到这些场景：

- **额度用完了** — Claude 到了限额，想无缝切到 Codex 继续
- **平台各有所长** — Claude 擅长架构，Codex 擅长执行，想在两个平台对比同一个任务的效果
- **会话断了** — 关了终端，第二天想接着昨天的对话继续
- **项目复盘** — 隔了一周，想回忆当时某个项目和 AI 聊了哪些决策和技术选型

传统做法：手动复制对话内容 → 粘贴到新平台 → 解释上下文 → 效率极低。

**AI Session Resumer**：给一个会话 ID → 自动提取历史 → 上下文注入 → 直接接着聊。

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| **一键续聊** | 给会话 ID，自动提取并注入上下文 |
| **双平台支持** | Claude CLI + Codex，自动识别 |
| **智能过滤** | 自动过滤系统噪音（`<local-command>`、模型切换、限流消息等） |
| **自然语言查找** | "找一下我昨天在 codex 上聊的那个" → 列出可选会话 |
| **大型会话处理** | 超过 50 条消息自动截取最近部分 + 摘要 |
| **无缝注入** | 不是"总结后问你从哪继续"，而是"我已经在对话里了，直接接着聊" |

---

## 🏗️ 工作原理

```
模式 1: 用户给 ID                    模式 2: 用户描述需求
     │                                    │
     ▼                                    ▼
 extract <id>                         list --hours 24 --platform X
     │                                    │
     ▼                                    ▼
 找到文件 → 解析 JSONL                   展示列表 → 用户选择
     │                                    │
     ▼                                    ▼
 吸收上下文 ←←←←←←←←←←←←←←←←←←←← 吸收上下文
     │
     ▼
 注入当前会话 → 直接接着聊
```

### 四阶段协议

| 阶段 | 说明 |
|------|------|
| **Phase 1: 定位** | 按 ID 搜索 `~/.claude/` 和 `~/.codex/`，找到 JSONL 会话文件 |
| **Phase 2: 吸收** | 解析消息 → 过滤噪音 → 识别主题/决策/状态/待办 |
| **Phase 3: 注入** | 用简洁格式呈现上下文，用户只需说"好"就能继续 |
| **Phase 4: 接续** | LLM 从这一刻起表现得像一直在那个会话里，直接干活 |

---

## 📦 安装

### 前置条件

在安装之前，请确保你的环境满足以下要求：

| 条件 | 说明 |
|------|------|
| **Python 3** | 脚本依赖 Python 3.7+，运行 `python3 --version` 确认已安装 |
| **Claude CLI 和/或 Codex CLI** | 至少安装并使用过其中一个，否则没有会话数据可提取 |
| **Craft Agents**（可选） | 如果你想用 Skill 模式（自然语言触发），需要先安装 Craft Agents |

> 💡 如果你只想用命令行脚本（见下方「手动使用」章节），不需要 Craft Agents。

### 方法 1: 克隆到 skills 目录（推荐）

```bash
git clone https://github.com/Songxiaor/ai-session-resumer.git ~/.agents/skills/resume-session
```

### 方法 2: 手动安装

```bash
# 1. 创建 skill 目录
mkdir -p ~/.agents/skills/resume-session/scripts

# 2. 下载文件
curl -o ~/.agents/skills/resume-session/SKILL.md \
  https://raw.githubusercontent.com/Songxiaor/ai-session-resumer/main/SKILL.md

curl -o ~/.agents/skills/resume-session/scripts/session_helper.py \
  https://raw.githubusercontent.com/Songxiaor/ai-session-resumer/main/scripts/session_helper.py

# 3. 赋予执行权限
chmod +x ~/.agents/skills/resume-session/scripts/session_helper.py
```

### 验证安装

安装完成后，运行以下命令验证：

```bash
python3 ~/.agents/skills/resume-session/scripts/session_helper.py list --hours 24 --platform all
```

- 如果输出一个 JSON 数组（哪怕是空的 `[]`），说明安装成功 ✅
- 如果报 `python3: command not found`，需要先安装 Python 3
- 如果报 `Permission denied`，运行 `chmod +x` 赋予执行权限

---

## 🚀 使用场景

> ⚠️ **以下所有对话演示均在 Craft Agents 环境中进行。** 在 Craft Agents 里，你可以用自然语言触发 skill（如"找一下我昨天聊的那个"、"resume session XXXX"）。如果你不在 Craft Agents 环境中，请直接使用命令行脚本，参见下方「手动使用」章节。

### 场景 1: 额度用完，丝滑转平台

> **Claude 额度用完了，但 Codex 还有额度**

```
你: codex resume 2d1e1ada-6472-4d04-903b-abf06cbbc0fa

AI: 已接入会话「x-ui-yg VPS 一键安装器」（Claude CLI，~/Documents，今天 16:18）

    上次我们在做：构建 macOS DMG 安装包。
    ✅ DMG 构建成功（5.0 MB，aarch64）
    ✅ 加入了「使用前必读.txt」解决未签名问题
    ⏸ 最后你要求总结内容，准备换个平台构建 Windows 安装包，但到了限额。

    要继续 Windows 构建的迁移说明吗？还是先处理别的？

你: 好，继续 Windows 构建

AI: （直接开始写 Windows 构建迁移说明，不需要任何额外上下文）
```

**好处**：
- 零上下文损失
- 无缝切换，用户无感
- 不需要重新解释项目背景

### 场景 2: 跨平台对比能力

> **同一个任务，在 Claude 和 Codex 上分别跑，对比结果**

```bash
# 1. 先在 Claude 上跑一个任务
# ... Claude 完成后，拿到会话 ID: abc123

# 2. 让 Codex 基于同一个上下文继续
你: codex resume abc123

# 3. Codex 读取 Claude 的完整上下文后，你可以：
#    - 让它重新做一遍，看效果差异
#    - 让它优化 Claude 的方案
#    - 让它做 Claude 没完成的部分
```

**好处**：
- 同一个项目，两个平台各展所长
- A/B 测试不同模型的代码质量
- 一个平台卡住了，另一个平台接力

### 场景 3: 跨天继续昨天的工作

> **昨天在 Claude 上聊到一半，今天想继续**

```
你: 找一下我昨天在 claude 上聊的那个

AI: 最近 48 小时的会话（共 12 个）

    | # | 平台   | ID       | 名称                    | 时间      |
    |---|--------|----------|-------------------------|-----------|
    | 1 | claude | 2d1e1ada | 看一下这个进度到哪了     | 今天 16:18 |
    | 2 | codex  | 019de1eb | 每日整理知识库网页剪藏   | 今天 15:52 |
    | 3 | claude | 86e52249 | 修复登录页 bug           | 昨天 22:30 |
    | ... | | | | |

    选哪个？

你: 3

AI: 已接入会话「修复登录页 bug」...
```

### 场景 4: 项目回顾与复盘

> **隔了一周，想回顾当时某个项目聊了哪些决策**

```
你: 看一下我上周在 claude 上聊的那个 x-ui 安装器

AI: 已接入会话「x-ui-yg VPS 一键安装器」（Claude CLI，4月28日）

    上次在做：构建 macOS DMG + Windows EXE 安装包。
    ✅ macOS DMG 完成
    ✅ Windows 跨平台说明已写
    ⏸ Linux 构建未开始

    关键决策：选了 Tauri 而非 Electron，仓库地址是 yonggekkk/x-ui-yg

    要继续开发，还是看看当时的技术细节？
```

**适用场景**：
- 回忆上周/上月的技术决策和选型理由
- 接手同事的项目时，读他之前和 AI 的讨论记录
- 写技术文档时，回溯当时的设计思路

---

## 🛠️ 手动使用（不依赖 Skill）

你也可以直接用命令行脚本，不依赖 Craft Agents 的 Skill 系统：

```bash
SCRIPT=~/.agents/skills/resume-session/scripts/session_helper.py

# 列出最近 24 小时的所有会话
python3 $SCRIPT list --hours 24 --platform all

# 只看 Codex 会话
python3 $SCRIPT list --hours 48 --platform codex

# 搜索会话（按 ID 前缀或关键词）
python3 $SCRIPT search "2d1e1ada"
python3 $SCRIPT search "x-ui"

# 提取对话内容
python3 $SCRIPT extract "2d1e1ada" --tail 30

# 只看元信息
python3 $SCRIPT info "2d1e1ada"
```

输出格式为 JSON，可以对接任何自动化流程。

---

## ❓ 常见问题

<details>
<summary><b>Q: 运行脚本报 <code>python3: command not found</code></b></summary>

macOS 用户可能需要安装 Python 3：
```bash
brew install python3
```
Linux 用户：
```bash
sudo apt install python3  # Debian/Ubuntu
sudo dnf install python3  # Fedora
```
Windows 用户需要从 [python.org](https://python.org) 下载安装，并确保 `python3` 在 PATH 中。
</details>

<details>
<summary><b>Q: 输出空数组 <code>[]</code>，找不到任何会话</b></summary>

可能原因：
1. Claude CLI / Codex CLI 从未使用过（没有会话数据）
2. 会话数据不在默认路径下
3. 时间范围太短 —— 试试 `--hours 168`（一周）

手动检查数据是否存在：
```bash
ls ~/.claude/projects/  # Claude CLI 会话
ls ~/.codex/sessions/   # Codex 会话
```
</details>

<details>
<summary><b>Q: Windows 能用吗？</b></summary>

脚本使用 `~` 路径，在 Windows 上需要确认 `~` 指向正确的用户目录。建议在 WSL (Windows Subsystem for Linux) 中使用，或手动将路径替换为 `%USERPROFILE%`。
</details>

<details>
<summary><b>Q: 提取的会话内容不完整 / 被截断</b></summary>

脚本默认将每条消息截断到 2000 字符。如果会话中包含大量代码，部分代码可能会被截断。这是设计上的取舍（避免超出 LLM 上下文窗口）。如需更完整的内容，可以修改 `session_helper.py` 中的 `[:2000]` 限制。
</details>

<details>
<summary><b>Q: Codex 会话路径不存在</b></summary>

Codex CLI 的会话存储路径可能随版本变化。如果 `~/.codex/sessions/` 不存在，尝试：
```bash
# 查找 Codex 会话文件的实际位置
find ~ -name "session_index.jsonl" -path "*.codex*" 2>/dev/null
find ~ -name "rollout-*.jsonl" 2>/dev/null | head -5
```
如果找到的路径与脚本中硬编码的不同，请修改 `session_helper.py` 顶部的路径常量。
</details>

---

## 🔧 支持的平台

| 平台 | ID 格式 | 文件位置 | 状态 |
|------|---------|----------|------|
| **Claude CLI** | 标准 UUID（`2d1e1ada-6472-...`） | `~/.claude/projects/` | ✅ 已支持 |
| **Codex** | 019 前缀（`019de1eb-7da0-...`） | `~/.codex/sessions/` | ✅ 已支持 |
| **Cursor** | 待研究 | 待研究 | 🔜 计划中 |
| **Windsurf** | 待研究 | 待研究 | 🔜 计划中 |
| **Cline** | 待研究 | 待研究 | 🔜 计划中 |

欢迎贡献新平台的适配！

---

## 🔍 如何获取会话 ID

会话 ID 的获取途径详见 [FINDING_SESSION_IDS.md](FINDING_SESSION_IDS.md)，这里列个概要：

| 方式 | 平台 | 说明 |
|------|------|------|
| **[CC Switch](https://github.com/farion1231/cc-switch)** | 双平台 | 跨平台桌面应用（Win/Mac/Linux），可视化浏览会话 |
| **`claude --resume`** | Claude | 终端交互式选择器 |
| **`codex resume`** | Codex | 终端交互式选择器，支持按名称搜 |
| **`session_helper.py list`** | 双平台 | 本项目脚本，统一列出两个平台 |
| **直接看文件** | 双平台 | `~/.claude/` 和 `~/.codex/` 目录 |

ccswitch 显示的 ID = 底层 Claude/Codex 原生 ID，直接用于本 skill，不需要转换。

---

## 📐 技术细节

### 会话文件格式

**Claude CLI** — JSONL，每行一个事件：
```json
{"type": "user", "message": {"role": "user", "content": "看一下这个进度到哪了"}}
{"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "..."}]}}
```

**Codex** — JSONL，每行一个事件：
```json
{"type": "response_item", "payload": {"type": "message", "role": "user", "content": [{"type": "input_text", "text": "..."}]}}
```

### 噪音过滤

Claude CLI 会话包含系统注入的噪音消息，脚本自动过滤：

| 噪音类型 | 示例 |
|----------|------|
| 模型切换 | `<command-name>/model</command-name>` |
| 本地命令 | `<local-command-caveat>...</local-command-caveat>` |
| 任务通知 | `<task-notification>...</task-notification>` |
| 限流消息 | `You've hit your limit` |
| 自动续聊 | `Continue from where you left off.` |

Codex 格式天然干净，无需额外过滤。

---

## 🤝 贡献

1. Fork 本仓库
2. 创建功能分支（`git checkout -b feature/new-platform`）
3. 提交更改（`git commit -m 'Add support for Cursor'`）
4. 推送分支（`git push origin feature/new-platform`）
5. 创建 Pull Request

### 贡献方向

- [ ] 支持更多平台（Cursor、Windsurf、Cline、Copilot）
- [ ] 会话内容全文搜索（不只搜名称）
- [ ] 索引缓存（加速大型会话库的搜索）
- [ ] 会话导出（Markdown、HTML 格式）
- [ ] 双向同步（在 Craft Agent 中的对话也能回写到原平台）

---

## 📄 License

MIT License - 自由使用、修改、分发。

---

## 🙏 致谢

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) — Claude CLI 的会话管理
- [Codex](https://openai.com/index/codex/) — OpenAI 的编码代理
- [Craft Agents](https://craftagents.com) — Skill 运行时环境
- [CC Switch](https://github.com/farion1231/cc-switch) — Claude Code / Codex / Gemini CLI 全方位管理工具
