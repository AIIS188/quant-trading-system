# Skill 自动安装问题解决方案

**日期:** 2026-03-05  
**问题:** `npx skills add` 和 `git clone` 超时导致无法自动部署 skills  
**状态:** ✅ 已解决

---

## 问题分析

### 原始错误

```
■  Failed to clone repository
│
│  Clone timed out after 60s. This often happens with private repos that require authentication.
```

### 根本原因

| 原因 | 说明 |
|------|------|
| **超时时间过短** | `npx skills add` 默认 60s 超时，大仓库或慢网络时不够 |
| **认证传递问题** | `GH_TOKEN` 环境变量未正确传递给 git clone |
| **无重试机制** | 一次失败就直接报错，没有自动重试 |
| **无降级方案** | 只有一种安装方式，失败后无备选方案 |

---

## 解决方案

### 脚本：`scripts/install-skill.sh`

**特性:**
- ✅ 3 种安装方法自动降级
- ✅ 可配置超时时间 (默认 120s)
- ✅ 自动重试 (最多 3 次，每次增加 60s)
- ✅ 自动获取 GitHub Token
- ✅ 详细日志输出

**安装方法 (按优先级):**

1. **npx skills add** - 首选，标准方式
2. **git clone** - 带认证，支持私有仓库
3. **GitHub Raw** - 直接下载文件，最轻量

---

## 使用方法

### 基本用法

```bash
# 安装 skill vetting
~/openclaw/workspace/scripts/install-skill.sh hugomrtz/skill-vetting-clawhub@clawhub-skill-vetting

# 安装 security scanner
~/openclaw/workspace/scripts/install-skill.sh affaan-m/everything-claude-code/security-review
```

### 自定义超时

```bash
# 设置 180 秒超时
./install-skill.sh owner/repo@skill 180
```

### 环境变量

```bash
# 设置 GitHub Token (可选，用于私有仓库)
export GH_TOKEN="github_pat_..."

# 设置 Skills 目录 (可选)
export SKILLS_DIR="$HOME/.openclaw/workspace/skills"
```

---

## 已安装 Skills 验证

```bash
# 检查已安装的 skills
clawhub list

# 输出:
# elite-longterm-memory  1.2.3
# clawdbot-filesystem  1.0.2
# self-improving-agent  1.0.11
# tavily-search  1.0.0
# find-skills  0.1.0
# skill-scanner  0.1.2      ← 新增
# security-scanner  1.0.0  ← 新增
```

### 测试 skill-scanner

```bash
# 扫描 tavily-search skill
python3 ~/.openclaw/workspace/skills/skill-scanner/skill_scanner.py ~/.openclaw/workspace/skills/tavily-search

# 输出:
# Verdict: APPROVED - No critical or high-severity issues detected
```

---

## 故障排除

### 问题 1: 仍然超时

```bash
# 增加超时时间
./install-skill.sh owner/repo@skill 300  # 5 分钟
```

### 问题 2: 认证失败

```bash
# 检查 token 是否有效
export GH_TOKEN="github_pat_..."
curl -H "Authorization: token $GH_TOKEN" https://api.github.com/user

# 如果失败，重新生成 token:
# https://github.com/settings/tokens
```

### 问题 3: 仓库不存在

```bash
# 验证仓库 URL
curl -sL https://api.github.com/repos/owner/repo | jq '.name'

# 如果返回 null，仓库不存在或无权限
```

### 问题 4: 网络问题

```bash
# 测试 GitHub 连接
curl -I https://github.com

# 如果失败，检查网络或配置代理
export HTTPS_PROXY="http://proxy:port"
```

---

## 最佳实践

### 1. 预检查

```bash
# 安装前检查
echo "GitHub Token: ${GH_TOKEN:+已设置}"
echo "Skills 目录：$SKILLS_DIR"
echo "网络连接：$(curl -sI github.com | head -1)"
```

### 2. 批量安装

```bash
#!/bin/bash
skills=(
  "hugomrtz/skill-vetting-clawhub@clawhub-skill-vetting"
  "affaan-m/everything-claude-code/security-review"
  "trailofbits/skills@solana-vulnerability-scanner"
)

for skill in "${skills[@]}"; do
  ./install-skill.sh "$skill" || echo "跳过：$skill"
done
```

### 3. 验证安装

```bash
# 安装后验证
verify_skill() {
  local name=$1
  local dir="$SKILLS_DIR/$name"
  
  if [ -f "$dir/SKILL.md" ]; then
    echo "✓ $name"
  else
    echo "✗ $name (缺少 SKILL.md)"
  fi
}

verify_skill "skill-scanner"
verify_skill "security-scanner"
```

---

## 100/3 法则实现

脚本遵循 100/3 法则:

- **100% 自动化** - 无需人工干预
- **3 次重试** - 每次失败后自动重试
- **3 种方法** - 自动降级到备选方案
- **超时递增** - 每次重试增加 60s 超时

---

## 文件清单

| 文件 | 用途 |
|------|------|
| `scripts/install-skill.sh` | Skill 自动安装脚本 |
| `scripts/test-all-skills.sh` | Skills 自动化测试脚本 |
| `skills-test-results.md` | 测试报告 |
| `skill-install-fix.md` | 本文档 |

---

## 总结

**问题:** 无法自动从 clawhub 部署 skills  
**原因:** 超时 + 认证 + 无重试  
**解决:** 多方法降级 + 自动重试 + 可配置超时  
**状态:** ✅ 已解决并验证

**后续:** 使用 `scripts/install-skill.sh` 安装新 skills，不再受超时问题影响。
