#!/bin/bash
# OpenClaw Skill 自动安装脚本
# 解决 npx skills add 超时和认证问题
# 遵循 100/3 法则：最多 3 次重试，每次增加超时时间

set -e

# 配置
DEFAULT_TIMEOUT=120
MAX_RETRIES=3
SKILLS_DIR="${SKILLS_DIR:-$HOME/.openclaw/workspace/skills}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() { echo -e "$1" | tee -a /tmp/skill-install.log; }
die() { log "${RED}✗ $1${NC}"; exit 1; }

# 获取 GitHub Token
get_github_token() {
    if [ -n "$GH_TOKEN" ]; then
        echo "$GH_TOKEN"
    elif [ -f "$HOME/.config/gh/hosts.yml" ]; then
        grep -A1 "oauth_token" "$HOME/.config/gh/hosts.yml" 2>/dev/null | tail -1 | tr -d ' '
    else
        echo ""
    fi
}

# 方法 1: 使用 npx skills add (首选)
install_via_npx() {
    local skill=$1
    local timeout=$2
    
    log "${BLUE}方法 1: npx skills add (超时：${timeout}s)${NC}"
    
    if timeout "$timeout" npx skills add "$skill" -g -y 2>&1; then
        return 0
    fi
    return 1
}

# 方法 2: 直接 git clone
install_via_git() {
    local owner=$1
    local repo=$2
    local skill_name=$3
    local timeout=$4
    local token=$(get_github_token)
    
    log "${BLUE}方法 2: git clone (超时：${timeout}s)${NC}"
    
    local clone_url
    if [ -n "$token" ]; then
        clone_url="git@github.com:${owner}/${repo}.git"
    else
        clone_url="https://github.com/${owner}/${repo}.git"
    fi
    
    local temp_dir="/tmp/skill-clone-$$"
    rm -rf "$temp_dir"
    
    if timeout "$timeout" git clone --depth=1 "$clone_url" "$temp_dir" 2>&1; then
        # 查找 skill 目录
        local skill_dir="$temp_dir/skills/${skill_name}"
        if [ -d "$skill_dir" ]; then
            cp -r "$skill_dir" "$SKILLS_DIR/"
            rm -rf "$temp_dir"
            return 0
        fi
        
        # 可能是根目录就是 skill
        if [ -f "$temp_dir/SKILL.md" ]; then
            mv "$temp_dir" "$SKILLS_DIR/${skill_name}"
            return 0
        fi
        
        # 查找 SKILL.md
        local found=$(find "$temp_dir" -name "SKILL.md" -type f | head -1)
        if [ -n "$found" ]; then
            local skill_folder=$(dirname "$found")
            cp -r "$skill_folder" "$SKILLS_DIR/${skill_name}"
            rm -rf "$temp_dir"
            return 0
        fi
        
        rm -rf "$temp_dir"
        log "${YELLOW}未找到 skill 目录${NC}"
    fi
    
    rm -rf "$temp_dir"
    return 1
}

# 方法 3: 从 raw.githubusercontent.com 下载
install_via_raw() {
    local owner=$1
    local repo=$2
    local branch=$3
    local skill_name=$4
    local timeout=$5
    
    log "${BLUE}方法 3: 从 GitHub Raw 下载 (超时：${timeout}s)${NC}"
    
    local skill_dir="$SKILLS_DIR/${skill_name}"
    mkdir -p "$skill_dir"
    
    # 下载 SKILL.md
    local raw_url="https://raw.githubusercontent.com/${owner}/${repo}/${branch}/skills/${skill_name}/SKILL.md"
    if timeout "$timeout" curl -sL "$raw_url" -o "$skill_dir/SKILL.md" 2>&1; then
        if [ -s "$skill_dir/SKILL.md" ]; then
            log "${GREEN}成功下载 SKILL.md${NC}"
            # 尝试下载其他文件
            local files_url="https://api.github.com/repos/${owner}/${repo}/contents/skills/${skill_name}"
            local files=$(curl -sL "$files_url" | grep '"name"' | sed 's/.*"name": "\([^"]*\)".*/\1/' | grep -v SKILL.md)
            
            for file in $files; do
                curl -sL "https://raw.githubusercontent.com/${owner}/${repo}/${branch}/skills/${skill_name}/${file}" -o "$skill_dir/${file}" 2>/dev/null &
            done
            wait
            
            return 0
        fi
    fi
    
    rm -rf "$skill_dir"
    return 1
}

