# K 线数据分析方法

**更新日期**: 2026-03-06  
**数据源**: 新浪财经 API

---

## 📊 一、K 线数据获取

### API 接口

```
http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| symbol | 股票代码 (sh/sz 前缀) | sh600519, sz000001 |
| scale | K 线周期 | 240=日线，241=周线 |
| ma | 均线 | no=不返回均线 |
| datalen | 数据条数 | 最多 100 条 |

### 返回数据

```json
[
  {
    "day": "2026-03-06",
    "open": "10.50",
    "high": "11.20",
    "low": "10.30",
    "close": "11.00",
    "volume": "12345678"
  }
]
```

### Python 调用

```python
import requests

def get_kline(symbol, count=100):
    # 格式化代码
    if symbol.startswith('6'):
        code = f"sh{symbol}"
    else:
        code = f"sz{symbol}"
    
    params = {
        'symbol': code,
        'scale': 240,  # 日线
        'ma': 'no',
        'datalen': count
    }
    
    resp = requests.get(base_url, params=params)
    data = resp.json()
    
    # 转 DataFrame
    df = pd.DataFrame(data)
    df = df.rename(columns={
        'day': '日期',
        'open': '开盘',
        'high': '最高',
        'low': '最低',
        'close': '收盘',
        'volume': '成交量'
    })
    
    return df
```

---

## 📈 二、K 线核心分析方法

### 1. 价格形态分析

#### (1) 回调幅度计算

```python
def calculate_pullback(kline):
    """
    计算从高点回调的幅度
    用于龙头回调策略
    """
    current_price = kline.iloc[-1]['收盘']
    recent_high = kline['最高'].max()
    
    pullback_pct = (recent_high - current_price) / recent_high * 100
    
    return pullback_pct, recent_high

# 应用
pullback, high = calculate_pullback(df.tail(20))
if 5 <= pullback <= 10:
    print(f"回调{pullback:.1f}%, 符合买入条件")
```

**用途**:
- 龙头回调策略入场点
- 支撑位判断
- 超卖识别

---

#### (2) 突破识别

```python
def check_breakout(kline, lookback=20):
    """
    识别平台突破
    """
    current_high = kline.iloc[-1]['最高']
    current_close = kline.iloc[-1]['收盘']
    
    # 前 N 日的最高价 (平台压力)
    platform_high = kline.iloc[-lookback:-1]['最高'].max()
    
    # 是否突破
    is_breakout = current_high > platform_high
    
    # 突破幅度
    breakout_pct = (current_close - platform_high) / platform_high * 100
    
    return is_breakout, breakout_pct, platform_high

# 应用
is_break, pct, pressure = check_breakout(df.tail(30))
if is_break and pct > 3:
    print(f"有效突破！压力位：{pressure}, 突破幅度：{pct:.2f}%")
```

**用途**:
- 突破策略入场
- 压力位/支撑位识别
- 新高判断

---

#### (3) K 线组合形态

```python
def analyze_kline_pattern(kline):
    """
    识别经典 K 线形态
    """
    last = kline.iloc[-1]
    prev = kline.iloc[-2]
    
    # 计算实体和影线
    body = abs(last['收盘'] - last['开盘'])
    upper_shadow = last['最高'] - max(last['收盘'], last['开盘'])
    lower_shadow = min(last['收盘'], last['开盘']) - last['最低']
    range_total = last['最高'] - last['最低']
    
    patterns = []
    
    # 大阳线
    if last['收盘'] > last['开盘'] and body > range_total * 0.7:
        patterns.append("大阳线")
    
    # 大阴线
    if last['收盘'] < last['开盘'] and body > range_total * 0.7:
        patterns.append("大阴线")
    
    # 十字星
    if body < range_total * 0.1:
        patterns.append("十字星")
    
    # 锤头线 (下影线长)
    if lower_shadow > body * 2 and upper_shadow < body:
        patterns.append("锤头线 (看涨)")
    
    # 吊颈线 (高位长上影)
    if upper_shadow > body * 2 and lower_shadow < body:
        patterns.append("吊颈线 (看跌)")
    
    # 阳包阴
    if (prev['收盘'] < prev['开盘'] and 
        last['收盘'] > last['开盘'] and
        last['收盘'] > prev['开盘'] and
        last['开盘'] < prev['收盘']):
        patterns.append("阳包阴 (看涨)")
    
    # 阴包阳
    if (prev['收盘'] > prev['开盘'] and 
        last['收盘'] < last['开盘'] and
        last['收盘'] < prev['开盘'] and
        last['开盘'] > prev['收盘']):
        patterns.append("阴包阳 (看跌)")
    
    return patterns

# 应用
patterns = analyze_kline_pattern(df.tail(2))
if patterns:
    print(f"K 线形态：{', '.join(patterns)}")
