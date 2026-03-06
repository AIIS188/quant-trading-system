"""
策略引擎模块
实现三大核心交易策略
"""

import pandas as pd
import numpy as np
from datetime import datetime
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class Signal:
    """交易信号"""
    stock_code: str
    stock_name: str
    strategy: str
    action: str  # buy/sell
    price: float
    quantity: int
    reason: str
    timestamp: datetime
    confidence: float  # 0-1


class StrategyEngine:
    """交易策略引擎"""
    
    def __init__(self, data_fetcher, risk_controller):
        self.data_fetcher = data_fetcher
        self.risk_controller = risk_controller
        self.signals = []
        self.strategy_stats = {
            '龙头回调': {'total': 0, 'win': 0, 'win_rate': 0},
            '突破': {'total': 0, 'win': 0, 'win_rate': 0},
            '情绪周期': {'total': 0, 'win': 0, 'win_rate': 0}
        }
    
    def check_leader_pullback(self, stock_code, threshold_low=5, threshold_high=10):
        """
        策略 1: 龙头回调
        条件:
        - 板块龙头
        - 回调 5%-10%
        - 成交量缩量
        
        :param stock_code: 股票代码
        :param threshold_low: 回调下限%
        :param threshold_high: 回调上限%
        :return: Signal or None
        """
        # 获取 K 线数据 (最近 20 日)
        kline = self.data_fetcher.get_kline(stock_code, period="daily")
        if kline is None or len(kline) < 10:
            return None
        
        kline = kline.tail(20).reset_index(drop=True)
        
        # 计算回调幅度
        current_price = kline.iloc[-1]['收盘']
        recent_high = kline['最高'].max()
        pullback_pct = (recent_high - current_price) / recent_high * 100
        
        # 检查回调幅度
        if not (threshold_low <= pullback_pct <= threshold_high):
            return None
        
        # 检查成交量是否缩量
        recent_vol = kline.iloc[-1]['成交量']
        avg_vol = kline.iloc[-6:-1]['成交量'].mean()
        volume_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        if volume_ratio >= 1:  # 没有缩量
            return None
        
        # 获取股票信息
        stock_info = self.data_fetcher.get_stock_info(stock_code)
        stock_name = stock_code
        
        # 生成信号
        signal = Signal(
            stock_code=stock_code,
            stock_name=stock_name,
            strategy="龙头回调",
            action="buy",
            price=current_price,
            quantity=self.risk_controller.calculate_position(current_price),
            reason=f"龙头回调{pullback_pct:.1f}%, 成交量缩量{volume_ratio:.2f}倍",
            timestamp=datetime.now(),
            confidence=0.7 if volume_ratio < 0.7 else 0.5
        )
        
        return signal
    
    def check_breakout(self, stock_code, turnover_threshold=10):
        """
        策略 2: 突破
        条件:
        - 突破平台
        - 成交量放大
        - 换手率 > 10%
        
        :param stock_code: 股票代码
        :param turnover_threshold: 换手率阈值%
        :return: Signal or None
        """
        # 获取 K 线数据
        kline = self.data_fetcher.get_kline(stock_code, period="daily")
        if kline is None or len(kline) < 30:
            return None
        
        kline = kline.tail(30).reset_index(drop=True)
        
        current_price = kline.iloc[-1]['收盘']
        current_high = kline.iloc[-1]['最高']
        
        # 计算平台压力位 (最近 20 日最高)
        platform_high = kline.iloc[:-1]['最高'].max()
        
        # 检查是否突破
        if current_high <= platform_high:
            return None
        
        # 检查成交量是否放大
        recent_vol = kline.iloc[-1]['成交量']
        avg_vol = kline.iloc[-10:-1]['成交量'].mean()
        volume_ratio = recent_vol / avg_vol if avg_vol > 0 else 1
        
        if volume_ratio < 1.5:  # 成交量没有明显放大
            return None
        
        # 检查换手率
        turnover = kline.iloc[-1].get('换手率', 0)
        if turnover < turnover_threshold:
            return None
        
        stock_name = stock_code
        
        # 生成信号
        signal = Signal(
            stock_code=stock_code,
            stock_name=stock_name,
            strategy="突破",
            action="buy",
            price=current_price,
            quantity=self.risk_controller.calculate_position(current_price),
            reason=f"突破平台，成交量放大{volume_ratio:.2f}倍，换手率{turnover:.1f}%",
            timestamp=datetime.now(),
            confidence=0.75 if turnover > 15 else 0.6
        )
        
        return signal
    
    def check_emotion_cycle(self, emotion_score, leaders):
        """
        策略 3: 情绪周期
        在情绪上升期：做龙头、做强势板块
        在退潮期：空仓、控制风险
        
        :param emotion_score: 情绪得分 (0-100)
        :param leaders: 龙头股列表
        :return: List[Signal]
        """
        signals = []
        
        if emotion_score >= 60:
            # 上升期 - 积极参与龙头
            for leader in leaders[:3]:  # 只取前 3 只龙头
                stock_code = leader.get('代码', '')
                if stock_code:
                    signal = Signal(
                        stock_code=stock_code,
                        stock_name=leader.get('名称', ''),
                        strategy="情绪周期",
                        action="buy",
                        price=leader.get('最新价', 0),
                        quantity=self.risk_controller.calculate_position(leader.get('最新价', 10)),
                        reason=f"情绪上升期 (得分{emotion_score}), 龙头股 (连板{leader.get('连板数', 0)})",
                        timestamp=datetime.now(),
                        confidence=0.8 if emotion_score > 70 else 0.65
                    )
                    signals.append(signal)
        
        elif emotion_score <= 30:
            # 退潮期 - 生成卖出信号或空仓建议
            signal = Signal(
                stock_code="MARKET",
                stock_name="市场",
                strategy="情绪周期",
                action="sell",
                price=0,
                quantity=0,
                reason=f"情绪退潮期 (得分{emotion_score}), 建议空仓或轻仓",
                timestamp=datetime.now(),
                confidence=0.9
            )
            signals.append(signal)
        
        return signals
    
    def scan_market(self, stock_list=None, max_stocks=10):
        """
        扫描市场，生成交易信号
        :param stock_list: 待扫描的股票列表，默认使用涨停股
        :param max_stocks: 最大扫描数量 (避免 API 限流)
        :return: List[Signal]
        """
        self.signals = []
        
        # 如果没有指定股票列表，使用涨停股
        if stock_list is None:
            limit_up = self.data_fetcher.get_limit_up()
            if limit_up is not None:
                # 优先扫描连板股
                if '连板数' in limit_up.columns:
                    limit_up_sorted = limit_up.sort_values('连板数', ascending=False)
                    stock_list = limit_up_sorted['代码'].tolist()[:max_stocks]
                else:
                    stock_list = limit_up['代码'].tolist()[:max_stocks]
            else:
                stock_list = []
        
        # 扫描每只股票
        for i, stock_code in enumerate(stock_list):
            if not isinstance(stock_code, str):
                continue
            
            print(f"   扫描 [{i+1}/{len(stock_list)}] {stock_code}...")
            
            # 策略 1: 龙头回调
            signal = self.check_leader_pullback(stock_code)
            if signal:
                self.signals.append(signal)
                print(f"      ✅ 发现信号：{signal.strategy}")
            
            # 策略 2: 突破
            signal = self.check_breakout(stock_code)
            if signal:
                self.signals.append(signal)
                print(f"      ✅ 发现信号：{signal.strategy}")
        
        return self.signals
    
    def execute_signals(self, signals, emotion_score, leaders):
        """
        执行信号生成
        :param signals: 策略信号列表
        :param emotion_score: 情绪得分
        :param leaders: 龙头股列表
        :return: 最终可执行信号
        """
        # 添加情绪周期信号
        emotion_signals = self.check_emotion_cycle(emotion_score, leaders)
        all_signals = signals + emotion_signals
        
        # 风控过滤
        filtered_signals = []
        for signal in all_signals:
            if self.risk_controller.check_signal(signal):
                filtered_signals.append(signal)
        
        return filtered_signals
    
    def update_strategy_stats(self, strategy, is_win):
        """更新策略统计"""
        if strategy in self.strategy_stats:
            self.strategy_stats[strategy]['total'] += 1
            if is_win:
                self.strategy_stats[strategy]['win'] += 1
            
            total = self.strategy_stats[strategy]['total']
            win = self.strategy_stats[strategy]['win']
            self.strategy_stats[strategy]['win_rate'] = win / total if total > 0 else 0
    
    def get_strategy_performance(self):
        """获取策略表现"""
        return self.strategy_stats.copy()


# 测试
if __name__ == "__main__":
    from data_fetcher import DataFetcher
    from risk_controller import RiskController
    
    fetcher = DataFetcher()
    risk_ctrl = RiskController(total_capital=100000)
    engine = StrategyEngine(fetcher, risk_ctrl)
    
    print("测试策略引擎...")
    
    # 获取涨停股
    limit_up = fetcher.get_limit_up()
    if limit_up is not None:
        stocks = limit_up['代码'].tolist()[:5]
        print(f"\n扫描 {len(stocks)} 只涨停股...")
        
        signals = engine.scan_market(stocks)
        print(f"生成 {len(signals)} 个交易信号:")
        
        for sig in signals:
            print(f"\n  {sig.stock_code} {sig.stock_name}")
            print(f"  策略：{sig.strategy}")
            print(f"  动作：{sig.action}")
            print(f"  原因：{sig.reason}")
            print(f"  信心：{sig.confidence}")
