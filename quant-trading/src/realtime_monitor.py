#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中实时监控系统
实时监控 K 线、资金流、生成交易信号

优势:
- 捕捉盘中最佳买点
- 避免收盘后滞后
- 适合 T+1 交易制度
"""

import requests
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class RealtimeKLineFetcher:
    """实时 K 线获取器"""
    
    def __init__(self):
        # 新浪财经实时 K 线 API
        self.kline_url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
        # 新浪财经实时行情 API
        self.quote_url = "http://hq.sinajs.cn/list="
    
    def get_realtime_kline(self, symbol: str, count=60, scale='60') -> pd.DataFrame:
        """
        获取实时 K 线
        
        Args:
            symbol: 股票代码 (如 000533)
            count: 获取条数 (最多 100)
            scale: K 线周期
                   1=1 分钟，5=5 分钟，15=15 分钟，30=30 分钟
                   60=60 分钟 (1 小时), 240=日线，241=周线
        
        Returns:
            DataFrame with 日期，开盘，最高，最低，收盘，成交量
        """
        # 格式化股票代码
        if symbol.startswith('6'):
            stock_code = f"sh{symbol}"
        else:
            stock_code = f"sz{symbol}"
        
        params = {
            'symbol': stock_code,
            'scale': scale,
            'ma': 'no',
            'datalen': min(count, 100)
        }
        
        try:
            resp = requests.get(self.kline_url, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                
                if data and len(data) > 0:
                    df = pd.DataFrame(data)
                    df = df.rename(columns={
                        'day': '日期',
                        'open': '开盘',
                        'high': '最高',
                        'low': '最低',
                        'close': '收盘',
                        'volume': '成交量'
                    })
                    
                    # 转换数据类型
                    df['日期'] = pd.to_datetime(df['日期'])
                    numeric_cols = ['开盘', '最高', '最低', '收盘', '成交量']
                    for col in numeric_cols:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    return df
            return None
        except Exception as e:
            logger.error(f"获取 K 线失败 ({symbol}): {e}")
            return None
    
    def get_realtime_quote(self, symbol: str) -> Dict:
        """
        获取实时行情 (每秒更新)
        
        Returns:
            {
                'code': '000533',
                'name': '顺钠股份',
                'price': 14.88,
                'open': 14.50,
                'high': 15.20,
                'low': 14.30,
                'volume': 123456,
                'amount': 1234567890,
                'bid': [买 1 价，买 2 价，...],
                'ask': [卖 1 价，卖 2 价，...],
                'time': '2026-03-06 10:30:00'
            }
        """
        if symbol.startswith('6'):
            stock_code = f"sh{symbol}"
        else:
            stock_code = f"sz{symbol}"
        
        try:
            resp = requests.get(f"{self.quote_url}{stock_code}", timeout=5)
            if resp.status_code == 200:
                # 解析结果：var hq_str_sh000001="..."
                content = resp.text
                if '=' in content:
                    quote_str = content.split('=')[1].strip('"').strip('"')
                    parts = quote_str.split(',')
                    
                    if len(parts) >= 32:
                        return {
                            'code': symbol,
                            'name': parts[0],
                            'price': float(parts[3]),  # 当前价
                            'open': float(parts[1]),   # 开盘
                            'high': float(parts[4]),   # 最高
                            'low': float(parts[5]),    # 最低
                            'volume': int(parts[8]),   # 成交量 (手)
                            'amount': float(parts[9]), # 成交额 (元)
                            'bid': [float(parts[11]), float(parts[13]), float(parts[15]), float(parts[17]), float(parts[19])],
                            'ask': [float(parts[21]), float(parts[23]), float(parts[25]), float(parts[27]), float(parts[29])],
                            'time': f"{parts[31]} {parts[32]}" if len(parts) > 32 else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
            return None
        except Exception as e:
            logger.error(f"获取行情失败 ({symbol}): {e}")
            return None
    
    def get_batch_quotes(self, symbols: List[str]) -> Dict[str, Dict]:
        """批量获取实时行情"""
        results = {}
        
        # 最多一次 800 只股票
        batch_size = 800
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            
            # 构建代码列表
            codes = []
            for symbol in batch:
                if symbol.startswith('6'):
                    codes.append(f"sh{symbol}")
                else:
                    codes.append(f"sz{symbol}")
            
            code_str = ','.join(codes)
            
            try:
                resp = requests.get(f"{self.quote_url}{code_str}", timeout=10)
                if resp.status_code == 200:
                    lines = resp.text.strip().split('\n')
                    for line in lines:
                        if '=' in line:
                            code = line.split('=')[0].split('_')[-1]
                            symbol = code[2:]  # 去掉 sh/sz
                            quote_str = line.split('=')[1].strip('"').strip('"')
                            parts = quote_str.split(',')
                            
                            if len(parts) >= 8 and parts[3]:
                                results[symbol] = {
                                    'code': symbol,
                                    'name': parts[0],
                                    'price': float(parts[3]) if parts[3] else 0,
                                    'change_pct': float(parts[2]) if parts[2] else 0,
                                    'volume': int(parts[8]) if parts[8] else 0,
                                    'amount': float(parts[9]) if parts[9] else 0,
                                }
            except Exception as e:
                logger.error(f"批量获取行情失败：{e}")
            
            time.sleep(0.5)
        
        return results


class RealtimeMonitor:
    """盘中实时监控"""
    
    def __init__(self, watch_list: List[str] = None):
        self.fetcher = RealtimeKLineFetcher()
        self.watch_list = watch_list or []
        self.signals = []
        self.last_update = None
    
    def add_stock(self, symbol: str):
        """添加监控股票"""
        if symbol not in self.watch_list:
            self.watch_list.append(symbol)
            logger.info(f"添加监控：{symbol}")
    
    def remove_stock(self, symbol: str):
        """移除监控股票"""
        if symbol in self.watch_list:
            self.watch_list.remove(symbol)
            logger.info(f"移除监控：{symbol}")
    
    def check_breakout(self, kline: pd.DataFrame, current_price: float) -> bool:
        """
        检查是否突破
        
        条件:
        - 突破 20 日高点
        - 成交量放大
        """
        if kline is None or len(kline) < 20:
            return False
        
        # 20 日高点
        platform_high = kline.iloc[:-1]['最高'].max()
        
        # 是否突破
        is_breakout = current_price > platform_high
        
        # 突破幅度
        breakout_pct = (current_price - platform_high) / platform_high * 100 if platform_high > 0 else 0
        
        return is_breakout and breakout_pct > 2  # 突破超过 2%
    
    def check_pullback(self, kline: pd.DataFrame, current_price: float) -> Optional[float]:
        """
        检查回调是否到位
        
        条件:
        - 从高点回调 5-10%
        - 缩量
        
        Returns:
            回调幅度 (%) 或 None
        """
        if kline is None or len(kline) < 10:
            return None
        
        # 近期高点
        recent_high = kline['最高'].max()
        
        # 回调幅度
        pullback = (recent_high - current_price) / recent_high * 100
        
        # 检查是否在 5-10% 区间
        if 5 <= pullback <= 10:
            return pullback
        
        return None
    
    def check_volume_surge(self, kline: pd.DataFrame, current_volume: int) -> bool:
        """
        检查成交量是否突然放大
        
        条件:
        - 当前成交量 > 过去 5 日均量 2 倍
        """
        if kline is None or len(kline) < 5:
            return False
        
        avg_volume = kline.iloc[-5:]['成交量'].mean()
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
        
        return volume_ratio > 2
    
    def scan(self) -> List[Dict]:
        """
        扫描所有监控股票，生成信号
        
        Returns:
            信号列表
        """
        self.signals = []
        logger.info(f"开始扫描 {len(self.watch_list)} 只股票...")
        
        for symbol in self.watch_list:
            # 获取实时行情
            quote = self.fetcher.get_realtime_quote(symbol)
            if not quote:
                continue
            
            current_price = quote['price']
            
            # 获取 K 线
            kline = self.fetcher.get_realtime_kline(symbol, count=60)
            
            # 检查突破
            if self.check_breakout(kline, current_price):
                signal = {
                    'symbol': symbol,
                    'name': quote['name'],
                    'action': 'buy',
                    'type': '突破',
                    'price': current_price,
                    'reason': f'突破平台，现价{current_price:.2f}元',
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'confidence': 0.7
                }
                self.signals.append(signal)
                logger.info(f"✅ {symbol} 突破信号！")
            
            # 检查回调
            pullback = self.check_pullback(kline, current_price)
            if pullback:
                signal = {
                    'symbol': symbol,
                    'name': quote['name'],
                    'action': 'buy',
                    'type': '回调',
                    'price': current_price,
                    'reason': f'回调{pullback:.1f}%, 现价{current_price:.2f}元',
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'confidence': 0.6
                }
                self.signals.append(signal)
                logger.info(f"✅ {symbol} 回调信号！")
            
            # 检查放量
            if self.check_volume_surge(kline, quote['volume']):
                signal = {
                    'symbol': symbol,
                    'name': quote['name'],
                    'action': 'watch',
                    'type': '放量',
                    'price': current_price,
                    'reason': f'成交量放大，现量{quote["volume"]}手',
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'confidence': 0.5
                }
                self.signals.append(signal)
                logger.info(f"👀 {symbol} 放量信号！")
        
        self.last_update = datetime.now()
        logger.info(f"扫描完成，生成 {len(self.signals)} 个信号")
        return self.signals
    
    def continuous_monitor(self, interval=300):
        """
        持续监控
        
        Args:
            interval: 扫描间隔 (秒), 默认 5 分钟
        """
        logger.info(f"开始持续监控，扫描间隔：{interval}秒")
        
        while self.is_market_open():
            self.scan()
            
            # 等待下次扫描
            time.sleep(interval)
        
        logger.info("市场已关闭，停止监控")
    
    def is_market_open(self) -> bool:
        """检查是否在交易时间"""
        now = datetime.now()
        
        # 检查是否工作日
        if now.weekday() >= 5:  # 周末
            return False
        
        # 检查时间
        hour = now.hour
        minute = now.minute
        
        # 上午 9:30-11:30
        if hour == 9 and minute >= 30:
            return True
        if hour == 10:
            return True
        if hour == 11 and minute <= 30:
            return True
        
        # 下午 13:00-15:00
        if hour == 13 or hour == 14:
            return True
        if hour == 15 and minute <= 0:
            return True
        
        return False
    
    def get_market_session(self) -> str:
        """获取当前交易时段"""
        if not self.is_market_open():
            return "休市"
        
        now = datetime.now()
        hour = now.hour
        
        if hour < 11:
            return "早盘"
        elif hour < 13:
            return "午间"
        elif hour < 15:
            return "午盘"
        else:
            return "收盘"


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("盘中实时监控系统测试")
    print("=" * 60)
    
    # 创建监控器
    monitor = RealtimeMonitor(watch_list=['000533', '605268', '000001'])
    
    # 测试实时行情
    print("\n【1】测试实时行情")
    for symbol in monitor.watch_list:
        quote = monitor.fetcher.get_realtime_quote(symbol)
        if quote:
            print(f"  {symbol} {quote['name']}: {quote['price']}元")
        else:
            print(f"  {symbol}: 获取失败")
    
    # 测试 K 线
    print("\n【2】测试 K 线数据")
    for symbol in monitor.watch_list:
        kline = monitor.fetcher.get_realtime_kline(symbol, count=30)
        if kline is not None:
            print(f"  {symbol}: {len(kline)}条")
            print(f"    最新：{kline.iloc[-1]['收盘']}元")
        else:
            print(f"  {symbol}: 获取失败")
    
    # 测试扫描
    print("\n【3】测试信号扫描")
    signals = monitor.scan()
    if signals:
        print(f"  生成 {len(signals)} 个信号:")
        for sig in signals:
            print(f"    {sig['symbol']} {sig['type']} {sig['reason']}")
    else:
        print("  无信号")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
