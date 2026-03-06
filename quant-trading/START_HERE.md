# 🚀 量化交易系统 - 从这里开始

**老板，系统已就绪！** 📊

---

## ✅ 当前状态

### 已完成功能

| 模块 | 状态 | 说明 |
|------|------|------|
| **实时 K 线** | ✅ 完成 | 新浪财经 API |
| **盘中策略** | ✅ 完成 | 早盘/盘中/尾盘 |
| **自建模拟盘** | ✅ 完成 | 本地记录 |
| **聚宽集成** | ✅ 完成 | API 已就绪 |
| **自动交易** | ✅ 完成 | 可立即运行 |
| **风控系统** | ✅ 完成 | 止损止盈 |

---

## 🎯 立即开始 (3 步)

### 步骤 1: 测试系统

```bash
cd /root/.openclaw/workspace/quant-trading
python auto_trading.py --test
```

**预期输出**:
```
✅ 自动交易系统初始化完成
✅ 加载监控列表：7 只股票
✅ 扫描完成，生成 0 个信号 (休市时间)
```

---

### 步骤 2: 设置监控列表

**编辑** `auto_trading.py` (第 195 行左右):

```python
watch_list = [
    '000533',  # 顺钠股份
    '605268',  # 王力安防
    '600545',  # 卓郎智能
    '002498',  # 汉缆股份
    '600590',  # 泰豪科技
    '000001',  # 平安银行
    '000002',  # 万科 A
]
```

**修改为您想监控的股票**。

---

### 步骤 3: 启动交易

**交易时间运行** (工作日 09:30-15:00):

```bash
# 方式 1: 手动启动
python auto_trading.py --interval 300

# 方式 2: 后台运行
nohup python auto_trading.py --interval 300 > logs/auto_trading.log 2>&1 &

# 方式 3: 使用启动脚本
bash scripts/start_monitor.sh
```

---

## 📊 使用聚宽 (推荐)

### 1. 注册聚宽账号

**访问**: https://www.joinquant.com/

**步骤**:
1. 注册账号 (手机号)
2. 实名认证 (10 分钟)
3. 开通量化交易
4. 获取 API 凭证

---

### 2. 安装 SDK

```bash
pip install jqdatasdk
```

---

### 3. 测试连接

```bash
python joinquant_integration.py
```

**输入**:
```
用户名 (手机号): 138****1234
密码：********
```

---

### 4. 配置凭证

```bash
mkdir -p config
nano config/joinquant_config.txt
```

**内容**:
```
username=138****1234
password=your_password
```

---

### 5. 启动聚宽交易

```bash
python auto_trading.py --joinquant --interval 300
```

---

## ⏰ 定时任务 (推荐)

### 设置自动运行

```bash
crontab -e
```

**添加**:
```bash
# 09:25 集合竞价后
25 9 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python auto_trading.py --once >> logs/daily_$(date+\%Y\%m\%d).log 2>&1

# 10:00 早盘
0 10 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python auto_trading.py --once >> logs/daily_$(date+\%Y\%m\%d).log 2>&1

# 14:30 尾盘
30 14 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python auto_trading.py --once >> logs/daily_$(date+\%Y\%m\%d).log 2>&1

# 15:30 收盘报告
30 15 * * 1-5 cd /root/.openclaw/workspace/quant-trading && python -c "from paper_trading import PaperTrading; p = PaperTrading(); p.print_report()" >> logs/daily_$(date+\%Y\%m\%d).log 2>&1
```

---

## 📁 重要文件

```
quant-trading/
├── auto_trading.py              # ⭐ 主程序
├── joinquant_integration.py     # ⭐ 聚宽 API
├── START_HERE.md                # ⭐ 本文档
├── docs/
│   ├── 模拟盘设置指南.md         # 详细指南
│   ├── 盘中实时监控设置.md
│   └── 系统升级总结.md
├── logs/
│   └── auto_trading.log         # 交易日志
└── config/
    └── joinquant_config.txt     # 聚宽凭证 (需创建)
```

---

## 🎯 下周一实战流程

### 08:30 准备
```bash
# 检查系统
cd quant-trading
python auto_trading.py --test
```

### 09:15 启动
```bash
# 启动监控
python auto_trading.py --interval 300
```

### 09:30-15:00 自动交易
- 系统自动扫描
- 发现信号自动买入
- 收盘自动生成报告

### 15:30 收盘
```bash
# 查看报告
cat logs/auto_trading.log
```

### 20:00 复盘
```bash
# 深度复盘
python main.py --review
```

---

## 📞 快速命令

```bash
# 测试系统
python auto_trading.py --test

# 运行一次
python auto_trading.py --once

# 连续监控
python auto_trading.py --interval 300

# 后台运行
nohup python auto_trading.py --interval 300 > logs/auto_trading.log 2>&1 &

# 查看日志
tail -f logs/auto_trading.log

# 查看模拟盘
python -c "from paper_trading import PaperTrading; p = PaperTrading(); p.print_report()"

# 测试聚宽
python joinquant_integration.py
```

---

## ⚠️ 注意事项

### 1. 交易时间
- ✅ 工作日：09:30-11:30, 13:00-15:00
- ❌ 周末/节假日：休市

### 2. 风险控制
- 单笔仓位≤10%
- 单日交易≤5 笔
- 止损 -5%
- 止盈 +15%

### 3. 网络要求
- 稳定网络连接
- 建议有线网络

### 4. 数据备份
```bash
# 每周备份
cp -r data/paper/ backup/paper_$(date +%Y%m%d)/
```

---

## 💡 策略说明

### 早盘突破 (09:30-10:30)
- 高开 2-5%
- 量比>1.5
- 止损 -5%, 止盈 +15%

### 盘中回调 (10:30-14:30)
- 回调 3-5%
- 缩量
- 止损 -5%, 止盈 +10%

### 尾盘买入 (14:30-15:00)
- 涨幅 3-7%
- 尾盘稳定
- 止损 -5%, 止盈 +10%

---

## 🎉 开始交易！

**老板，一切就绪！**

**下周一 09:15**，运行:
```bash
python auto_trading.py --interval 300
```

**祝交易顺利！** 📈

---

**有问题随时找我！**