# 解析 skill 标识符
parse_skill_id() {
    local skill_id=$1
    
    # 格式：owner/repo@skill 或 owner/repo/skill
    if [[ "$skill_id" =~ ^([^/]+)/([^/@]+)@(.+)$ ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
        SKILL_NAME="${BASH_REMATCH[3]}"
        BRANCH="main"
        return 0
    elif [[ "$skill_id" =~ ^([^/]+)/([^/]+)/(.+)$ ]]; then
        OWNER="${BASH_REMATCH[1]}"
        REPO="${BASH_REMATCH[2]}"
        SKILL_NAME="${BASH_REMATCH[3]}"
        BRANCH="main"
        return 0
    fi
    
    return 1
}

# 主安装函数
install_skill() {
    local skill_id=$1
    local timeout=${2:-$DEFAULT_TIMEOUT}
    
    log "========================================"
    log "安装 skill: $skill_id"
    log "超时：${timeout}s | 最大重试：$MAX_RETRIES"
    log "========================================"
    
    # 解析 skill 标识符
    if ! parse_skill_id "$skill_id"; then
        die "无法解析 skill 标识符：$skill_id (期望格式：owner/repo@skill)"
    fi
    
    log "所有者：$OWNER"
    log "仓库：$REPO"
    log "Skill: $SKILL_NAME"
    log ""
    
    # 重试循环
    local attempt=1
    local current_timeout=$timeout
    
    while [ $attempt -le $MAX_RETRIES ]; do
        log "${BLUE}=== 尝试 $attempt/$MAX_RETRIES (超时：${current_timeout}s) ===${NC}"
        
        # 方法 1: npx skills add
        if install_via_npx "$skill_id" "$current_timeout"; then
            log "${GREEN}✓ 安装成功 (方法 1: npx)${NC}"
            return 0
        fi
        
        # 方法 2: git clone
        if install_via_git "$OWNER" "$REPO" "$SKILL_NAME" "$current_timeout"; then
            log "${GREEN}✓ 安装成功 (方法 2: git)${NC}"
            return 0
        fi
        
        # 方法 3: raw download
        if install_via_raw "$OWNER" "$REPO" "$BRANCH" "$SKILL_NAME" "$current_timeout"; then
            log "${GREEN}✓ 安装成功 (方法 3: raw)${NC}"
            return 0
        fi
        
        attempt=$((attempt + 1))
        current_timeout=$((current_timeout + 60))  # 每次增加 60s 超时
        
        if [ $attempt -le $MAX_RETRIES ]; then
            log "${YELLOW}重试前等待 2 秒...${NC}"
            sleep 2
        fi
    done
    
    die "所有方法都失败了"
}

# 验证安装
verify_install() {
    local skill_name=$1
    local skill_dir="$SKILLS_DIR/$skill_name"
    
    log ""
    log "${BLUE}=== 验证安装 ===${NC}"
    
    if [ -d "$skill_dir" ]; then
        if [ -f "$skill_dir/SKILL.md" ]; then
            log "${GREEN}✓ Skill 已安装：$skill_dir${NC}"
            log "文件列表:"
            find "$skill_dir" -type f | head -10
            return 0
        else
            log "${YELLOW}⚠ 目录存在但缺少 SKILL.md${NC}"
            return 1
        fi
    else
        log "${RED}✗ Skill 目录不存在${NC}"
        return 1
    fi
}

# 使用帮助
show_help() {
    cat << EOF
用法：$0 <skill-id> [timeout]

skill-id 格式:
  owner/repo@skill    - 例如：hugomrtz/skill-vetting-clawhub@clawhub-skill-vetting
  owner/repo/skill    - 例如：affaan-m/everything-claude-code/security-review

示例:
  $0 hugomrtz/skill-vetting-clawhub@clawhub-skill-vetting
  $0 affaan-m/everything-claude-code/security-review 180

环境变量:
  GH_TOKEN          - GitHub Personal Access Token (可选，用于私有仓库)
  SKILLS_DIR        - Skills 安装目录 (默认：~/.openclaw/workspace/skills)

安装策略:
  1. npx skills add (首选)
  2. git clone (带认证)
  3. GitHub Raw 下载

遵循 100/3 法则：最多 3 次重试，每次增加超时时间
EOF
}

# 主程序
main() {
    if [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
        show_help
        exit 0
    fi
    
    if [ -z "$1" ]; then
        die "请提供 skill 标识符 (使用 -h 查看帮助)"
    fi
    
    # 确保目标目录存在
    mkdir -p "$SKILLS_DIR"
    
    # 安装
    if install_skill "$1" "${2:-$DEFAULT_TIMEOUT}"; then
        # 提取 skill 名称进行验证
        parse_skill_id "$1"
        verify_install "$SKILL_NAME"
        
        log ""
        log "${GREEN}========================================${NC}"
        log "${GREEN}安装完成！${NC}"
        log "${GREEN}========================================${NC}"
        exit 0
    else
        log ""
        log "${RED}========================================${NC}"
        log "${RED}安装失败${NC}"
        log "${RED}========================================${NC}"
        log ""
        log "建议:"
        log "1. 检查网络连接"
        log "2. 设置 GH_TOKEN 环境变量"
        log "3. 尝试手动安装：cd $SKILLS_DIR && git clone ..."
        exit 1
    fi
}

main "$@"

# SSH 连接测试函数
test_ssh_connection() {
    if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
        return 0
    fi
    return 1
}
