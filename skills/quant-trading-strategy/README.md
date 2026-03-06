# 量化交易策略 Skill

A 股短线量化交易策略执行与实时监控系统 (v2.0 - K 线增强版)

## 快速开始

```bash
# 进入项目目录
cd /root/.openclaw/workspace/quant-trading

# 启动自动交易
python3 auto_trading.py --interval 300

# 每日扫描
python3 main.py --scan
```

## 核心功能

- 📊 **5 大策略**: 龙头接力、早盘突破、盘中回调、尾盘买入、情绪周期
- 🎯 **K 线增强**: 买入过滤 + 卖出判断 + 实时监控
- 🛡️ **严格风控**: 单笔≤10%、回撤≤8%、日亏≤3%
- 📈 **模拟盘**: 安全验证策略，无实盘风险
- 📝 **自动复盘**: 每日/每周自动生成报告

## 文档

- [SKILL.md](./SKILL.md) - 完整使用说明
- [STRATEGY_AND_DATA.md](../../quant-trading/STRATEGY_AND_DATA.md) - 策略详解
- [OPTIMIZATION_SUMMARY_20260307.md](../../quant-trading/docs/OPTIMIZATION_SUMMARY_20260307.md) - v2.0 优化报告

## 版本

- **v2.0** (2026-03-07) - K 线增强版
- **v1.0** (2026-03-05) - 基础版
