#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中实时策略 v2.0 - K 线增强版
基于实时 K 线和行情生成交易信号

优化日期：2026-03-07
优化内容:
- 增加 K 线买入过滤 (5 日线、量比、换手率)
- 增加 K 线卖出判断 (破位、放量滞涨、顶部背离)
- 持仓实时监控 (每 5 分钟扫描)
"""

import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

from realtime_monitor import RealtimeMonitor, RealtimeKLineFetcher

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class IntradaySignal:
    """盘中交易信号"""
    symbol: str
    name: str
    action: str  # buy/sell/watch
    strategy: str  # 突破/回调/放量/...
    price: float
    quantity: int
    reason: str
    timestamp: datetime
    confidence: float
    stop_loss: float
    take_profit: float
    market_session: str  # 早盘/午盘


class IntradayStrategy:
    """盘中实时策略引擎 v2.0 - K 线增强版"""
    
    def __init__(self, capital=100000):
        self.capital = capital
        self.monitor = RealtimeMonitor()
        self.fetcher = RealtimeKLineFetcher()
        self.signals = []
        self.positions = {}  # 持仓
        
        # K 线策略参数
        self.kline_params = {
            'buy': {
                'ma5_up': True,           # 5 日线向上
                'volume_ratio_min': 1.5,  # 最小量比
                'turnover_rate_min': 10,  # 最小换手率%
                'upper_shadow_max': 3     # 最大上影线%
            },
            'sell': {
                'stop_loss_ma5': True,        # 跌破 5 日线止损
                'stop_loss_change_pct': -5,   # 当日跌幅止损
                'stop_loss_volume_down': True,# 放量下跌止损
                'take_profit_pct': 30,        # 止盈阈值%
                'take_profit_ma10': True      # 跌破 10 日线止盈
            }
        }
    
    def add_watch_stock(self, symbol: str, name: str = ''):
        """添加监控股票"""
        self.monitor.add_stock(symbol)
        logger.info(f"添加监控股：{symbol} {name}")
    
    def set_watch_list(self, symbols: List[str]):
        """设置监控列表"""
        self.monitor.watch_list = symbols
        logger.info(f"设置监控列表：{len(symbols)}只股票")
    
    # ========== K 线分析方法 (新增) ==========
    
    def check_kline_buy_signal(self, symbol: str) -> tuple:
        """
        K 线买入确认 (v2.0 新增)
        
        Returns:
            (bool, str): (是否满足条件，原因)
        """
        kline = self.fetcher.get_realtime_kline(symbol, count=10)
        quote = self.fetcher.get_realtime_quote(symbol)
        
        if not kline or not quote or len(kline) < 6:
            return False, "数据不足"
        
        current_price = quote['price']
        
        # 1. 5 日均线向上
        if self.kline_params['buy']['ma5_up']:
            ma5 = kline.iloc[-5:]['收盘'].mean()
            ma5_prev = kline.iloc[-6:-1]['收盘'].mean()
            if ma5 <= ma5_prev:
                return False, "5 日线未向上"
        
        # 2. 量比 > 1.5
        current_vol = quote.get('volume', 0)
        avg_vol = kline.iloc[-5:]['成交量'].mean()
        volume_ratio = current_vol / avg_vol if avg_vol > 0 else 0
        
        if volume_ratio < self.kline_params['buy']['volume_ratio_min']:
            return False, f"量比不足 ({volume_ratio:.2f} < {self.kline_params['buy']['volume_ratio_min']})"
        
        # 3. 换手率 > 10%
        turnover = quote.get('turnover_rate', 0)
        if turnover < self.kline_params['buy']['turnover_rate_min']:
            return False, f"换手率不足 ({turnover:.1f}% < {self.kline_params['buy']['turnover_rate_min']}%)"
        
        # 4. 无上影线或上影线 < 3%
        high = quote.get('high', current_price)
        upper_shadow = (high - current_price) / current_price * 100 if current_price > 0 else 0
        
        if upper_shadow > self.kline_params['buy']['upper_shadow_max']:
            return False, f"上影线过长 ({upper_shadow:.1f}% > {self.kline_params['buy']['upper_shadow_max']}%)"
        
        return True, f"K 线确认：量比{volume_ratio:.2f}, 换手{turnover:.1f}%, 上影{upper_shadow:.1f}%"
    
    def check_sell_signal(self, symbol: str, position: dict) -> Optional[str]:
        """
        K 线卖出信号检测 (v2.0 新增)
        
        Args:
            symbol: 股票代码
            position: 持仓信息 {stock_code, cost_price, quantity, ...}
        
        Returns:
            str or None: 卖出原因，无信号返回 None
        """
        kline = self.fetcher.get_realtime_kline(symbol, count=20)
        quote = self.fetcher.get_realtime_quote(symbol)
        
        if kline is None or len(kline) == 0 or not quote:
            return None
        
        current_price = quote['price']
        cost_price = position.get('cost_price', current_price)
        
        # 计算均线
        ma5 = kline.iloc[-5:]['收盘'].mean()
        ma10 = kline.iloc[-10:]['收盘'].mean()
        
        # 当日跌幅
        prev_close = kline.iloc[-2]['收盘'] if len(kline) > 1 else current_price
        change_pct = (current_price - prev_close) / prev_close * 100 if prev_close > 0 else 0
        
        # 量比
        current_vol = quote.get('volume', 0)
        avg_vol = kline.iloc[-5:]['成交量'].mean()
        volume_ratio = current_vol / avg_vol if avg_vol > 0 else 0
        
        # ========== 止损检查 ==========
        
        # 1. 跌破 5 日线
        if self.kline_params['sell']['stop_loss_ma5']:
            if current_price < ma5 * 0.98:  # 2% 容错
                return f"止损：跌破 5 日线 ({current_price:.2f} < {ma5:.2f})"
        
        # 2. 当日跌幅 > -5%
        if change_pct < self.kline_params['sell']['stop_loss_change_pct']:
            return f"止损：当日跌幅 {change_pct:.1f}%"
        
        # 3. 放量下跌
        if self.kline_params['sell']['stop_loss_volume_down']:
            if volume_ratio > 2 and change_pct < -3:
                return f"止损：放量下跌 (量比{volume_ratio:.2f}, 跌幅{change_pct:.1f}%)"
        
        # ========== 止盈检查 ==========
        
        # 计算盈利
        profit_pct = (current_price - cost_price) / cost_price * 100 if cost_price > 0 else 0
        
        # 4. 盈利 > 30% + 放量滞涨
        if profit_pct > self.kline_params['sell']['take_profit_pct']:
            if change_pct < 2 and volume_ratio > 2:
                return f"止盈：盈利{profit_pct:.1f}% + 放量滞涨"
        
        # 5. 盈利 > 10% + 跌破 10 日线
        if self.kline_params['sell']['take_profit_ma10']:
            if profit_pct > 10 and current_price < ma10 * 0.98:
                return f"止盈：跌破 10 日线 (盈利{profit_pct:.1f}%)"
        
        # 6. 高位长上影线 (>5%) + 缩量
        high = quote.get('high', current_price)
        upper_shadow = (high - current_price) / current_price * 100 if current_price > 0 else 0
        
        if profit_pct > 20 and upper_shadow > 5 and volume_ratio < 0.7:
            return f"止盈：高位长上影 ({upper_shadow:.1f}%) + 缩量"
        
        return None
    
    def monitor_positions(self, positions: List[dict]) -> List[Dict]:
        """
        持仓 K 线实时监控 (v2.0 新增)
        
        Args:
            positions: 持仓列表
        
        Returns:
            卖出信号列表
        """
        sell_signals = []
        
        for position in positions:
            symbol = position.get('stock_code')
            if not symbol:
                continue
            
            sell_reason = self.check_sell_signal(symbol, position)
            
            if sell_reason:
                signal = {
                    'symbol': symbol,
                    'action': 'sell',
                    'reason': sell_reason,
                    'position': position,
                    'timestamp': datetime.now()
                }
                sell_signals.append(signal)
                logger.info(f"⚠️ 持仓监控：{symbol} - {sell_reason}")
        
        return sell_signals
    
    def check_morning_breakout(self, symbol: str) -> Optional[IntradaySignal]:
        """
        早盘突破策略 v2.0 (09:30-10:30)
        
        条件:
        - 高开 2-5%
        - 开盘后继续上涨
        - 成交量放大
        - K 线确认 (5 日线向上、量比、换手率)
        """
        # 获取实时行情
        quote = self.fetcher.get_realtime_quote(symbol)
        if not quote:
            return None
        
        # 获取 K 线
        kline = self.fetcher.get_realtime_kline(symbol, count=30)
        if kline is None or len(kline) < 5:
            return None
        
        current_price = quote['price']
        open_price = quote.get('open', current_price)
        prev_close = kline.iloc[-2]['收盘'] if len(kline) > 1 else open_price
        
        # 高开幅度
        gap_up = (open_price - prev_close) / prev_close * 100
        
        # 当前涨幅
        change_pct = (current_price - prev_close) / prev_close * 100
        
        # 检查条件
        if not (2 <= gap_up <= 5):  # 高开 2-5%
            return None
        
        if change_pct < gap_up:  # 没有继续上涨
            return None
        
        # 成交量
        current_vol = quote.get('volume', 0)
        avg_vol = kline.iloc[-5:]['成交量'].mean()
        volume_ratio = current_vol / avg_vol if avg_vol > 0 else 0
        
        if volume_ratio < 1.5:  # 成交量不够
            return None
        
        # ========== v2.0 新增：K 线确认 ==========
        kline_ok, kline_reason = self.check_kline_buy_signal(symbol)
        if not kline_ok:
            logger.info(f"❌ {symbol} K 线过滤未通过：{kline_reason}")
            return None
        
        # 生成信号
        quantity = int(self.capital * 0.1 / current_price / 100) * 100  # 10% 仓位，100 股整数倍
        
        signal = IntradaySignal(
            symbol=symbol,
            name=quote['name'],
            action='buy',
            strategy='早盘突破',
            price=current_price,
            quantity=quantity,
            reason=f'高开{gap_up:.1f}%, 现涨{change_pct:.1f}%, {kline_reason}',
            timestamp=datetime.now(),
            confidence=0.8,  # v2.0: 信心提升 (有 K 线确认)
            stop_loss=current_price * 0.95,  # -5% 止损
            take_profit=current_price * 1.15,  # +15% 止盈
            market_session='早盘'
        )
        
        logger.info(f"✅ 早盘突破信号：{symbol} - {kline_reason}")
        return signal
    
    def check_pullback_buy(self, symbol: str) -> Optional[IntradaySignal]:
        """
        盘中回调买入策略 v2.0
        
        条件:
        - 从日内高点回调 3-5%
        - 缩量
        - 在支撑位企稳
        - K 线确认 (5 日线向上)
        """
        # 获取 5 分钟 K 线
        kline = self.fetcher.get_realtime_kline(symbol, count=60, scale='5')
        if kline is None or len(kline) < 20:
            return None
        
        # 获取实时行情
        quote = self.fetcher.get_realtime_quote(symbol)
        if not quote:
            return None
        
        current_price = quote['price']
        
        # 日内高点
        intraday_high = kline['最高'].max()
        
        # 回调幅度
        pullback = (intraday_high - current_price) / intraday_high * 100
        
        # 检查回调幅度
        if not (3 <= pullback <= 5):
            return None
        
        # 检查是否缩量
        recent_vol = kline.iloc[-1]['成交量']
        avg_vol = kline.iloc[-10:-1]['成交量'].mean()
        volume_ratio = recent_vol / avg_vol if avg_vol > 0 else 0
        
        if volume_ratio > 0.8:  # 没有明显缩量
            return None
        
        # 检查是否企稳 (最后 3 根 K 线不再创新低)
        recent_lows = kline.iloc[-3:]['最低']
        if recent_lows.min() < kline.iloc[-4]['最低']:
            return None
        
        # ========== v2.0 新增：K 线确认 ==========
        # 回调策略放宽量比要求，但 5 日线必须向上
        kline_ok, kline_reason = self.check_kline_buy_signal(symbol)
        if not kline_ok:
            # 放宽条件：只要 5 日线向上即可
            kline_5 = self.fetcher.get_realtime_kline(symbol, count=10)
            if kline_5 is not None and len(kline_5) >= 6:
                ma5 = kline_5.iloc[-5:]['收盘'].mean()
                ma5_prev = kline_5.iloc[-6:-1]['收盘'].mean()
                if ma5 <= ma5_prev:
                    logger.info(f"❌ {symbol} 回调但 5 日线向下")
                    return None
                kline_reason = f"5 日线向上，回调{pullback:.1f}%"
            else:
                return None
        
        # 生成信号
        quantity = int(self.capital * 0.1 / current_price / 100) * 100
        
        signal = IntradaySignal(
            symbol=symbol,
            name=quote['name'],
            action='buy',
            strategy='盘中回调',
            price=current_price,
            quantity=quantity,
            reason=f'回调{pullback:.1f}%, 缩量{volume_ratio:.2f}倍, {kline_reason}',
            timestamp=datetime.now(),
            confidence=0.7,  # v2.0: 信心提升
            stop_loss=current_price * 0.95,
            take_profit=current_price * 1.10,
            market_session=self.monitor.get_market_session()
        )
        
        logger.info(f"✅ 盘中回调信号：{symbol} - {kline_reason}")
        return signal
    
    def check_tail_buy(self, symbol: str) -> Optional[IntradaySignal]:
        """
        尾盘买入策略 v2.0 (14:30-15:00)
        
        条件:
        - 全天强势 (涨幅 3-7%)
        - 尾盘不跳水
        - 成交量正常
        - K 线确认 (5 日线向上，无上影线)
        """
        # 检查时间
        now = datetime.now().time()
        tail_start = time(14, 30)
        tail_end = time(15, 0)
        
        if not (tail_start <= now <= tail_end):
            return None
        
        # 获取实时行情
        quote = self.fetcher.get_realtime_quote(symbol)
        if not quote:
            return None
        
        # 获取日线
        kline = self.fetcher.get_realtime_kline(symbol, count=30)
        if kline is None or len(kline) < 5:
            return None
        
        current_price = quote['price']
        prev_close = kline.iloc[-2]['收盘']
        
        # 涨幅
        change_pct = (current_price - prev_close) / prev_close * 100
        
        # 检查涨幅
        if not (3 <= change_pct <= 7):
            return None
        
        # 检查尾盘是否稳定 (最后 30 分钟不跌破均价)
        intraday_kline = self.fetcher.get_realtime_kline(symbol, count=10, scale='5')
        if intraday_kline is None:
            return None
        
        avg_price = intraday_kline['收盘'].mean()
        if current_price < avg_price * 0.98:  # 跌破均价 2%
            return None
        
        # ========== v2.0 新增：K 线确认 ==========
        kline_ok, kline_reason = self.check_kline_buy_signal(symbol)
        if not kline_ok:
            # 尾盘策略放宽：只要 5 日线向上 + 无上影线
            kline_5 = self.fetcher.get_realtime_kline(symbol, count=10)
            if kline_5 is not None and len(kline_5) >= 6:
                ma5 = kline_5.iloc[-5:]['收盘'].mean()
                ma5_prev = kline_5.iloc[-6:-1]['收盘'].mean()
                if ma5 <= ma5_prev:
                    logger.info(f"❌ {symbol} 尾盘但 5 日线向下")
                    return None
                
                # 检查上影线
                high = quote.get('high', current_price)
                upper_shadow = (high - current_price) / current_price * 100 if current_price > 0 else 0
                if upper_shadow > 3:
                    logger.info(f"❌ {symbol} 尾盘上影线过长 ({upper_shadow:.1f}%)")
                    return None
                
                kline_reason = f"5 日线向上，上影{upper_shadow:.1f}%"
            else:
                return None
        
        # 生成信号
        quantity = int(self.capital * 0.1 / current_price / 100) * 100
        
        signal = IntradaySignal(
            symbol=symbol,
            name=quote['name'],
            action='buy',
            strategy='尾盘买入',
            price=current_price,
            quantity=quantity,
            reason=f'涨幅{change_pct:.1f}%, 尾盘稳定，{kline_reason}',
            timestamp=datetime.now(),
            confidence=0.85,  # v2.0: 尾盘 +K 线确认，最高信心
            stop_loss=current_price * 0.95,
            take_profit=current_price * 1.10,
            market_session='尾盘'
        )
        
        logger.info(f"✅ 尾盘买入信号：{symbol} - {kline_reason}")
        return signal
    
    def scan_all(self, positions: List[dict] = None) -> List[IntradaySignal]:
        """
        扫描所有监控股票 v2.0
        
        Args:
            positions: 持仓列表 (可选，用于监控卖出信号)
        """
        self.signals = []
        now = datetime.now().time()
        
        logger.info(f"开始盘中扫描，监控 {len(self.monitor.watch_list)} 只股票...")
        
        # ========== v2.0 新增：持仓监控 ==========
        if positions:
            sell_signals = self.monitor_positions(positions)
            for sell_sig in sell_signals:
                position = sell_sig['position']
                signal = IntradaySignal(
                    symbol=sell_sig['symbol'],
                    name=position.get('stock_name', ''),
                    action='sell',
                    strategy='K 线止损/止盈',
                    price=0,  # 实际执行时获取实时价
                    quantity=position.get('quantity', 0),
                    reason=sell_sig['reason'],
                    timestamp=sell_sig['timestamp'],
                    confidence=0.9,  # 止损/止盈信号高信心
                    stop_loss=0,
                    take_profit=0,
                    market_session=self.monitor.get_market_session()
                )
                self.signals.append(signal)
        
        # 买入信号扫描
        for symbol in self.monitor.watch_list:
            # 早盘策略 (09:30-10:30)
            if time(9, 30) <= now <= time(10, 30):
                signal = self.check_morning_breakout(symbol)
                if signal:
                    self.signals.append(signal)
            
            # 盘中回调 (全天)
            if time(9, 35) <= now <= time(14, 50):
                signal = self.check_pullback_buy(symbol)
                if signal:
                    self.signals.append(signal)
            
            # 尾盘策略 (14:30-15:00)
            if time(14, 30) <= now <= time(15, 0):
                signal = self.check_tail_buy(symbol)
                if signal:
                    self.signals.append(signal)
        
        logger.info(f"扫描完成，生成 {len(self.signals)} 个信号")
        return self.signals
    
    def print_signals(self):
        """打印信号"""
        if not self.signals:
            print("  无信号")
            return
        
        print(f"\n生成 {len(self.signals)} 个交易信号:")
        print("=" * 80)
        
        for sig in self.signals:
            print(f"\n{sig.symbol} {sig.name}")
            print(f"  策略：{sig.strategy}")
            print(f"  动作：{sig.action}")
            print(f"  价格：{sig.price:.2f}元")
            print(f"  仓位：{sig.quantity}股")
            print(f"  理由：{sig.reason}")
            print(f"  信心：{sig.confidence}")
            print(f"  止损：{sig.stop_loss:.2f}元 (-5%)")
            print(f"  止盈：{sig.take_profit:.2f}元 (+10~15%)")
            print(f"  时段：{sig.market_session}")
        
        print("=" * 80)
    
    def execute_signals(self):
        """执行信号 (模拟)"""
        if not self.signals:
            return
        
        print("\n执行交易信号...")
        for sig in self.signals:
            if sig.action == 'buy':
                print(f"  ✅ 买入 {sig.symbol} {sig.quantity}股 @ {sig.price:.2f}元")
                # 实际执行需要对接交易接口
                # self.paper_trading.buy(...)
    
    def run(self, interval=300):
        """
        运行盘中监控
        
        Args:
            interval: 扫描间隔 (秒)
        """
        print("\n" + "=" * 60)
        print("盘中实时监控系统启动")
        print("=" * 60)
        print(f"监控股票：{len(self.monitor.watch_list)}只")
        print(f"扫描间隔：{interval}秒")
        print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"交易时段：{self.monitor.get_market_session()}")
        print("=" * 60)
        
        while self.monitor.is_market_open():
            # 扫描
            self.scan_all()
            
            # 打印信号
            if self.signals:
                self.print_signals()
                self.execute_signals()
            
            # 等待
            print(f"\n等待{interval}秒后下次扫描...")
            time.sleep(interval)
        
        print("\n市场已关闭，停止监控")


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("盘中实时策略测试")
    print("=" * 60)
    
    # 创建策略引擎
    strategy = IntradayStrategy(capital=100000)
    
    # 设置监控列表 (龙头股)
    watch_stocks = [
        '000533',  # 顺钠股份
        '605268',  # 王力安防
        '600545',  # 卓郎智能
        '002498',  # 汉缆股份
        '600590',  # 泰豪科技
    ]
    
    strategy.set_watch_list(watch_stocks)
    print(f"监控列表：{watch_stocks}")
    
    # 扫描
    print("\n开始扫描...")
    signals = strategy.scan_all()
    strategy.print_signals()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
    
    print("\n💡 提示:")
    print("  - 当前是休市时间，无实时行情")
    print("  - 交易时间运行才能获取实时数据")
    print("  - 运行：python intraday_strategy.py --live")
