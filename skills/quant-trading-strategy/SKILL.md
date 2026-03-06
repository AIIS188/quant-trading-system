---
name: quant-trading-strategy
description: "A 股量化交易策略执行与监控。Use when: (1) 盘中实时扫描交易信号，(2) 监控持仓 K 线止损/止盈，(3) 执行龙头接力/突破/回调策略，(4) 生成每日复盘报告。NOT for: 实盘交易执行 (需人工确认), 低流动性股票分析，或非 A 股市场。"
metadata:
  {
    "openclaw":
      {
        "emoji": "📊",
        "requires": { "bins": ["python3", "pip"] },
        "install":
          [
            {
              "id": "deps",
              "kind": "pip",
              "package": "pandas requests numpy",
              "label": "安装量化交易依赖",
            },
          ],
      },
  }
---

# 量化交易策略 Skill

A 股短线量化交易策略执行与实时监控系统。

## 当使用时

✅ **使用此 skill 当:**

- "扫描今日交易信号"
- "监控持仓股票"
- "执行龙头接力策略"
- "查看早盘/尾盘机会"
- "生成每日复盘报告"
- "检查 K 线止损/止盈信号"
- "分析市场情绪得分"

## 不使用时

❌ **不使用此 skill 当:**

- 实盘交易执行 → 需人工确认
- 低流动性股票分析 → 策略自动过滤
- 非 A 股市场 (美股/港股) → 数据源不支持
- 历史数据回测 → 使用 `backtest.py` 单独模块
- 基本面分析 → 使用 `data_fetcher.py` 基础数据模块

## 系统架构

```
quant-trading/
├── auto_trading.py          # 自动交易主程序 (v2.0)
├── main.py                  # 每日扫描主程序
├── src/
│   ├── intraday_strategy.py # 盘中实时策略 (K 线增强 v2.0)
│   ├── realtime_monitor.py  # K 线实时监控
│   ├── paper_trading.py     # 模拟盘执行
│   ├── data_fetcher.py      # 基础数据获取
│   ├── hotspot_analyzer.py  # 热点分析
│   ├── strategy_engine.py   # 策略引擎
│   ├── risk_controller.py   # 风控系统
│   └── daily_review.py      # 每日复盘
├── config/
│   └── config.json          # 策略参数配置
├── data/
│   ├── paper/               # 模拟盘数据
│   └── cache/               # 数据缓存
├── logs/                    # 交易日志
└── docs/                    # 文档报告
```

## 核心策略

### 1. 龙头接力策略 v2.0 (K 线增强)

**适用场景**: 情绪上升期的连板龙头

**入场条件**:
- 情绪得分 > 60
- 连板数 ≥ 2
- 封板资金 > 5000 万
- 所属板块是热点
- **K 线确认 (v2.0 新增)**:
  - 5 日均线向上
  - 量比 > 1.5
  - 换手率 > 10%
  - 上影线 < 3%

**出场条件**:
- **止损**: 跌破 5 日线 / 当日跌幅>-5% / 放量下跌
- **止盈**: 盈利>30%+ 放量滞涨 / 跌破 10 日线 / 高位长上影

**仓位**: 单笔 5-10%

**置信度**: 0.7-0.85

### 2. 早盘突破策略 v2.0

**时间**: 09:30-10:30

**条件**:
- 高开 2-5%
- 开盘后继续上涨
- 量比 > 1.5
- K 线确认 (5 日线向上、上影线<3%)

**仓位**: 10%

**置信度**: 0.8

### 3. 盘中回调策略 v2.0

**时间**: 09:35-14:50

**条件**:
- 从日内高点回调 3-5%
- 缩量 (量比<0.8)
- 5 日均线向上
- 最后 3 根 K 线不创新低

**仓位**: 10%

**置信度**: 0.7

### 4. 尾盘买入策略 v2.0

**时间**: 14:30-15:00

**条件**:
- 全天强势 (涨幅 3-7%)
- 尾盘不跳水 (不跌破均价)
- K 线确认 (5 日线向上、上影线<3%)

**仓位**: 10%

**置信度**: 0.85

## 快速命令

### 启动自动交易