```

**常见形态含义**:

| 形态 | 含义 | 信号强度 |
|------|------|----------|
| 大阳线 | 强势上涨 | ⭐⭐⭐ |
| 大阴线 | 强势下跌 | ⭐⭐⭐ |
| 十字星 | 多空平衡/变盘 | ⭐⭐ |
| 锤头线 | 底部反转 | ⭐⭐⭐ |
| 吊颈线 | 顶部反转 | ⭐⭐⭐ |
| 阳包阴 | 看涨反转 | ⭐⭐⭐⭐ |
| 阴包阳 | 看跌反转 | ⭐⭐⭐⭐ |

---

### 2. 成交量分析

#### (1) 量比计算

```python
def calculate_volume_ratio(kline, window=5):
    """
    计算量比 (今日成交量 / 过去 N 日平均)
    """
    current_vol = kline.iloc[-1]['成交量']
    avg_vol = kline.iloc[-window-1:-1]['成交量'].mean()
    
    volume_ratio = current_vol / avg_vol if avg_vol > 0 else 1
    
    return volume_ratio

# 应用
vol_ratio = calculate_volume_ratio(df.tail(10))
if vol_ratio > 2:
    print(f"成交量放大{vol_ratio:.2f}倍，放量！")
elif vol_ratio < 0.5:
    print(f"成交量萎缩{vol_ratio:.2f}倍，缩量！")
```

**量比含义**:

| 量比 | 含义 | 操作 |
|------|------|------|
| > 3 | 极度放量 | 警惕反转 |
| 2-3 | 明显放量 | 突破确认 |
| 1.5-2 | 温和放量 | 健康上涨 |
| 0.8-1.2 | 正常 | 观望 |
| 0.5-0.8 | 缩量 | 回调正常 |
| < 0.5 | 极度缩量 | 变盘信号 |

---

#### (2) 量价关系分析

```python
def analyze_volume_price(kline):
    """
    分析量价关系
    """
    last = kline.iloc[-1]
    prev = kline.iloc[-2]
    
    price_up = last['收盘'] > prev['收盘']
    vol_up = last['成交量'] > prev['成交量']
    
    if price_up and vol_up:
        return "量增价涨 (健康)"
    elif price_up and not vol_up:
        return "量缩价涨 (背离，警惕)"
    elif not price_up and vol_up:
        return "放量下跌 (危险)"
    else:
        return "缩量回调 (正常)"

# 应用
relation = analyze_volume_price(df.tail(2))
print(f"量价关系：{relation}")
```

**量价关系口诀**:
- 量增价涨 → 健康上涨，继续持有
- 量缩价涨 → 背离信号，警惕回调
- 放量下跌 → 主力出货，果断止损
- 缩量回调 → 正常调整，可逢低买入

---

### 3. 均线系统分析

#### (1) 均线计算

```python
def calculate_ma(kline, periods=[5, 10, 20, 60]):
    """
    计算多条均线
    """
    df = kline.copy()
    
    for period in periods:
        df[f'MA{period}'] = df['收盘'].rolling(window=period).mean()
    
    return df

# 应用
df_ma = calculate_ma(df.tail(60))
print(df_ma[['日期', '收盘', 'MA5', 'MA10', 'MA20', 'MA60']].tail())
```

#### (2) 均线排列分析

```python
def analyze_ma_arrangement(kline):
    """
    分析均线排列 (多头/空头)
    """
    df = calculate_ma(kline.tail(60))
    
    last = df.iloc[-1]
    
    # 多头排列：MA5 > MA10 > MA20 > MA60
    bullish = (last['MA5'] > last['MA10'] > last['MA20'] > last['MA60'])
    
    # 空头排列：MA5 < MA10 < MA20 < MA60
    bearish = (last['MA5'] < last['MA10'] < last['MA20'] < last['MA60'])
    
    # 金叉：MA5 上穿 MA10
    golden_cross = (df.iloc[-2]['MA5'] <= df.iloc[-2]['MA10'] and 
                    last['MA5'] > last['MA10'])
    
    # 死叉：MA5 下穿 MA10
    death_cross = (df.iloc[-2]['MA5'] >= df.iloc[-2]['MA10'] and 
                   last['MA5'] < last['MA10'])
    
    signals = []
    if bullish:
        signals.append("多头排列 (强势)")
    if bearish:
        signals.append("空头排列 (弱势)")
    if golden_cross:
        signals.append("金叉 (买入信号)")
    if death_cross:
        signals.append("死叉 (卖出信号)")
    
    return signals

