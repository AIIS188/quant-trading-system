#!/bin/bash
# 盘中实时监控启动脚本

echo "============================================================"
echo "A 股量化交易系统 - 盘中实时监控"
echo "============================================================"
echo ""

# 检查是否在交易时间
HOUR=$(date +%H)
MINUTE=$(date +%M)
DAY_OF_WEEK=$(date +%u)

# 检查是否工作日
if [ $DAY_OF_WEEK -ge 6 ]; then
    echo "❌ 今日是周末，休市"
    exit 0
fi

# 检查时间
TIME_NUM=$((HOUR * 100 + MINUTE))

if [ $TIME_NUM -lt 925 ]; then
    echo "⏰ 还未开盘，当前时间：${HOUR}:${MINUTE}"
    echo "   集合竞价：09:15-09:25"
    echo "   连续竞价：09:30-11:30, 13:00-15:00"
    exit 0
fi

if [ $TIME_NUM -gt 1500 ]; then
    echo "✅ 已收盘，当前时间：${HOUR}:${MINUTE}"
    echo "   运行复盘程序..."
    cd /root/.openclaw/workspace/quant-trading
    python3 main.py --review
    exit 0
fi

# 启动实时监控
echo "🚀 启动盘中实时监控..."
echo "   时间：${HOUR}:${MINUTE}"
echo "   监控股票：龙头股池"
echo "   扫描间隔：5 分钟"
echo ""

cd /root/.openclaw/workspace/quant-trading

# 运行监控
if [ "$1" == "--background" ]; then
    echo "后台运行..."
    nohup python3 src/intraday_strategy.py > logs/intraday_$(date +%Y%m%d).log 2>&1 &
    echo "✅ 监控已启动，日志：logs/intraday_$(date +%Y%m%d).log"
else
    python3 src/intraday_strategy.py
fi

echo ""
echo "============================================================"
