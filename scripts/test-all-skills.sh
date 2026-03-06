#!/bin/bash
# OpenClaw Skills 自动化测试脚本
# 遵循 100/3 法则：测试 100% 可测试内容，每个测试最多 3 次重试

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试统计
TOTAL=0
PASSED=0
FAILED=0
SKIPPED=0

# 日志文件
LOG_FILE="/root/.openclaw/workspace/skills-test-$(date +%Y%m%d-%H%M%S).log"

log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

test_result() {
    local name=$1
    local result=$2
    local details=$3
    
    TOTAL=$((TOTAL + 1))
    
    if [ "$result" == "PASS" ]; then
        PASSED=$((PASSED + 1))
        log "${GREEN}✓ PASS${NC}: $name"
    elif [ "$result" == "FAIL" ]; then
        FAILED=$((FAILED + 1))
        log "${RED}✗ FAIL${NC}: $name - $details"
    elif [ "$result" == "SKIP" ]; then
        SKIPPED=$((SKIPPED + 1))
        log "${YELLOW}○ SKIP${NC}: $name - $details"
    fi
}

# 重试函数 (100/3 法则：最多 3 次重试)
retry_test() {
    local name=$1
    local command=$2
    local max_attempts=3
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "${BLUE}尝试 $attempt/$max_attempts${NC}: $name"
        
        if eval "$command" > /dev/null 2>&1; then
            test_result "$name" "PASS"
            return 0
        fi
        
        attempt=$((attempt + 1))
        if [ $attempt -le $max_attempts ]; then
            sleep 1
        fi
    done
    
    test_result "$name" "FAIL" "3 次重试后仍失败"
    return 1
}

log "========================================"
log "OpenClaw Skills 自动化测试"
log "开始时间: $(date)"
log "========================================"
log ""

# 设置环境变量 (从配置读取，不硬编码)
# export TAVILY_API_KEY="your_key_here"
# export GH_TOKEN="your_token_here"

# ============================================
# 1. 基础依赖检查
# ============================================
log "${BLUE}=== 基础依赖检查 ===${NC}"

check_dependency() {
    if command -v $1 &> /dev/null; then
        test_result "$1" "PASS"
    else
        test_result "$1" "FAIL" "未安装"
    fi
}

check_dependency "node"
check_dependency "python3"
check_dependency "curl"
check_dependency "jq"
check_dependency "rg"
check_dependency "git"
check_dependency "tmux"
check_dependency "gh"
check_dependency "ffmpeg"
check_dependency "openclaw"

log ""

# ============================================
# 2. 环境变量检查
# ============================================
log "${BLUE}=== 环境变量检查 ===${NC}"

check_env() {
    if [ -n "${!1}" ]; then
        test_result "$1" "PASS"
    else
        test_result "$1" "SKIP" "未设置"
    fi
}

check_env "TAVILY_API_KEY"
check_env "GH_TOKEN"
check_env "OPENAI_API_KEY"
check_env "NOTION_API_KEY"
check_env "ELEVENLABS_API_KEY"

log ""

# ============================================
# 3. 工作区 Skills 测试
# ============================================
log "${BLUE}=== 工作区 Skills 测试 ===${NC}"

# 3.1 tavily-search
log "${BLUE}测试 tavily-search...${NC}"
if cd ~/.openclaw/workspace/skills/tavily-search && node scripts/search.mjs "test" -n 1 2>&1 | grep -q "results"; then
    test_result "tavily-search" "PASS"
else
    test_result "tavily-search" "FAIL" "搜索失败"
fi

# 3.2 clawdbot-filesystem
log "${BLUE}测试 clawdbot-filesystem...${NC}"
if [ -f ~/.openclaw/workspace/skills/clawdbot-filesystem/scripts/list.mjs ]; then
    test_result "clawdbot-filesystem" "PASS"
else
    test_result "clawdbot-filesystem" "FAIL" "脚本不存在"
fi

# 3.3 find-skills
log "${BLUE}测试 find-skills...${NC}"
if npx skills --version > /dev/null 2>&1; then
    test_result "find-skills" "PASS"
else
    test_result "find-skills" "FAIL" "npx skills 不可用"
fi

