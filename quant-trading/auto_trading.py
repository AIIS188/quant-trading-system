#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
盘中实时监控 + 模拟盘自动交易
整合实时策略和模拟盘执行

工作流程:
09:25  集合竞价监控
09:30  开盘，启动扫描
09:30-10:30  早盘突破策略
10:30-14:30  盘中回调策略
14:30-15:00  尾盘买入策略
15:00  收盘，生成报告
"""

import sys
import time
from datetime import datetime, time as dt_time
from pathlib import Path

# 添加路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from intraday_strategy import IntradayStrategy
from paper_trading import PaperTrading
from realtime_monitor import RealtimeMonitor
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/monitor_{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class AutoTradingSystem:
    """自动交易系统"""
    
    def __init__(self, capital=100000):
        self.strategy = IntradayStrategy(capital=capital)
        self.paper_trading = PaperTrading(initial_capital=capital)
        self.monitor = RealtimeMonitor()
        self.traded_stocks = set()  # 今日已交易股票
        self.daily_stats = {
            'total_trades': 0,
            'buy_count': 0,
            'sell_count': 0,
            'total_amount': 0
        }
        
        logger.info(f"自动交易系统初始化完成")
        logger.info(f"初始资金：{capital}元")
    
    def load_watch_list(self, symbols):
        """加载监控列表"""
        self.strategy.set_watch_list(symbols)
        logger.info(f"加载监控列表：{len(symbols)}只股票")
    
    def execute_buy(self, signal):
        """执行买入"""
        # 检查是否已交易过
        if signal.symbol in self.traded_stocks:
            logger.info(f"跳过 {signal.symbol}: 今日已交易")
            return False
        
        # 执行模拟买入
        success = self.paper_trading.buy(
            stock_code=signal.symbol,
            stock_name=signal.name,
            price=signal.price,
            quantity=signal.quantity,
            strategy=signal.strategy,
            signal_reason=signal.reason
        )
        
        if success:
            self.traded_stocks.add(signal.symbol)
            self.daily_stats['buy_count'] += 1
            self.daily_stats['total_trades'] += 1
            self.daily_stats['total_amount'] += signal.price * signal.quantity
            
            logger.info(f"✅ 买入：{signal.symbol} {signal.quantity}股 @ {signal.price:.2f}元")
            
            # 发送通知 (可添加飞书/邮件推送)
            self.send_notification(signal, 'buy')
            
            return True
        
        return False
    
    def execute_sell(self, signal):
        """执行卖出"""
        # 执行模拟卖出
        pnl = self.paper_trading.sell(
            stock_code=signal.symbol,
            price=signal.price
        )
        
        self.daily_stats['sell_count'] += 1
        self.daily_stats['total_trades'] += 1
        
        logger.info(f"✅ 卖出：{signal.symbol} @ {signal.price:.2f}元，盈亏：{pnl:.2f}元")
        
        self.send_notification(signal, 'sell')
        
        return True
    
    def send_notification(self, signal, action):
        """发送交易通知"""
        message = f"""
🔔 交易通知

