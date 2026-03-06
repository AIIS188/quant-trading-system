# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

---

## 📊 量化交易技能 (Quant Trading Skill)

**位置**: `/root/.openclaw/workspace/skills/quant-trading-strategy/`

**版本**: v2.0 - K 线增强版 (2026-03-07)

### 核心能力

- 盘中实时 K 线监控 (每 5 分钟)
- 5 大策略：龙头接力、早盘突破、盘中回调、尾盘买入、情绪周期
- K 线过滤：5 日线、量比、换手率、上影线
- 自动止损/止盈：破 5 日线、放量滞涨、顶部背离
- 模拟盘执行 + 每日复盘

### 使用方式

```bash
# 自动交易 (交易时间)
cd /root/.openclaw/workspace/quant-trading
python3 auto_trading.py --interval 300

# 每日扫描
python3 main.py --scan

# 查看持仓
cat data/paper/paper_state.json | jq
```

### 配置参数

**买入过滤**:
- 5 日均线向上：✅
- 量比 > 1.5
- 换手率 > 10%
- 上影线 < 3%

**止损条件**:
- 跌破 5 日线
- 当日跌幅 > -5%
- 放量下跌 (量比>2 且跌幅>3%)

**止盈条件**:
- 盈利>30% + 放量滞涨
- 跌破 10 日线 (盈利>10% 时)
- 高位长上影 (>5%) + 缩量

### 实战检验

- **下个交易日**: 2026-03-09 (周一) 09:20
- **复盘时间**: 2026-03-09 20:00
- **当前持仓**: 000533 顺钠股份、605268 王力安防

### 相关文档

- `quant-trading/STRATEGY_AND_DATA.md` - 策略详解
- `quant-trading/STRATEGY_OPTIMIZATION_20260307.md` - 优化日志
- `quant-trading/docs/OPTIMIZATION_SUMMARY_20260307.md` - 总结报告

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## 已配置的环境变量 (2026-03-05)

### API Keys

| 变量 | 用途 | 状态 |
|------|------|------|
| `TAVILY_API_KEY` | Tavily AI 搜索 | ✅ 已配置 |
| `GH_TOKEN` | GitHub API 访问 | ✅ 已配置 |

### 已安装工具

| 工具 | 版本 | 用途 |
|------|------|------|
| `jq` | 1.6 | JSON 处理 |
| `rg` (ripgrep) | 13.0.0 | 快速文本搜索 |
| `gh` | 2.4.0 | GitHub CLI |
| `node` | v22.22.0 | JavaScript 运行时 |
| `python3` | 系统版本 | Python 脚本 |
| `curl` | 系统版本 | HTTP 请求 |
| `git` | 系统版本 | 版本控制 |
| `tmux` | 系统版本 | 终端复用 |

### GitHub 用户

- **用户名:** AIIS188
- **主页:** https://github.com/AIIS188

---

Add whatever helps you do your job. This is your cheat sheet.
