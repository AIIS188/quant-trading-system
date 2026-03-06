"""
回测框架
对策略进行历史回测验证
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict
import json
import os

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_values = []
        
        # 回测参数
        self.commission_rate = 0.0003  # 佣金万 3
        self.stamp_tax_rate = 0.001  # 印花税千 1 (卖出收取)
        self.slippage = 0.001  # 滑点 0.1%
    
    def reset(self):
        """重置回测状态"""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.portfolio_values = []
    
    def buy(self, stock_code: str, price: float, quantity: int, date: datetime):
        """
        模拟买入
        """
        if quantity <= 0:
            return
        
        # 计算实际成交价 (考虑滑点)
        actual_price = price * (1 + self.slippage)
        amount = actual_price * quantity
        
        # 佣金
        commission = max(amount * self.commission_rate, 5)  # 最低 5 元
        
        total_cost = amount + commission
        
        if total_cost > self.capital:
            # 资金不足，调整数量
            quantity = int((self.capital * 0.95) / actual_price / 100) * 100
            if quantity <= 0:
                return
            amount = actual_price * quantity
            commission = max(amount * self.commission_rate, 5)
            total_cost = amount + commission
        
        self.capital -= total_cost
        
        # 更新持仓
        if stock_code in self.positions:
            pos = self.positions[stock_code]
            total_qty = pos['quantity'] + quantity
            avg_price = (pos['price'] * pos['quantity'] + actual_price * quantity) / total_qty
            self.positions[stock_code] = {
                'quantity': total_qty,
                'price': avg_price,
                'buy_date': pos['buy_date']
            }
        else:
            self.positions[stock_code] = {
                'quantity': quantity,
                'price': actual_price,
                'buy_date': date
            }
        
        # 记录交易
        self.trades.append({
            'date': date,
            'stock_code': stock_code,
            'action': 'buy',
            'price': actual_price,
            'quantity': quantity,
            'amount': amount,
            'commission': commission,
            'pnl': 0
        })
    
    def sell(self, stock_code: str, price: float, quantity: int = None, date: datetime = None):
        """
        模拟卖出
        """
        if stock_code not in self.positions:
            return 0
        
        pos = self.positions[stock_code]
        if quantity is None:
            quantity = pos['quantity']
        
        quantity = min(quantity, pos['quantity'])
        if quantity <= 0:
            return 0
        
        # 计算实际成交价 (考虑滑点)
        actual_price = price * (1 - self.slippage)
        amount = actual_price * quantity
        
        # 佣金和印花税
        commission = max(amount * self.commission_rate, 5)
        stamp_tax = amount * self.stamp_tax_rate
        
        total_received = amount - commission - stamp_tax
        
        # 计算盈亏
        pnl = (actual_price - pos['price']) * quantity - commission - stamp_tax
        
        self.capital += total_received
        
        # 更新持仓
        pos['quantity'] -= quantity
        if pos['quantity'] <= 0:
            del self.positions[stock_code]
        
        # 记录交易
        self.trades.append({
            'date': date,
            'stock_code': stock_code,
            'action': 'sell',
            'price': actual_price,
            'quantity': quantity,
            'amount': amount,
            'commission': commission,
            'stamp_tax': stamp_tax,
            'pnl': pnl
        })
        
        return pnl
    
    def update_portfolio_value(self, current_prices: Dict[str, float], date: datetime):
        """更新组合价值"""
        position_value = sum(
            qty * current_prices.get(code, pos['price'])
            for code, pos in self.positions.items()
            for qty in [pos['quantity']]
        )
        total_value = self.capital + position_value
        
        self.portfolio_values.append({
            'date': date,
            'total_value': total_value,
            'capital': self.capital,
            'position_value': position_value
        })
        
        return total_value
    
    def run_backtest(self, kline_data: pd.DataFrame, signals: List[Dict]) -> Dict:
        """
        运行回测
        :param kline_data: K 线数据 DataFrame (包含日期、代码、开盘、收盘、最高、最低等)
        :param signals: 交易信号列表
        :return: 回测结果
        """
        self.reset()
        
        dates = sorted(kline_data['日期'].unique())
        
        for date in dates:
            date_str = date if isinstance(date, str) else date.strftime('%Y-%m-%d')
            date_dt = datetime.strptime(date_str, '%Y-%m-%d') if isinstance(date, str) else date
            
            # 获取当日 K 线
            daily_kline = kline_data[kline_data['日期'] == date]
            current_prices = dict(zip(daily_kline['代码'], daily_kline['收盘']))
            
            # 处理当日信号
            daily_signals = [s for s in signals if s['date'] == date_str]
            for signal in daily_signals:
                if signal['action'] == 'buy':
                    price = daily_kline[daily_kline['代码'] == signal['stock_code']]['收盘'].values
                    if len(price) > 0:
                        self.buy(signal['stock_code'], price[0], signal['quantity'], date_dt)
                elif signal['action'] == 'sell':
                    price = daily_kline[daily_kline['代码'] == signal['stock_code']]['收盘'].values
                    if len(price) > 0:
                        self.sell(signal['stock_code'], price[0], signal.get('quantity'), date_dt)
            
            # 更新组合价值
            self.update_portfolio_value(current_prices, date_dt)
        
        return self.calculate_metrics()
    
    def calculate_metrics(self) -> Dict:
        """计算回测指标"""
        if not self.portfolio_values:
            return {}
        
        values = [pv['total_value'] for pv in self.portfolio_values]
        
        # 总收益
        total_return = (values[-1] - self.initial_capital) / self.initial_capital * 100
        
        # 年化收益 (假设 250 个交易日)
        days = len(values)
        annual_return = ((values[-1] / self.initial_capital) ** (250 / days) - 1) * 100 if days > 0 else 0
        
        # 最大回撤
        peak = values[0]
        max_drawdown = 0
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        # 胜率
        winning_trades = [t for t in self.trades if t['action'] == 'sell' and t['pnl'] > 0]
        total_trades = [t for t in self.trades if t['action'] == 'sell']
        win_rate = len(winning_trades) / len(total_trades) * 100 if total_trades else 0
        
        # 盈亏比
        total_profit = sum(t['pnl'] for t in winning_trades)
        total_loss = abs(sum(t['pnl'] for t in self.trades if t['action'] == 'sell' and t['pnl'] < 0))
        profit_loss_ratio = total_profit / total_loss if total_loss > 0 else 0
        
        # 夏普比率 (简化计算)
        if len(values) > 1:
            daily_returns = [(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))]
            avg_return = np.mean(daily_returns)
            std_return = np.std(daily_returns)
            sharpe_ratio = (avg_return / std_return) * np.sqrt(252) if std_return > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            '初始资金': self.initial_capital,
            '最终资金': values[-1],
            '总收益 (%)': round(total_return, 2),
            '年化收益 (%)': round(annual_return, 2),
            '最大回撤 (%)': round(max_drawdown, 2),
            '交易次数': len([t for t in self.trades if t['action'] == 'sell']),
            '胜率 (%)': round(win_rate, 2),
            '盈亏比': round(profit_loss_ratio, 2),
            '夏普比率': round(sharpe_ratio, 2),
            '交易明细': self.trades,
            '净值曲线': self.portfolio_values
        }
    
    def save_results(self, results: Dict, filepath: str):
        """保存回测结果"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存为 JSON
        with open(filepath, 'w', encoding='utf-8') as f:
            # 处理 datetime 对象
            def convert(obj):
                if isinstance(obj, datetime):
                    return obj.strftime('%Y-%m-%d')
                elif isinstance(obj, dict):
                    return {k: convert(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert(i) for i in obj]
                return obj
            
            json.dump(convert(results), f, ensure_ascii=False, indent=2)
        
        print(f"回测结果已保存：{filepath}")
    
    def generate_report(self, results: Dict) -> str:
        """生成回测报告"""
        report = []
        report.append("=" * 60)
        report.append("回测报告")
        report.append("=" * 60)
        report.append(f"初始资金：¥{results.get('初始资金', 0):,.2f}")
        report.append(f"最终资金：¥{results.get('最终资金', 0):,.2f}")
        report.append(f"总收益：{results.get('总收益 (%)', 0):.2f}%")
        report.append(f"年化收益：{results.get('年化收益 (%)', 0):.2f}%")
        report.append(f"最大回撤：{results.get('最大回撤 (%)', 0):.2f}%")
        report.append(f"交易次数：{results.get('交易次数', 0)}")
        report.append(f"胜率：{results.get('胜率 (%)', 0):.2f}%")
        report.append(f"盈亏比：{results.get('盈亏比', 0):.2f}")
        report.append(f"夏普比率：{results.get('夏普比率', 0):.2f}")
        report.append("=" * 60)
        
        return "\n".join(report)


# 测试
if __name__ == "__main__":
    engine = BacktestEngine(initial_capital=100000)
    
    print("测试回测框架...")
    
    # 创建模拟数据
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    kline_data = pd.DataFrame({
        '日期': dates.tolist() * 2,
        '代码': ['000001'] * 100 + ['000002'] * 100,
        '收盘': np.random.uniform(10, 15, 200),
        '开盘': np.random.uniform(9, 14, 200),
        '最高': np.random.uniform(11, 16, 200),
        '最低': np.random.uniform(8, 13, 200)
    })
    
    # 创建模拟信号
    signals = [
        {'date': '2024-01-05', 'stock_code': '000001', 'action': 'buy', 'quantity': 1000},
        {'date': '2024-01-15', 'stock_code': '000001', 'action': 'sell', 'quantity': 1000},
        {'date': '2024-01-10', 'stock_code': '000002', 'action': 'buy', 'quantity': 1000},
        {'date': '2024-01-20', 'stock_code': '000002', 'action': 'sell', 'quantity': 1000}
    ]
    
    results = engine.run_backtest(kline_data, signals)
    
    if results:
        print("\n" + engine.generate_report(results))