股票：{signal.symbol} {signal.name}
动作：{'买入' if action == 'buy' else '卖出'}
策略：{signal.strategy}
价格：{signal.price:.2f}元
数量：{signal.quantity}股
时间：{datetime.now().strftime('%H:%M:%S')}
        """
        
        # 打印通知
        print(message)
        
        # TODO: 发送到飞书/微信/邮件
        # self.send_to_feishu(message)
        # self.send_email(message)
        
        logger.info("通知已发送")
    
    def scan_and_trade(self):
        """扫描并执行交易 v2.0 - 增加持仓监控"""
        logger.info("开始扫描交易机会...")
        
        # v2.0: 获取当前持仓用于监控 (转换为字典格式)
        positions = []
        for pos in self.paper_trading.positions:
            positions.append({
                'stock_code': pos.stock_code,
                'stock_name': pos.stock_name,
                'quantity': pos.quantity,
                'cost_price': pos.cost_price,
                'current_price': pos.current_price
            })
        
        # 获取信号 (包含买入和卖出)
        signals = self.strategy.scan_all(positions=positions)
        
        if not signals:
            logger.info("无交易信号")
            return
        
        logger.info(f"生成 {len(signals)} 个交易信号")
        
        # 执行交易
        for signal in signals:
            if signal.action == 'buy':
                self.execute_buy(signal)
            elif signal.action == 'sell':
                # v2.0: 卖出信号需要更新价格
                quote = self.strategy.fetcher.get_realtime_quote(signal.symbol)
                if quote:
                    signal.price = quote['price']
                self.execute_sell(signal)
    
    def print_daily_report(self):
        """打印每日报告"""
        print("\n" + "=" * 80)
        print("每日交易报告")
        print("=" * 80)
        
        # 模拟盘报告
        self.paper_trading.print_report()
        
        # 交易统计
        print(f"\n今日统计:")
        print(f"  交易次数：{self.daily_stats['total_trades']}")
        print(f"  买入：{self.daily_stats['buy_count']}笔")
        print(f"  卖出：{self.daily_stats['sell_count']}笔")
        print(f"  交易金额：{self.daily_stats['total_amount']:.2f}元")
        print(f"  监控股票：{len(self.traded_stocks)}只")
        
        print("=" * 80)
    
    def run(self, interval=300):
        """运行自动交易"""
        print("\n" + "=" * 80)
        print("A 股自动交易系统启动")
        print("=" * 80)
        print(f"初始资金：{self.paper_trading.initial_capital}元")
        print(f"监控列表：{len(self.strategy.monitor.watch_list)}只股票")
        print(f"扫描间隔：{interval}秒")
        print(f"当前时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"交易时段：{self.monitor.get_market_session()}")
        print("=" * 80)
        
        # 检查是否交易时间
        if not self.monitor.is_market_open():
            print("⚠️ 当前不是交易时间")
            print("   交易时间：09:30-11:30, 13:00-15:00")
            return
        
        logger.info("开始盘中自动交易...")
        
        try:
            while self.monitor.is_market_open():
                # 扫描并交易
                self.scan_and_trade()
                
                # 等待下次扫描
                next_scan = datetime.now().timestamp() + interval
                print(f"\n等待{interval}秒后下次扫描...")
                time.sleep(interval)
            
            # 收盘后生成报告
            print("\n市场已关闭，生成收盘报告...")
            self.print_daily_report()
            
            # 保存数据
            self.paper_trading._save_state()
            logger.info("数据已保存")
            
        except KeyboardInterrupt:
            print("\n停止交易...")
            self.print_daily_report()
            self.paper_trading._save_state()
    
    def run_once(self):
        """运行一次扫描"""
        self.scan_and_trade()


# 主程序
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='A 股自动交易系统')
    parser.add_argument('--capital', type=int, default=100000, help='初始资金')
    parser.add_argument('--interval', type=int, default=300, help='扫描间隔 (秒)')
    parser.add_argument('--once', action='store_true', help='只运行一次')
    parser.add_argument('--test', action='store_true', help='测试模式')
    
    args = parser.parse_args()
    
    # 创建系统
    system = AutoTradingSystem(capital=args.capital)
    
    # 设置监控列表 (龙头股)
    watch_list = [
        '000533',  # 顺钠股份
        '605268',  # 王力安防
        '600545',  # 卓郎智能
        '002498',  # 汉缆股份
        '600590',  # 泰豪科技
        '000001',  # 平安银行
        '000002',  # 万科 A
    ]
    
    system.load_watch_list(watch_list)
    
    if args.test:
        print("\n测试模式...")
        system.run_once()
    elif args.once:
        print("\n运行一次...")
        system.run_once()
    else:
        print("\n开始连续监控...")
        system.run(interval=args.interval)