```bash
cd /root/.openclaw/workspace/quant-trading

# 连续监控 (交易时间每 5 分钟扫描)
python3 auto_trading.py --interval 300

# 运行一次扫描
python3 auto_trading.py --once

# 测试模式
python3 auto_trading.py --test

# 尾盘策略专项
python3 auto_trading.py --tail
```

### 每日市场扫描

```bash
cd /root/.openclaw/workspace/quant-trading

# 完整扫描 (涨停/情绪/热点/信号)
python3 main.py --scan

# 查看系统状态
python3 main.py --status

# 生成复盘报告
python3 main.py --review
```

### 查看持仓和日志

```bash
# 查看模拟盘持仓
cat /root/.openclaw/workspace/quant-trading/data/paper/paper_state.json | jq

# 查看今日日志
tail -f /root/.openclaw/workspace/quant-trading/logs/daily_$(date +%Y%m%d).log

# 查看自动交易日志
tail -f /root/.openclaw/workspace/quant-trading/logs/auto_trading.log
```

### 获取实时 K 线

```bash
cd /root/.openclaw/workspace/quant-trading

# 测试 K 线获取
python3 -c "
from src.realtime_monitor import RealtimeKLineFetcher
f = RealtimeKLineFetcher()
kline = f.get_realtime_kline('000533', count=30)
print(kline.tail() if kline is not None else '获取失败')
"

# 测试实时行情
python3 -c "
from src.realtime_monitor import RealtimeKLineFetcher
f = RealtimeKLineFetcher()
quote = f.get_realtime_quote('000533')
print(quote if quote else '获取失败')
"
```

## 策略参数配置

编辑 `config/config.json`:

```json
{
  "kline_strategy": {
    "buy": {
      "ma5_up": true,
      "volume_ratio_min": 1.5,
      "turnover_rate_min": 10,
      "upper_shadow_max": 3
    },
    "sell": {
      "stop_loss_ma5": true,
      "stop_loss_change_pct": -5,
      "stop_loss_volume_down": true,
      "take_profit_pct": 30,
      "take_profit_ma10": true
    },
    "monitor": {
      "interval_seconds": 300,
      "tail_interval_seconds": 120
    }
  }
}
```

## 自动运行时间表

### 交易日 (周一至周五)

| 时间 | 任务 | 说明 |
|------|------|------|
| **09:20** | 早盘监控 | 集合竞价后第一次扫描 |
| **09:30-10:30** | 早盘突破 | 每 5 分钟扫描 |
| **10:30-14:30** | 盘中回调 | 每 5 分钟扫描 |
| **14:30-15:00** | 尾盘买入 | 每 2 分钟扫描 (重点) |
| **15:30** | 收盘报告 | 生成每日报告 |
| **20:00** | 晚间复盘 | 深度复盘分析 |

### 设置 Crontab

```bash
crontab -e

# 添加以下任务 (交易日自动运行)
*/5 9-11 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python3 auto_trading.py --interval 300 >> logs/cron.log 2>&1
*/5 13-14 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python3 auto_trading.py --interval 300 >> logs/cron.log 2>&1
*/2 14:30-14:59 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python3 auto_trading.py --interval 120 >> logs/cron.log 2>&1
30 15 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python3 main.py --review >> logs/cron.log 2>&1
0 20 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python3 main.py --review >> logs/cron.log 2>&1
```

## 风控规则

| 指标 | 限制 | 动作 |
|------|------|------|
| 单笔仓位 | ≤ 10% | 强制执行 |
| 单日交易 | ≤ 5 笔 | 停止买入 |
| 单日亏损 | ≤ 3% | 停止交易 |
| 最大回撤 | ≤ 8% | 清仓 |
| 连续亏损 | ≤ 3 次 | 暂停 1 天 |

## 输出示例

### 交易信号

```
✅ 早盘突破信号：000533 顺钠股份
  策略：早盘突破
  价格：15.20 元
  仓位：1000 股
  理由：高开 3.2%, 现涨 4.5%, K 线确认：量比 1.8, 换手 12.3%, 上影 1.2%
  信心：0.8
  止损：14.44 元 (-5%)
  止盈：17.48 元 (+15%)
```

### 持仓监控

