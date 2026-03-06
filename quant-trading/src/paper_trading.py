"""
模拟盘交易模块
用于验证策略，不实际交易
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class PaperPosition:
    """模拟持仓"""
    stock_code: str
    stock_name: str
    quantity: int
    cost_price: float
    current_price: float
    buy_date: str
    strategy: str
    signal_reason: str


@dataclass
class PaperTrade:
    """模拟交易记录"""
    stock_code: str
    stock_name: str
    action: str  # buy/sell
    quantity: int
    price: float
    amount: float
    date: str
    strategy: str
    pnl: float = 0
    pnl_pct: float = 0


class PaperTrading:
    """模拟盘"""
    
    def __init__(self, initial_capital=100000, data_dir="data/paper"):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: List[PaperPosition] = []
        self.trades: List[PaperTrade] = []
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 加载已有数据
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        state_file = self.data_dir / "paper_state.json"
        if state_file.exists():
            with open(state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
                self.capital = state.get('capital', self.initial_capital)
                self.positions = [PaperPosition(**p) for p in state.get('positions', [])]
                self.trades = [PaperTrade(**t) for t in state.get('trades', [])]
    
    def _save_state(self):
        """保存状态"""
        state_file = self.data_dir / "paper_state.json"
        state = {
            'capital': self.capital,
            'positions': [p.__dict__ for p in self.positions],
            'trades': [t.__dict__ for t in self.trades]
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def buy(self, stock_code: str, stock_name: str, price: float, quantity: int, 
            strategy: str, signal_reason: str, date: str = None) -> bool:
        """
        模拟买入
        :return: 是否成功
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        amount = price * quantity
        
        # 检查资金
        if amount > self.capital:
            print(f"模拟盘：资金不足 {amount:.2f} > {self.capital:.2f}")
            return False
        
        # 扣减资金
        self.capital -= amount
        
        # 创建持仓
        position = PaperPosition(
            stock_code=stock_code,
            stock_name=stock_name,
            quantity=quantity,
            cost_price=price,
            current_price=price,
            buy_date=date,
            strategy=strategy,
            signal_reason=signal_reason
        )
        self.positions.append(position)
        
        # 记录交易
        trade = PaperTrade(
            stock_code=stock_code,
            stock_name=stock_name,
            action='buy',
            quantity=quantity,
            price=price,
            amount=amount,
            date=date,
            strategy=strategy
        )
        self.trades.append(trade)
        
        print(f"模拟买入：{stock_code} {quantity}股 @ {price:.2f}")
        
        self._save_state()
        return True
    
    def sell(self, stock_code: str, price: float, quantity: int = None, 
             date: str = None) -> float:
        """
        模拟卖出
        :return: 盈亏
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        # 查找持仓
        position = None
        pos_idx = -1
        for i, pos in enumerate(self.positions):
            if pos.stock_code == stock_code:
                position = pos
                pos_idx = i
                break
        
        if position is None:
            print(f"模拟盘：未找到持仓 {stock_code}")
            return 0
        
        if quantity is None:
            quantity = position.quantity
        
        quantity = min(quantity, position.quantity)
        if quantity <= 0:
            return 0
        
        # 计算盈亏
        amount = price * quantity
        cost = position.cost_price * quantity
        pnl = amount - cost
        pnl_pct = pnl / cost * 100 if cost > 0 else 0
        
        # 增加资金
        self.capital += amount
        
        # 更新或移除持仓
        if quantity >= position.quantity:
            self.positions.pop(pos_idx)
        else:
            position.quantity -= quantity
        
        # 记录交易
        trade = PaperTrade(
            stock_code=stock_code,
            stock_name=position.stock_name,
            action='sell',
            quantity=quantity,
            price=price,
            amount=amount,
            date=date,
            strategy=position.strategy,
            pnl=pnl,
            pnl_pct=pnl_pct
        )
        self.trades.append(trade)
        
        print(f"模拟卖出：{stock_code} {quantity}股 @ {price:.2f}, 盈亏：{pnl:.2f} ({pnl_pct:.1f}%)")
        
        self._save_state()
        return pnl
    
    def update_prices(self, prices: Dict[str, float]):
        """
        更新持仓价格
        :param prices: {stock_code: current_price}
        """
        for position in self.positions:
            if position.stock_code in prices:
                position.current_price = prices[position.stock_code]
        
        self._save_state()
    
    def get_report(self) -> Dict:
        """生成模拟盘报告"""
        # 持仓价值
        position_value = sum(p.quantity * p.current_price for p in self.positions)
        total_value = self.capital + position_value
        
        # 总盈亏
        total_pnl = total_value - self.initial_capital
        total_pnl_pct = total_pnl / self.initial_capital * 100
        
        # 已实现盈亏
        realized_pnl = sum(t.pnl for t in self.trades if t.action == 'sell')
        
        # 胜率
        sell_trades = [t for t in self.trades if t.action == 'sell']
        winning_trades = [t for t in sell_trades if t.pnl > 0]
        win_rate = len(winning_trades) / len(sell_trades) * 100 if sell_trades else 0
        
        # 持仓明细
        positions_detail = []
        for p in self.positions:
            pnl = (p.current_price - p.cost_price) * p.quantity
            pnl_pct = pnl / (p.cost_price * p.quantity) * 100 if p.cost_price > 0 else 0
            positions_detail.append({
                '代码': p.stock_code,
                '名称': p.stock_name,
                '数量': p.quantity,
                '成本': p.cost_price,
                '现价': p.current_price,
                '盈亏': pnl,
                '盈亏%': pnl_pct,
                '持仓天数': (datetime.now() - datetime.strptime(p.buy_date, '%Y-%m-%d')).days
            })
        
        return {
            '日期': datetime.now().strftime('%Y-%m-%d'),
            '总资金': f"{total_value:.2f}",
            '可用资金': f"{self.capital:.2f}",
            '持仓价值': f"{position_value:.2f}",
            '总盈亏': f"{total_pnl:.2f} ({total_pnl_pct:.2f}%)",
            '已实现盈亏': f"{realized_pnl:.2f}",
            '交易次数': len(self.trades),
            '胜率': f"{win_rate:.1f}%",
            '持仓数量': len(self.positions),
            '持仓明细': positions_detail,
            '交易记录': [t.__dict__ for t in self.trades[-10:]]  # 最近 10 笔
        }
    
    def print_report(self):
        """打印报告"""
        report = self.get_report()
        
        print("\n" + "=" * 60)
        print(f"模拟盘报告 - {report['日期']}")
        print("=" * 60)
        print(f"总资金：{report['总资金']}")
        print(f"可用资金：{report['可用资金']}")
        print(f"持仓价值：{report['持仓价值']}")
        print(f"总盈亏：{report['总盈亏']}")
        print(f"已实现盈亏：{report['已实现盈亏']}")
        print(f"交易次数：{report['交易次数']}")
        print(f"胜率：{report['胜率']}")
        
        if report['持仓明细']:
            print(f"\n持仓明细:")
            for pos in report['持仓明细']:
                pnl_symbol = "+" if pos['盈亏'] >= 0 else ""
                print(f"  {pos['代码']} {pos['名称']}: {pnl_symbol}{pos['盈亏']:.2f} ({pnl_symbol}{pos['盈亏%']:.1f}%)")
        
        print("=" * 60)
    
    def reset(self):
        """重置模拟盘"""
        self.capital = self.initial_capital
        self.positions = []
        self.trades = []
        self._save_state()
        print("模拟盘已重置")


# 测试
if __name__ == "__main__":
    paper = PaperTrading(initial_capital=100000)
    
    print("测试模拟盘...")
    
    # 模拟买入
    paper.buy('000001', '平安银行', 10.5, 1000, '龙头回调', '回调 8%, 缩量')
    paper.buy('000002', '万科 A', 8.2, 1200, '突破', '突破平台，放量')
    
    # 更新价格
    paper.update_prices({'000001': 11.0, '000002': 8.0})
    
    # 打印报告
    paper.print_report()
    
    # 模拟卖出
    paper.sell('000001', 11.0)
    
    # 最终报告
    paper.print_report()