# 应用
ma_signals = analyze_ma_arrangement(df)
print(f"均线信号：{', '.join(ma_signals)}")
```

---

### 4. 支撑位与压力位

```python
def find_support_resistance(kline, window=20):
    """
    识别支撑位和压力位
    """
    recent = kline.tail(window)
    
    # 压力位：近期高点
    resistance = recent['最高'].max()
    
    # 支撑位：近期低点
    support = recent['最低'].min()
    
    # 中间位
    current = recent.iloc[-1]['收盘']
    
    # 距离压力/支撑的幅度
    to_resistance = (resistance - current) / current * 100
    to_support = (current - support) / current * 100
    
    return {
        '压力位': resistance,
        '支撑位': support,
        '距压力%': to_resistance,
        '距支撑%': to_support
    }

# 应用
levels = find_support_resistance(df.tail(30))
print(f"压力位：{levels['压力位']:.2f} (+{levels['距压力%']:.2f}%)")
print(f"支撑位：{levels['支撑位']:.2f} (-{levels['距支撑%']:.2f}%)")
```

---

### 5. 技术指标计算

#### (1) RSI (相对强弱指标)

```python
def calculate_rsi(kline, period=14):
    """
    计算 RSI
    """
    delta = kline['收盘'].diff()
    
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.iloc[-1]

# 应用
rsi = calculate_rsi(df.tail(30))
if rsi > 70:
    print(f"RSI={rsi:.2f}, 超买区，警惕回调")
elif rsi < 30:
    print(f"RSI={rsi:.2f}, 超卖区，可能反弹")
else:
    print(f"RSI={rsi:.2f}, 中性区域")
```

**RSI 含义**:

| RSI 值 | 状态 | 操作 |
|--------|------|------|
| > 80 | 严重超买 | 减仓/卖出 |
| 70-80 | 超买 | 谨慎 |
| 30-70 | 中性 | 持有/观望 |
| 20-30 | 超卖 | 关注 |
| < 20 | 严重超卖 | 买入机会 |

---

#### (2) MACD (平滑异同移动平均线)

```python
def calculate_macd(kline, fast=12, slow=26, signal=9):
    """
    计算 MACD
    """
    exp1 = kline['收盘'].ewm(span=fast, adjust=False).mean()
    exp2 = kline['收盘'].ewm(span=slow, adjust=False).mean()
    
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    
    return {
        'MACD': macd_line.iloc[-1],
        'Signal': signal_line.iloc[-1],
        'Histogram': histogram.iloc[-1]
    }

# 应用
macd = calculate_macd(df.tail(60))
print(f"MACD: {macd['MACD']:.4f}")
print(f"Signal: {macd['Signal']:.4f}")
print(f"Histogram: {macd['Histogram']:.4f}")

if macd['MACD'] > macd['Signal'] and macd['Histogram'] > 0:
    print("MACD 金叉，看涨信号")
elif macd['MACD'] < macd['Signal'] and macd['Histogram'] < 0:
    print("MACD 死叉，看跌信号")
```

---

## 🎯 三、K 线分析在策略中的应用

### 策略 1: 龙头回调

```python
def check_leader_pullback(kline):
    """
    龙头回调策略的 K 线分析
    """
    # 1. 计算回调幅度
    current = kline.iloc[-1]['收盘']
    high = kline.tail(20)['最高'].max()
    pullback = (high - current) / high * 100
    
    # 2. 检查是否在 5-10% 区间
    if not (5 <= pullback <= 10):
        return None, "回调幅度不符合"
    
    # 3. 检查成交量是否缩量
    vol_ratio = calculate_volume_ratio(kline.tail(10))
    if vol_ratio > 0.8:
        return None, "成交量未明显缩量"
    
    # 4. 检查是否企稳 (出现下影线或小阳线)
    last = kline.iloc[-1]
    body = abs(last['收盘'] - last['开盘'])
    lower_shadow = min(last['收盘'], last['开盘']) - last['最低']
    
    if lower_shadow > body or last['收盘'] > last['开盘']:
        return {
            'signal': 'buy',
            'reason': f'回调{pullback:.1f}%, 缩量{vol_ratio:.2f}倍，企稳信号',
            'confidence': 0.7
        }
    
    return None, "未出现企稳信号"
```

---

### 策略 2: 突破策略

```python
def check_breakout(kline):
    """
    突破策略的 K 线分析
    """
    # 1. 识别平台压力位
    platform_high = kline.tail(30).iloc[:-1]['最高'].max()
    current_high = kline.iloc[-1]['最高']
    current_close = kline.iloc[-1]['收盘']
    
    # 2. 检查是否突破
    if current_high <= platform_high:
        return None, "未突破平台"
    
    # 3. 检查突破幅度 (要求>3%)
    breakout_pct = (current_close - platform_high) / platform_high * 100
    if breakout_pct < 3:
        return None, "突破幅度不足"
    
    # 4. 检查成交量
    vol_ratio = calculate_volume_ratio(kline.tail(15))
    if vol_ratio < 1.5:
        return None, "成交量未放大"
    
    # 5. 检查 K 线形态 (大阳线更佳)
    last = kline.iloc[-1]
    body = abs(last['收盘'] - last['开盘'])
    range_total = last['最高'] - last['最低']
    
    is_big_yang = (last['收盘'] > last['开盘'] and body > range_total * 0.6)
    
    confidence = 0.8 if is_big_yang else 0.6
    
    return {
        'signal': 'buy',
        'reason': f'突破平台 (+{breakout_pct:.2f}%), 放量{vol_ratio:.2f}倍',
        'confidence': confidence
    }