```
⚠️ 持仓监控：000533 - 止损：跌破 5 日线 (14.50 < 14.80)
✅ 卖出：000533 @ 14.50 元，盈亏：-380 元
```

### 每日复盘

```
================================================================================
每日交易报告 - 2026-03-09
================================================================================

【市场情绪】
情绪得分：65 分 (上升期)
涨停：72 只，跌停：2 只
连板高度：5 板

【交易统计】
交易次数：3 笔
买入：2 笔，卖出：1 笔
交易金额：28,500 元
胜率：67%

【持仓情况】
000533 顺钠股份：1000 股 @ 14.88 元，浮盈 +320 元 (+2.2%)
605268 王力安防：1000 股 @ 13.94 元，浮盈 +180 元 (+1.3%)

【策略表现】
龙头接力：1 胜 0 负 (100%)
早盘突破：0 胜 0 负 (-)
盘中回调：0 胜 0 负 (-)
```

## 数据源

| 数据 | 来源 | 用途 |
|------|------|------|
| 涨停/跌停板 | akshare | 识别热点、龙头 |
| 龙虎榜 | akshare | 机构/游资动向 |
| K 线数据 | 新浪财经 | 技术分析、实时监控 |
| 行业资金流 | akshare | 板块热度 |
| 概念资金流 | akshare | 题材热度 |
| 北向资金 | akshare | 外资情绪 |

## 故障排查

### 问题 1: 数据获取失败

```bash
# 测试网络连接
ping money.finance.sina.com.cn

# 测试 akshare
python3 -c "import akshare as ak; print(ak.__version__)"

# 重新安装依赖
pip3 install -r requirements.txt
```

### 问题 2: K 线数据为空

```bash
# 检查是否在交易时间
python3 -c "
from src.realtime_monitor import RealtimeMonitor
m = RealtimeMonitor()
print('交易时间:', m.is_market_open())
print('时段:', m.get_market_session())
"

# 休市时间无实时行情，使用日线数据测试
python3 -c "
from src.realtime_monitor import RealtimeKLineFetcher
f = RealtimeKLineFetcher()
kline = f.get_realtime_kline('000533', count=30, scale='240')  # 日线
print(kline.tail() if kline is not None else '获取失败')
"
```

### 问题 3: 策略无信号

```bash
# 检查策略参数是否过严
cat config/config.json | jq '.kline_strategy.buy'

# 临时放宽参数测试
python3 -c "
import json
with open('config/config.json', 'r') as f:
    config = json.load(f)
config['kline_strategy']['buy']['volume_ratio_min'] = 1.2
with open('config/config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('参数已放宽')
"
```

## 版本历史

### v2.0 (2026-03-07) - K 线增强版

**核心改进**:
- ✅ 买入增加 K 线过滤 (5 日线、量比、换手率、上影线)
- ✅ 卖出增加 K 线判断 (破位、放量滞涨、顶部背离)
- ✅ 持仓实时监控 (每 5 分钟扫描)
- ✅ 信心评分提升 (有 K 线确认的信号更高)

**预期效果**:
- 胜率：55% → 65%
- 平均盈利：8% → 12%
- 最大回撤：15% → 8%

### v1.0 (2026-03-05) - 基础版

- 基础策略框架
- 涨停板数据获取
- 情绪周期计算
- 模拟盘执行

## 注意事项

1. **休市时间**: 非交易时间无实时 K 线数据
2. **网络依赖**: 需要访问新浪财经和 akshare API
3. **模拟盘**: 当前为模拟交易，非实盘
4. **参数调优**: 根据实战结果调整策略参数
5. **日志检查**: 每日查看日志，发现问题及时调整

## 相关文档

- `/root/.openclaw/workspace/quant-trading/STRATEGY_AND_DATA.md` - 策略与数据源详解
- `/root/.openclaw/workspace/quant-trading/STRATEGY_OPTIMIZATION_20260307.md` - v2.0 优化日志
- `/root/.openclaw/workspace/quant-trading/docs/OPTIMIZATION_SUMMARY_20260307.md` - 优化总结报告
- `/root/.openclaw/workspace/quant-trading/AUTO_RUN_STATUS.md` - 自动运行状态

---

**Skill 版本**: v2.0  
**最后更新**: 2026-03-07  
**维护者**: 量化助手
