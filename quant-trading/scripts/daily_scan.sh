#!/bin/bash
# 每日市场扫描脚本
# 添加到 crontab: 30 15 * * 1-5 /root/.openclaw/workspace/quant-trading/scripts/daily_scan.sh

cd /root/.openclaw/workspace/quant-trading

# 记录日志
LOG_FILE="logs/scan_$(date +%Y%m%d).log"

echo "========================================" >> $LOG_FILE
echo "扫描时间：$(date '+%Y-%m-%d %H:%M:%S')" >> $LOG_FILE
echo "========================================" >> $LOG_FILE

# 执行扫描
python3 main.py --scan 2>&1 | tee -a $LOG_FILE

echo "" >> $LOG_FILE
echo "扫描完成" >> $LOG_FILE
echo "" >> $LOG_FILE