```

---

## 📊 四、完整 K 线分析报告模板

```python
def generate_kline_report(symbol, kline):
    """
    生成完整的 K 线分析报告
    """
    report = f"# {symbol} K 线分析报告\n\n"
    report += f"**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
    
    # 1. 基本数据
    last = kline.iloc[-1]
    report += "## 📊 基本数据\n"
    report += f"- 最新价：{last['收盘']:.2f}\n"
    report += f"- 涨跌幅：{(last['收盘']-last['开盘'])/last['开盘']*100:.2f}%\n"
    report += f"- 成交量：{last['成交量']:,}\n"
    report += f"- 振幅：{(last['最高']-last['最低'])/last['开盘']*100:.2f}%\n\n"
    
    # 2. 趋势分析
    report += "## 📈 趋势分析\n"
    pullback, high = calculate_pullback(kline.tail(20))
    report += f"- 距 20 日高点回调：{pullback:.2f}%\n"
    
    ma_signals = analyze_ma_arrangement(kline)
    report += f"- 均线信号：{', '.join(ma_signals)}\n\n"
    
    # 3. 量价分析
    report += "## 💰 量价分析\n"
    vol_ratio = calculate_volume_ratio(kline.tail(10))
    report += f"- 量比：{vol_ratio:.2f}\n"
    report += f"- 量价关系：{analyze_volume_price(kline.tail(2))}\n\n"
    
    # 4. 支撑压力
    report += "## 🎯 支撑与压力\n"
    levels = find_support_resistance(kline.tail(30))
    report += f"- 压力位：{levels['压力位']:.2f} (+{levels['距压力%']:.2f}%)\n"
    report += f"- 支撑位：{levels['支撑位']:.2f} (-{levels['距支撑%']:.2f}%)\n\n"
    
    # 5. 技术指标
    report += "## 📉 技术指标\n"
    rsi = calculate_rsi(kline.tail(30))
    report += f"- RSI(14): {rsi:.2f}\n"
    
    macd = calculate_macd(kline.tail(60))
    report += f"- MACD: {macd['MACD']:.4f}\n"
    report += f"- Signal: {macd['Signal']:.4f}\n"
    report += f"- Histogram: {macd['Histogram']:.4f}\n\n"
    
    # 6. 操作建议
    report += "## 💡 操作建议\n"
    if pullback > 10:
        report += "- ⚠️ 回调过深，谨慎抄底\n"
    elif 5 <= pullback <= 10 and vol_ratio < 0.7:
        report += "- ✅ 龙头回调机会，可逢低买入\n"
    elif rsi > 70:
        report += "- ⚠️ 超买区，警惕回调\n"
    elif rsi < 30:
        report += "- ✅ 超卖区，关注反弹机会\n"
    else:
        report += "- ⏸️ 观望为主\n"
    
    return report
```

---

## ⚠️ 五、注意事项

### 1. 数据质量

- ✅ 使用前检查数据完整性
- ✅ 处理停牌、除权除息
- ✅ 注意数据延迟 (日线 T+1)

### 2. 分析局限性

- ⚠️ K 线分析是技术分析，不是基本面
- ⚠️ 需要结合成交量、市场情绪
- ⚠️ 单一指标可靠性有限

### 3. 最佳实践

- ✅ 多指标共振 (K 线 + 均线 + 成交量)
- ✅ 结合市场情绪 (涨停/跌停比)
- ✅ 严格止损 (技术位破位即止损)
- ✅ 回测验证 (历史数据测试)

---

## 🚀 六、代码示例

### 完整分析流程

```python
from data_fetcher_sina import SinaKLineFetcher

# 1. 获取 K 线
fetcher = SinaKLineFetcher()
kline = fetcher.get_daily_kline('000001', count=60)

# 2. 生成报告
report = generate_kline_report('000001', kline)
print(report)

# 3. 策略检查
pullback_signal, reason = check_leader_pullback(kline)
if pullback_signal:
    print(f"✅ 龙头回调信号：{reason}")
else:
    print(f"⏸️ 无信号：{reason}")

breakout_signal = check_breakout(kline)
if breakout_signal:
    print(f"✅ 突破信号：{breakout_signal['reason']}")
```

---

**K 线分析是短线交易的核心技能，需要持续学习和实践！** 📊
