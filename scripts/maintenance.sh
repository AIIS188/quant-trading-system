#!/bin/bash
# OpenClaw 自动维护脚本

echo "=== OpenClaw 维护 ==="
echo "时间：$(date)"

# 清理临时文件
echo "清理临时文件..."
rm -rf /tmp/skill-clone-* /tmp/*.log 2>/dev/null

# 检查磁盘
echo "磁盘使用:"
df -h / | tail -1

# 检查技能
echo "已安装技能:"
clawhub list 2>/dev/null

# 检查更新
echo "检查 OpenClaw 更新..."
openclaw update status 2>/dev/null | head -5

echo "维护完成"
