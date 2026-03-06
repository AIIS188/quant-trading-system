# 量化交易技能封装学习日志

**日期**: 2026-03-07  
**类别**: skill_creation  
**优先级**: high  
**状态**: completed

---

## 学习内容

### 背景

老板指出我应该：
1. 好好学习现有 skills 的结构和使用方式
2. 将自己的新能力 (K 线增强策略) 封装成 skill 形式
3. 参考标准 skill 模式进行记录和复用

### 学习的 Skill 结构

#### 1. Weather Skill (简洁型)

**特点**:
- YAML frontmatter 定义 name、description、metadata
- 清晰的 When to Use / When NOT to Use
- 快速命令参考
- 格式代码/参数说明

**结构**:
```markdown
---
name: weather
description: "一句话说明用途和使用场景"
metadata: { "openclaw": { "emoji": "🌤️", "requires": { "bins": ["curl"] } } }
---

# Weather Skill

## When to Use
✅ **USE this skill when:**
- 具体使用场景 1
- 具体使用场景 2

## When NOT to Use
❌ **DON'T use this skill when:**
- 不适用的场景 1
- 不适用的场景 2

## Commands
### 功能分类 1
```bash
命令示例
```

## Notes
- 注意事项
```

#### 2. GitHub Skill (功能型)

**特点**:
- 更详细的 metadata (包含安装说明)
- 分类详细的命令参考
- JSON 输出和模板示例
- 故障排查指南

**结构亮点**:
- `metadata.openclaw.install` - 依赖安装
- `## Common Commands` - 按功能分类
- `## Templates` - 常用模板
- `## Notes` - 使用提示

#### 3. Self-Improvement Skill (文档型)

**特点**:
- 超详细文档 (>19KB)
- 完整的工作流程说明
- 多 agent 支持
- 推广机制 (promote to CLAUDE.md/AGENTS.md)

**结构亮点**:
- `## Quick Reference` - 快速参考表
- `## Logging Format` - 日志格式模板
- `## Promotion Targets` - 推广目标说明
- `## Detection Triggers` - 自动检测触发条件

---

## 封装的 Skill: Quant Trading Strategy v2.0

### 采用的结构

结合以上三个 skill 的优点，我设计了量化交易 skill:

```markdown
---
name: quant-trading-strategy
description: "A 股量化交易策略执行与监控。Use when: (1)...(2)...(3)... NOT for: ..."
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["python3", "pip"] },
        "install": [...]
      }
  }
---

# 量化交易策略 Skill

## 当使用时 / 不使用时
✅ **使用此 skill 当:** ...
❌ **不使用此 skill 当:** ...

## 系统架构
```
项目结构图
```

## 核心策略
1. 龙头接力策略 v2.0
2. 早盘突破策略 v2.0
3. 盘中回调策略 v2.0
4. 尾盘买入策略 v2.0

## 快速命令
```bash
# 启动自动交易
python3 auto_trading.py --interval 300

# 每日扫描
python3 main.py --scan
```

## 策略参数配置
```json
{ ... }
```

## 自动运行时间表
| 时间 | 任务 | 说明 |
|------|------|------|

## 风控规则
| 指标 | 限制 | 动作 |

## 输出示例
- 交易信号示例
- 持仓监控示例
- 每日复盘示例

## 数据源
| 数据 | 来源 | 用途 |

## 故障排查
### 问题 1: ...
### 问题 2: ...

## 版本历史
### v2.0 - K 线增强版
### v1.0 - 基础版
```

### 关键决策

1. **使用中文还是英文**:
   - 决策：使用中文
   - 原因：策略针对 A 股市场，用户是中文使用者
   - 权衡：skill 名称用英文 (quant-trading-strategy) 便于搜索

2. **详细程度**:
   - 决策：介于 GitHub 和 Self-Improvement 之间
   - 原因：需要足够详细以便复用，但不能过于冗长
   - 结果：约 7.8KB

3. **策略细节是否全部写入**:
   - 决策：核心策略写入 SKILL.md，详细逻辑保留在代码和文档中
   - 原因：SKILL.md 是使用指南，不是技术文档
   - 权衡：提供关键参数和条件，完整逻辑见代码

