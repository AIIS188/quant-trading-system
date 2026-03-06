"""
风控模块
严格执行交易风险控制
"""

import pandas as pd
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Position:
    """持仓记录"""
    stock_code: str
    stock_name: str
    quantity: int
    cost_price: float
    current_price: float
    buy_date: datetime
    strategy: str


@dataclass
class Trade:
    """交易记录"""
    stock_code: str
    action: str  # buy/sell
    quantity: int
    price: float
    amount: float
    date: datetime
    strategy: str
    pnl: float = 0  # 盈亏


class RiskController:
    """风险控制器"""
    
    def __init__(self, total_capital=100000):
        self.total_capital = total_capital  # 总资金
        self.available_capital = total_capital  # 可用资金
        self.positions: List[Position] = []  # 当前持仓
        self.trades: List[Trade] = []  # 交易记录
        
        # 风控参数
        self.max_position_pct = 0.10  # 单笔仓位 ≤ 10%
        self.max_drawdown = 0.08  # 最大回撤 ≤ 8%
        self.max_daily_loss = 0.03  # 单日亏损 ≤ 3%
        self.max_consecutive_loss = 3  # 连续亏损次数
        
        # 风控状态
        self.current_drawdown = 0  # 当前回撤
        self.daily_pnl = 0  # 当日盈亏
        self.consecutive_loss = 0  # 连续亏损次数
        self.peak_capital = total_capital  # 资金峰值
        self.trading_allowed = True  # 是否允许交易
    
    def calculate_position(self, price: float) -> int:
        """
        计算可买入数量
        :param price: 当前价格
        :return: 可买入数量 (股)
        """
        if not self.trading_allowed:
            return 0
        
        # 单笔最大金额
        max_amount = self.total_capital * self.max_position_pct
        
        # 考虑可用资金
        max_amount = min(max_amount, self.available_capital * 0.95)  # 留 5% 现金
        
        # 计算数量 (100 股的整数倍)
        quantity = int(max_amount / price / 100) * 100
        
        return max(quantity, 0)
    
    def check_signal(self, signal) -> bool:
        """
        检查信号是否符合风控要求
        :param signal: 交易信号
        :return: 是否允许执行
        """
        # 检查是否允许交易
        if not self.trading_allowed:
            print(f"风控拦截：交易已暂停 (连续亏损{self.consecutive_loss}次)")
            return False
        
        # 检查信号类型
        if signal.action != "buy":
            return True
        
        # 检查单笔仓位
        required_amount = signal.price * signal.quantity
        max_allowed = self.total_capital * self.max_position_pct
        
        if required_amount > max_allowed:
            print(f"风控拦截：单笔仓位超限 ({required_amount:.2f} > {max_allowed:.2f})")
            return False
        
        # 检查可用资金
        if required_amount > self.available_capital:
            print(f"风控拦截：可用资金不足 ({required_amount:.2f} > {self.available_capital:.2f})")
            return False
        
        # 检查当日亏损
        daily_loss_limit = self.total_capital * self.max_daily_loss
        if self.daily_pnl < -daily_loss_limit:
            print(f"风控拦截：触及单日亏损限制 ({self.daily_pnl:.2f} < {-daily_loss_limit:.2f})")
            self.trading_allowed = False
            return False
        
        # 检查回撤
        drawdown_limit = self.total_capital * self.max_drawdown
        if self.current_drawdown > drawdown_limit:
            print(f"风控拦截：触及最大回撤限制 ({self.current_drawdown:.2f} > {drawdown_limit:.2f})")
            self.trading_allowed = False
            return False
        
        return True
    
    def execute_buy(self, signal) -> Optional[Position]:
        """
        执行买入
        :param signal: 买入信号
        :return: 持仓记录
        """
        if not self.check_signal(signal):
            return None
        
        amount = signal.price * signal.quantity
        
        # 更新资金
        self.available_capital -= amount
        
        # 创建持仓
        position = Position(
            stock_code=signal.stock_code,
            stock_name=signal.stock_name,
            quantity=signal.quantity,
            cost_price=signal.price,
            current_price=signal.price,
            buy_date=datetime.now(),
            strategy=signal.strategy
        )
        
        self.positions.append(position)
        
        # 记录交易
        trade = Trade(
            stock_code=signal.stock_code,
            action="buy",
            quantity=signal.quantity,
            price=signal.price,
            amount=amount,
            date=datetime.now(),
            strategy=signal.strategy
        )
        self.trades.append(trade)
        
        print(f"买入：{signal.stock_code} {signal.quantity}股 @ {signal.price}")
        return position
    
    def execute_sell(self, stock_code: str, price: float, quantity: int = None) -> Optional[Trade]:
        """
        执行卖出
        :param stock_code: 股票代码
        :param price: 卖出价格
        :param quantity: 卖出数量，默认全部
        :return: 交易记录
        """
        # 查找持仓
        position = None
        for pos in self.positions:
            if pos.stock_code == stock_code:
                position = pos
                break
        
        if position is None:
            print(f"卖出失败：未找到持仓 {stock_code}")
            return None
        
        if quantity is None:
            quantity = position.quantity
        
        if quantity > position.quantity:
            quantity = position.quantity
        
        # 计算盈亏
        pnl = (price - position.cost_price) * quantity
        
        # 更新资金
        amount = price * quantity
        self.available_capital += amount
        
        # 更新当日盈亏
        self.daily_pnl += pnl
        
        # 更新连续亏损计数
        if pnl < 0:
            self.consecutive_loss += 1
            if self.consecutive_loss >= self.max_consecutive_loss:
                print(f"风控警告：连续亏损{self.consecutive_loss}次，暂停交易")
                self.trading_allowed = False
        else:
            self.consecutive_loss = 0
        
        # 更新峰值和回撤
        total_value = self.available_capital + sum(p.quantity * p.current_price for p in self.positions)
        if total_value > self.peak_capital:
            self.peak_capital = total_value
        
        self.current_drawdown = self.peak_capital - total_value
        
        # 记录交易
        trade = Trade(
            stock_code=stock_code,
            action="sell",
            quantity=quantity,
            price=price,
            amount=amount,
            date=datetime.now(),
            strategy=position.strategy,
            pnl=pnl
        )
        self.trades.append(trade)
        
        # 更新或移除持仓
        if quantity >= position.quantity:
            self.positions.remove(position)
        else:
            position.quantity -= quantity
        
        print(f"卖出：{stock_code} {quantity}股 @ {price}, 盈亏：{pnl:.2f}")
        return trade
    
    def update_positions(self, prices: dict):
        """
        更新持仓价格
        :param prices: {stock_code: current_price}
        """
        for position in self.positions:
            if position.stock_code in prices:
                position.current_price = prices[position.stock_code]
        
        # 重新计算回撤
        total_value = self.available_capital + sum(
            p.quantity * p.current_price for p in self.positions
        )
        
        if total_value > self.peak_capital:
            self.peak_capital = total_value
        
        self.current_drawdown = self.peak_capital - total_value
    
    def get_daily_report(self) -> dict:
        """生成每日风控报告"""
        total_value = self.available_capital + sum(
            p.quantity * p.current_price for p in self.positions
        )
        
        total_pnl = total_value - self.total_capital
        total_pnl_pct = total_pnl / self.total_capital * 100
        
        today_trades = [t for t in self.trades if t.date.date() == datetime.now().date()]
        today_pnl = sum(t.pnl for t in today_trades if t.action == "sell")
        
        return {
            'date': datetime.now().strftime('%Y-%m-%d'),
            '总资金': f"{total_value:.2f}",
            '可用资金': f"{self.available_capital:.2f}",
            '持仓数量': len(self.positions),
            '总盈亏': f"{total_pnl:.2f} ({total_pnl_pct:.2f}%)",
            '当日盈亏': f"{today_pnl:.2f}",
            '当前回撤': f"{self.current_drawdown:.2f}",
            '最大回撤': f"{self.peak_capital - self.total_capital:.2f}",
            '连续亏损': self.consecutive_loss,
            '交易状态': "正常" if self.trading_allowed else "暂停",
            '持仓明细': [
                {
                    '代码': p.stock_code,
                    '名称': p.stock_name,
                    '数量': p.quantity,
                    '成本': p.cost_price,
                    '现价': p.current_price,
                    '盈亏': (p.current_price - p.cost_price) * p.quantity
                }
                for p in self.positions
            ]
        }
    
    def reset_daily(self):
        """每日重置"""
        self.daily_pnl = 0
        # 不重置连续亏损，因为这是持续的风险指标
    
    def resume_trading(self):
        """恢复交易 (需要人工确认)"""
        print("风控提示：恢复交易需要人工确认")
        # 实际应该要求人工确认
        self.trading_allowed = True
        self.consecutive_loss = 0
        print("交易已恢复")