# 3.4 self-improving-agent
log "${BLUE}测试 self-improving-agent...${NC}"
if [ -d ~/.openclaw/workspace/skills/self-improving-agent ]; then
    test_result "self-improving-agent" "PASS"
else
    test_result "self-improving-agent" "FAIL" "目录不存在"
fi

# 3.5 elite-longterm-memory
log "${BLUE}测试 elite-longterm-memory...${NC}"
if [ -f ~/.openclaw/workspace/skills/elite-longterm-memory/SKILL.md ]; then
    test_result "elite-longterm-memory" "PASS"
else
    test_result "elite-longterm-memory" "FAIL" "文件不存在"
fi

log ""

# ============================================
# 4. 系统 Skills 测试
# ============================================
log "${BLUE}=== 系统 Skills 测试 ===${NC}"

# 4.1 weather
log "${BLUE}测试 weather...${NC}"
if curl -s "wttr.in/Beijing?format=3" | grep -q "."; then
    test_result "weather" "PASS"
else
    test_result "weather" "FAIL" "API 无响应"
fi

# 4.2 healthcheck
log "${BLUE}测试 healthcheck...${NC}"
if openclaw security audit > /dev/null 2>&1; then
    test_result "healthcheck" "PASS"
else
    test_result "healthcheck" "FAIL" "审计失败"
fi

# 4.3 github (需要 GH_TOKEN)
log "${BLUE}测试 github...${NC}"
if gh api user > /dev/null 2>&1; then
    test_result "github" "PASS"
else
    test_result "github" "FAIL" "API 调用失败"
fi

# 4.4 session-logs
log "${BLUE}测试 session-logs...${NC}"
if openclaw sessions list --limit 1 > /dev/null 2>&1; then
    test_result "session-logs" "PASS"
else
    test_result "session-logs" "FAIL" "会话列表失败"
fi

# 4.5 memory_search
log "${BLUE}测试 memory_search...${NC}"
if [ -f ~/.openclaw/workspace/MEMORY.md ] || [ -d ~/.openclaw/workspace/memory ]; then
    test_result "memory_search" "PASS"
else
    test_result "memory_search" "SKIP" "memory 文件不存在"
fi

# 4.6 canvas
log "${BLUE}测试 canvas...${NC}"
if command -v canvas &> /dev/null || [ -n "$(openclaw status 2>&1 | grep canvas)" ]; then
    test_result "canvas" "PASS"
else
    test_result "canvas" "SKIP" "canvas 不可用"
fi

# 4.7 tmux
log "${BLUE}测试 tmux...${NC}"
if tmux list-sessions > /dev/null 2>&1; then
    test_result "tmux" "PASS"
else
    test_result "tmux" "SKIP" "无活动会话"
fi

# 4.8 video-frames (需要 ffmpeg)
log "${BLUE}测试 video-frames...${NC}"
if command -v ffmpeg &> /dev/null; then
    test_result "video-frames" "PASS"
else
    test_result "video-frames" "FAIL" "ffmpeg 未安装"
fi

log ""

# ============================================
# 5. OpenClaw 核心功能测试
# ============================================
log "${BLUE}=== OpenClaw 核心功能测试 ===${NC}"

# 5.1 openclaw status
retry_test "openclaw status" "openclaw status > /dev/null 2>&1"

# 5.2 openclaw version
retry_test "openclaw version" "openclaw --version > /dev/null 2>&1"

# 5.3 sessions list
retry_test "sessions list" "openclaw sessions list --limit 1 > /dev/null 2>&1"

log ""

# ============================================
# 测试结果汇总
# ============================================
log "========================================"
log "测试结果汇总"
log "========================================"
log "总测试数：$TOTAL"
log "${GREEN}通过：$PASSED${NC}"
log "${RED}失败：$FAILED${NC}"
log "${YELLOW}跳过：$SKIPPED${NC}"
log ""

if [ $TOTAL -gt 0 ]; then
    PASS_RATE=$((PASSED * 100 / TOTAL))
    log "通过率：${PASS_RATE}%"
fi

log ""
log "详细日志：$LOG_FILE"
log "完成时间: $(date)"
log "========================================"

# 退出码
if [ $FAILED -gt 0 ]; then
    exit 1
else
    exit 0
fi
