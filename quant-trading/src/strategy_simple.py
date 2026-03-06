"""
简化策略引擎
不依赖 K 线数据，基于涨停板、龙虎榜等可用数据
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict


@dataclass
class Signal:
    """交易信号"""
    stock_code: str
    stock_name: str
    strategy: str
    action: str
    price: float
    quantity: int
    reason: str
    timestamp: datetime
    confidence: float


class SimpleStrategyEngine:
    """简化策略引擎 - 基于可用数据"""
    
    def __init__(self, risk_controller):
        self.risk_controller = risk_controller
        self.signals = []
    
    def scan_limit_up_stocks(self, limit_up_data: List[Dict], emotion_score: int):
        """
        扫描涨停股，生成信号
        :param limit_up_data: 涨停板数据
        :param emotion_score: 情绪得分
        :return: List[Signal]
        """
        self.signals = []
        
        if not limit_up_data:
            return self.signals
        
        # 情绪上升期才积极做多
        if emotion_score < 40:
            print(f"   情绪低迷 ({emotion_score}分), 减少信号生成")
            return self.signals
        
        # 筛选连板股
        continuous_stocks = []
        for stock in limit_up_data:
            continuous = stock.get('连板数', 0)
            if continuous >= 2:  # 至少 2 连板
                continuous_stocks.append(stock)
        
        # 按连板数排序
        continuous_stocks.sort(key=lambda x: x.get('连板数', 0), reverse=True)
        
        print(f"   发现 {len(continuous_stocks)} 只连板股")
        
        # 策略：龙头股 (最高连板)
        if continuous_stocks and emotion_score >= 60:
            leader = continuous_stocks[0]
            
            signal = Signal(
                stock_code=leader.get('代码', ''),
                stock_name=leader.get('名称', ''),
                strategy="龙头接力",
                action="buy",
                price=leader.get('最新价', 0),
                quantity=self.risk_controller.calculate_position(leader.get('最新价', 10)),
                reason=f"市场龙头，{leader.get('连板数', 0)}连板，封板资金{leader.get('封板资金', 0)}",
                timestamp=datetime.now(),
                confidence=0.7 if leader.get('连板数', 0) >= 3 else 0.5
            )
            
            if self.risk_controller.check_signal(signal):
                self.signals.append(signal)
                print(f"   ✅ 龙头信号：{signal.stock_code} {signal.stock_name}")
        
        # 策略：首板挖掘 (情绪上升期)
        if emotion_score >= 60 and len(continuous_stocks) >= 3:
            # 找首板股 (连板数=1)
            first_board = [s for s in limit_up_data if s.get('连板数', 0) == 1]
            
            if first_board:
                # 选择封板资金最大的
                first_board.sort(key=lambda x: x.get('封板资金', 0), reverse=True)
                candidate = first_board[0]
                
                signal = Signal(
                    stock_code=candidate.get('代码', ''),
                    stock_name=candidate.get('名称', ''),
                    strategy="首板挖掘",
                    action="buy",
                    price=candidate.get('最新价', 0),
                    quantity=self.risk_controller.calculate_position(candidate.get('最新价', 10)),
                    reason=f"首板，封板资金{candidate.get('封板资金', 0)}",
                    timestamp=datetime.now(),
                    confidence=0.5
                )
                
                if self.risk_controller.check_signal(signal):
                    self.signals.append(signal)
                    print(f"   ✅ 首板信号：{signal.stock_code} {signal.stock_name}")
        
        return self.signals
    
    def scan_longhu_stocks(self, longhu_data: List[Dict]):
        """
        扫描龙虎榜，生成信号
        :param longhu_data: 龙虎榜数据
        :return: List[Signal]
        """
        signals = []
        
        if not longhu_data:
            return signals
        
        # 筛选机构买入的
        for stock in longhu_data[:10]:  # 只看前 10
            # 这里需要解析龙虎榜数据
            # 简化处理：如果有机构席位买入，生成信号
            pass
        
        return signals
    
    def check_emotion_cycle(self, emotion_score: int, leaders: List[Dict]):
        """
        情绪周期策略
        :param emotion_score: 情绪得分
        :param leaders: 龙头股列表
        :return: List[Signal]
        """
        signals = []
        
        if emotion_score >= 70:
            # 高潮期 - 谨慎
            signals.append(Signal(
                stock_code="MARKET",
                stock_name="市场",
                strategy="情绪周期",
                action="hold",
                price=0,
                quantity=0,
                reason=f"情绪高潮 ({emotion_score}分), 持有但不追高",
                timestamp=datetime.now(),
                confidence=0.8
            ))
        
        elif emotion_score >= 60:
            # 上升期 - 积极
            for leader in leaders[:2]:
                signals.append(Signal(
                    stock_code=leader.get('代码', ''),
                    stock_name=leader.get('名称', ''),
                    strategy="情绪周期",
                    action="buy",
                    price=leader.get('最新价', 0),
                    quantity=self.risk_controller.calculate_position(leader.get('最新价', 10)),
                    reason=f"情绪上升期 ({emotion_score}分), 龙头股",
                    timestamp=datetime.now(),
                    confidence=0.75
                ))
        
        elif emotion_score <= 30:
            # 退潮期 - 空仓
            signals.append(Signal(
                stock_code="MARKET",
                stock_name="市场",
                strategy="情绪周期",
                action="sell",
                price=0,
                quantity=0,
                reason=f"情绪退潮 ({emotion_score}分), 建议空仓",
                timestamp=datetime.now(),
                confidence=0.9
            ))
        
        return signals
    
    def generate_signals(self, limit_up_data=None, longhu_data=None, emotion_score=50):
        """
        生成综合信号
        :param limit_up_data: 涨停板数据
        :param longhu_data: 龙虎榜数据
        :param emotion_score: 情绪得分
        :return: List[Signal]
        """
        all_signals = []
        
        # 涨停股策略
        if limit_up_data:
            limit_up_signals = self.scan_limit_up_stocks(limit_up_data, emotion_score)
            all_signals.extend(limit_up_signals)
        
        # 龙虎榜策略
        if longhu_data:
            longhu_signals = self.scan_longhu_stocks(longhu_data)
            all_signals.extend(longhu_signals)
        
        # 情绪周期策略
        leaders = []
        if limit_up_data:
            leaders = [s for s in limit_up_data if s.get('连板数', 0) >= 2][:3]
        
        emotion_signals = self.check_emotion_cycle(emotion_score, leaders)
        all_signals.extend(emotion_signals)
        
        # 风控过滤
        filtered = [s for s in all_signals if self.risk_controller.check_signal(s)]
        
        return filtered


# 测试
if __name__ == "__main__":
    from risk_controller import RiskController
    
    risk_ctrl = RiskController(total_capital=100000)
    engine = SimpleStrategyEngine(risk_ctrl)
    
    # 模拟数据
    limit_up = [
        {'代码': '000001', '名称': '平安银行', '最新价': 10.5, '连板数': 3, '封板资金': 100000000},
        {'代码': '000002', '名称': '万科 A', '最新价': 8.2, '连板数': 2, '封板资金': 80000000},
        {'代码': '000003', '名称': '测试股', '最新价': 15.0, '连板数': 1, '封板资金': 50000000},
    ]
    
    print("测试简化策略引擎...")
    print(f"\n情绪得分：70 (上升期)")
    
    signals = engine.generate_signals(limit_up, emotion_score=70)
    
    print(f"\n生成 {len(signals)} 个信号:")
    for sig in signals:
        print(f"\n  {sig.stock_code} {sig.stock_name}")
        print(f"  策略：{sig.strategy}")
        print(f"  动作：{sig.action}")
        print(f"  原因：{sig.reason}")