4. **是否包含故障排查**:
   - 决策：包含
   - 原因：参考 GitHub skill 的做法，实用性强
   - 内容：3 个常见问题及解决方案

---

## 创建的 Files

```
/root/.openclaw/workspace/skills/quant-trading-strategy/
├── SKILL.md          # 主文档 (7.8KB)
├── _meta.json        # 元数据 (268B)
└── README.md         # 简要说明 (677B)
```

同时更新:
- `TOOLS.md` - 添加量化技能使用指南
- `.learnings/2026-03-07-skill-creation.md` - 本学习日志

---

## 关键收获

### 1. Skill 结构的核心要素

**必须包含**:
- ✅ YAML frontmatter (name, description, metadata)
- ✅ When to Use / When NOT to Use
- ✅ 快速命令参考
- ✅ 核心功能说明

**可选但推荐**:
- ✅ 系统架构图
- ✅ 参数配置说明
- ✅ 输出示例
- ✅ 故障排查
- ✅ 版本历史

### 2. Description 写法

**好**:
> "A 股量化交易策略执行与监控。Use when: (1) 盘中实时扫描交易信号，(2) 监控持仓 K 线止损/止盈，(3) 执行龙头接力/突破/回调策略，(4) 生成每日复盘报告。NOT for: 实盘交易执行 (需人工确认), 低流动性股票分析，或非 A 股市场。"

**特点**:
- 一句话说明核心功能
- 列出具体使用场景 (1)(2)(3)(4)
- 明确说明 NOT for 的场景

### 3. Metadata 设计

```json
{
  "openclaw": {
    "emoji": "📊",
    "requires": { "bins": ["python3", "pip"] },
    "install": [
      {
        "id": "deps",
        "kind": "pip",
        "package": "pandas requests numpy",
        "label": "安装量化交易依赖"
      }
    ]
  }
}
```

**要点**:
- emoji 便于识别
- requires 说明依赖
- install 提供安装指南

### 4. 命令组织方式

按**使用场景**而非**文件结构**组织:

**好**:
```markdown
## 快速命令
### 启动自动交易
### 每日市场扫描
### 查看持仓和日志
### 获取实时 K 线
```

**不好**:
```markdown
## 命令
### auto_trading.py
### main.py
### realtime_monitor.py
```

---

## 自我反思

### 做得好的地方

1. ✅ **主动学习**: 老板提出后立刻学习现有 skills
2. ✅ **结构化思维**: 分析多个 skill 后提取最佳实践
3. ✅ **完整封装**: 不仅写 SKILL.md，还创建_meta.json 和 README
4. ✅ **及时记录**: 创建学习日志，记录决策过程
5. ✅ **更新 TOOLS.md**: 将技能使用指南写入本地笔记

### 需要改进的地方

1. ⚠️ **学习不够早**: 应该更早学习 skill 结构，而不是等老板提醒
2. ⚠️ **复用意识弱**: K 线增强功能开发完成后，没有第一时间想到封装成 skill
3. ⚠️ **文档滞后**: 代码写完后才补文档，应该同步进行

### 未来改进

1. **新能力立即封装**: 以后开发新功能后，立即封装成 skill
2. **定期 review skills**: 每周查看现有 skills，发现可复用的模式
3. **向其他 skills 学习**: 继续学习更多 skills 的设计思路

---

## 推广建议

这个学习应该推广到:

1. **AGENTS.md** - 添加"新能力封装成 skill"的工作流程
2. **SOUL.md** - 添加"主动学习、及时封装"的原则

---

## 相关条目

- **参见**: LRN-20260305-001 (量化交易系统搭建)
- **参见**: STRATEGY_OPTIMIZATION_20260307 (v2.0 优化日志)
- **推广至**: TOOLS.md (已更新)

---

**Logged**: 2026-03-07T01:45:00+08:00  
**Priority**: high  
**Status**: completed  
**Area**: backend  
**Source**: user_feedback (老板提醒)  
**Tags**: skill, documentation, quant-trading
