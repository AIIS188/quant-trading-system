# Skills 自动化测试计划

## 概述

本计划用于自动化测试所有 OpenClaw skills，识别缺失的依赖和环境配置。

## Skills 分类

### 1. 工作区 Skills (5 个)

| Skill | 位置 | 依赖 | 环境变量 |
|-------|------|------|----------|
| tavily-search | `~/.openclaw/workspace/skills/tavily-search` | node | TAVILY_API_KEY |
| clawdbot-filesystem | `~/.openclaw/workspace/skills/clawdbot-filesystem` | node | - |
| find-skills | `~/.openclaw/workspace/skills/find-skills` | npx skills | - |
| self-improving-agent | `~/.openclaw/workspace/skills/self-improving-agent` | - | - |
| elite-longterm-memory | `~/.openclaw/workspace/skills/elite-longterm-memory` | - | OPENAI_API_KEY (可选) |

### 2. 系统 Skills - 无需外部依赖 (可直接测试)

| Skill | 功能 | 测试命令 |
|-------|------|----------|
| weather | 天气查询 | `curl "wttr.in/Beijing?format=3"` |
| healthcheck | 安全检查 | `openclaw security audit` |
| tmux | tmux 控制 | `tmux list-sessions` |
| session-logs | 会话日志搜索 | `openclaw sessions list` |
| canvas | Canvas 控制 | `canvas snapshot` |
| memory_search | 内存搜索 | `memory_search query="test"` |

### 3. 系统 Skills - 需要 API Keys

| Skill | 环境变量 | 获取方式 |
|-------|----------|----------|
| openai-image-gen | OPENAI_API_KEY | https://platform.openai.com |
| openai-whisper-api | OPENAI_API_KEY | https://platform.openai.com |
| notion | NOTION_API_KEY | https://notion.so/my-integrations |
| sag | ELEVENLABS_API_KEY | https://elevenlabs.io |
| tavily (系统版) | TAVILY_API_KEY | https://tavily.com |
| nano-banana-pro | GEMINI_API_KEY | https://aistudio.google.com |
| trello | TRELLO_API_KEY, TRELLO_TOKEN | https://trello.com/power-ups/admin |
| goplaces | GOOGLE_PLACES_API_KEY | https://console.cloud.google.com |
| feishu-* | FEISHU_* | 飞书开放平台 |

### 4. 系统 Skills - 需要 CLI 工具安装

| Skill | 所需二进制 | 安装方式 |
|-------|-----------|----------|
| github | gh | `brew install gh` / `apt install gh` |
| gemini | gemini | `brew install gemini-cli` |
| spotify-player | spogo 或 spotify_player | `brew install spogo` |
| obsidian | obsidian-cli | 需手动安装 |
| 1password | op | 1Password CLI |
| video-frames | ffmpeg | `brew install ffmpeg` |
| openai-whisper | whisper | `pip install openai-whisper` |
| himalaya | himalaya | IMAP CLI |
| sherpa-onnx-tts | sherpa-onnx | 需编译安装 |

### 5. 系统 Skills - macOS 专用

| Skill | 功能 |
|-------|------|
| apple-reminders | 苹果提醒事项 |
| bear-notes | Bear 笔记 |
| things-mac | Things 3 任务管理 |
| apple-notes | 苹果备忘录 |
| peekaboo | 截图工具 |
| model-usage | 模型使用统计 |

### 6. 系统 Skills - 需要配置

| Skill | 配置项 |
|-------|--------|
| discord | channels.discord.token |
| slack | channels.slack |
| bluesky | blucli 配置 |
| whatsapp | wacli 配置 |
| sonos | sonoscli 配置 |

## 测试策略

### 阶段 1: 基础依赖检查

```bash
# 检查 Node.js
node --version

# 检查 Python
python3 --version

# 检查常用工具
which curl jq rg git

# 检查 OpenClaw
openclaw --version
openclaw status
```

### 阶段 2: 工作区 Skills 测试

```bash
# 1. clawdbot-filesystem (无需配置)
cd ~/.openclaw/workspace/skills/clawdbot-filesystem
ls -la

# 2. find-skills (需要 npx)
npx skills --version

# 3. tavily-search (需要 API key)
echo $TAVILY_API_KEY  # 检查是否设置

# 4. self-improving-agent
ls -la ~/.openclaw/workspace/.learnings/

# 5. elite-longterm-memory
cat ~/.openclaw/workspace/SESSION-STATE.md 2>/dev/null || echo "未创建"
```

### 阶段 3: 系统 Skills 快速测试

```bash
# weather (无需 API key)
curl -s "wttr.in/Beijing?format=3"

# healthcheck
openclaw security audit

# session-logs
openclaw sessions list --limit 5
```

### 阶段 4: 环境检查脚本

创建检查脚本 `skills-check.sh`:

```bash
#!/bin/bash

echo "=== OpenClaw Skills 依赖检查 ==="

# 基础工具
check_bin() {
    if command -v $1 &> /dev/null; then
        echo "✓ $1: $(command -v $1)"
    else
        echo "✗ $1: 未安装"
    fi
}

# 环境变量
check_env() {
    if [ -n "${!1}" ]; then
        echo "✓ $1: 已设置 (${!1:0:8}...)"
    else
        echo "✗ $1: 未设置"
    fi
}

echo ""
echo "## 基础工具"
check_bin node
check_bin python3
check_bin curl
check_bin jq
check_bin git
check_bin tmux

echo ""
echo "## OpenClaw CLI"
check_bin openclaw
if command -v openclaw &> /dev/null; then
    openclaw --version
fi

echo ""
echo "## 环境变量"
check_env OPENAI_API_KEY
check_env TAVILY_API_KEY
check_env NOTION_API_KEY
check_env ELEVENLABS_API_KEY
check_env GEMINI_API_KEY
check_env GH_TOKEN

echo ""
echo "## Skills 目录"
echo "工作区 skills: $(ls -d ~/.openclaw/workspace/skills/*/ 2>/dev/null | wc -l)"
echo "系统 skills: $(ls -d ~/.nvm/versions/node/v22.22.0/lib/node_modules/openclaw/skills/*/ 2>/dev/null | wc -l)"
```

## 需要你提供的内容

### 必需 (用于完整测试)

1. **API Keys** (如需要测试相关 skills):
   - [ ] OPENAI_API_KEY
   - [ ] TAVILY_API_KEY
   - [ ] NOTION_API_KEY
   - [ ] ELEVENLABS_API_KEY
   - [ ] GEMINI_API_KEY
   - [ ] GH_TOKEN (GitHub)

2. **CLI 工具** (如需要测试):
   - [ ] gh (GitHub CLI)
   - [ ] gemini (Gemini CLI)
   - [ ] ffmpeg
   - [ ] tmux
   - [ ] obsidian-cli

3. **配置** (如需要测试):
   - [ ] Discord bot token
   - [ ] Slack bot token
   - [ ] 飞书应用凭证

### 可选 (macOS 专用)

- [ ] 1Password CLI
- [ ] spogo (Spotify)
- [ ] 苹果应用访问权限

## 测试输出格式

每个 skill 的测试结果:

```markdown
## skill-name

- [ ] 依赖检查: PASS/FAIL
- [ ] 环境检查: PASS/FAIL/SKIP
- [ ] 功能测试: PASS/FAIL/SKIP
- [ ] 备注: ...
```

## 下一步

1. 运行基础依赖检查
2. 确认需要测试哪些 skills
3. 提供相应的 API keys 和配置
4. 执行自动化测试脚本
5. 生成测试报告