# 测试
if __name__ == "__main__":
    controller = RiskController(total_capital=100000)
    
    print("测试风控模块...")
    print(f"\n初始资金：{controller.total_capital}")
    print(f"单笔最大仓位：{controller.total_capital * controller.max_position_pct}")
    print(f"最大回撤限制：{controller.total_capital * controller.max_drawdown}")
    print(f"单日亏损限制：{controller.total_capital * controller.max_daily_loss}")
    
    # 模拟买入
    print("\n--- 模拟交易 ---")
    from dataclasses import dataclass
    
    @dataclass
    class TestSignal:
        stock_code: str
        stock_name: str
        strategy: str
        action: str
        price: float
        quantity: int
        reason: str
        timestamp: datetime
        confidence: float
    
    signal = TestSignal(
        stock_code="000001",
        stock_name="平安银行",
        strategy="龙头回调",
        action="buy",
        price=10.5,
        quantity=900,
        reason="测试",
        timestamp=datetime.now(),
        confidence=0.7
    )
    
    position = controller.execute_buy(signal)
    if position:
        print(f"买入成功：{position.quantity}股 @ {position.cost_price}")
    
    # 生成报告
    report = controller.get_daily_report()
    print(f"\n风控报告:")
    for k, v in report.items():
        if k != '持仓明细':
            print(f"  {k}: {v}")
