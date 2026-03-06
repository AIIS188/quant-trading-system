#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
聚宽 JoinQuant API 集成模块
用于真实模拟盘交易

使用前需要:
1. 注册聚宽账号：https://www.joinquant.com/
2. 开通量化交易权限
3. 获取 API 用户名和密码
"""

import jqdatasdk
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class JoinQuantTrader:
    """聚宽量化交易接口"""
    
    def __init__(self, username: str = None, password: str = None):
        """
        初始化聚宽接口
        
        Args:
            username: 聚宽用户名 (手机号)
            password: 聚宽密码
        """
        self.username = username
        self.password = password
        self.is_authenticated = False
        self.account_id = None
        
        # 如果提供了凭证，自动认证
        if username and password:
            self.authenticate(username, password)
    
    def authenticate(self, username: str, password: str) -> bool:
        """
        认证登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            是否成功
        """
        try:
            jqdatasdk.auth(username, password)
            self.is_authenticated = True
            self.username = username
            logger.info("聚宽认证成功!")
            return True
        except Exception as e:
            logger.error(f"聚宽认证失败：{e}")
            self.is_authenticated = False
            return False
    
    def get_realtime_price(self, symbol: str) -> Optional[float]:
        """
        获取实时价格
        
        Args:
            symbol: 股票代码 (如 000533)
            
        Returns:
            实时价格
        """
        if not self.is_authenticated:
            logger.error("未认证")
            return None
        
        try:
            # 格式化股票代码
            if symbol.startswith('6'):
                stock_id = f"{symbol}.SH"
            else:
                stock_id = f"{symbol}.SZ"
            
            # 获取实时行情
            df = jqdatasdk.get_price(stock_id, count=1, fields=['close'])
            
            if df is not None and len(df) > 0:
                price = df['close'].iloc[-1]
                return float(price)
            
            return None
        except Exception as e:
            logger.error(f"获取价格失败 ({symbol}): {e}")
            return None
    
    def get_kline(self, symbol: str, count=60, frequency='daily') -> pd.DataFrame:
        """
        获取 K 线数据
        
        Args:
            symbol: 股票代码
            count: 数据条数
            frequency: 频率 (1m/5m/15m/30m/60m/120m/daily/weekly/monthly)
            
        Returns:
            K 线数据 DataFrame
        """
        if not self.is_authenticated:
            logger.error("未认证")
            return pd.DataFrame()
        
        try:
            if symbol.startswith('6'):
                stock_id = f"{symbol}.SH"
            else:
                stock_id = f"{symbol}.SZ"
            
            df = jqdatasdk.get_price(stock_id, count=count, frequency=frequency)
            return df
        except Exception as e:
            logger.error(f"获取 K 线失败 ({symbol}): {e}")
            return pd.DataFrame()
    
    def get_positions(self) -> List[Dict]:
        """
        获取持仓列表
        
        Returns:
            持仓列表
        """
        if not self.is_authenticated:
            logger.error("未认证")
            return []
        
        try:
            # 获取持仓
            positions = jqdatasdk.get_positions()
            
            result = []
            for pos in positions:
                result.append({
                    'symbol': pos.sec_code,
                    'name': '',  # 需要额外获取
                    'quantity': pos.total_amount,
                    'available_quantity': pos.available_amount,
                    'cost_basis': pos.avg_cost,
                    'current_price': pos.last_sale_price,
                    'pnl': pos.pnl
                })
            
            return result
        except Exception as e:
            logger.error(f"获取持仓失败：{e}")
            return []
    
    def get_account_info(self) -> Dict:
        """
        获取账户信息
        
        Returns:
            账户信息
        """
        if not self.is_authenticated:
            logger.error("未认证")
            return {}
        
        try:
            account = jqdatasdk.get_account_info()
            
            return {
                'total_value': account.total_value,
                'cash': account.cash,
                'positions_value': account.positions_value,
                'pnl': account.pnl,
                'pnl_ratio': account.pnl_ratio
            }
        except Exception as e:
            logger.error(f"获取账户信息失败：{e}")
            return {}
    
    def order_buy(self, symbol: str, quantity: int, price: float = None) -> bool:
        """
        买入订单
        
        Args:
            symbol: 股票代码
            quantity: 数量 (股)
            price: 价格 (可选，市价单为 None)
            
        Returns:
            是否成功
        """
        if not self.is_authenticated:
            logger.error("未认证")
            return False
        
        try:
            if symbol.startswith('6'):
                stock_id = f"{symbol}.SH"
            else:
                stock_id = f"{symbol}.SZ"
            
            # 市价单
            if price is None:
                order_result = jqdatasdk.order(stock_id, quantity)
            else:
                # 限价单
                order_result = jqdatasdk.order_limit(stock_id, quantity, price)
            
            logger.info(f"买入订单：{symbol} {quantity}股 @ {price or '市价'}")
            return order_result is not None
        except Exception as e:
            logger.error(f"买入失败 ({symbol}): {e}")
            return False
    
    def order_sell(self, symbol: str, quantity: int, price: float = None) -> bool:
        """
        卖出订单
        
        Args:
            symbol: 股票代码
            quantity: 数量 (股)
            price: 价格 (可选)
            
        Returns:
            是否成功
        """
        if not self.is_authenticated:
            logger.error("未认证")
            return False
        
        try:
            if symbol.startswith('6'):
                stock_id = f"{symbol}.SH"
            else:
                stock_id = f"{symbol}.SZ"
            
            # 卖出数量为负数
            if price is None:
                order_result = jqdatasdk.order(stock_id, -quantity)
            else:
                order_result = jqdatasdk.order_limit(stock_id, -quantity, price)
            
            logger.info(f"卖出订单：{symbol} {quantity}股 @ {price or '市价'}")
            return order_result is not None
        except Exception as e:
            logger.error(f"卖出失败 ({symbol}): {e}")
            return False
    
    def order_target(self, symbol: str, target_value: float) -> bool:
        """
        目标仓位订单
        
        Args:
            symbol: 股票代码
            target_value: 目标市值 (元)
            
        Returns:
            是否成功
        """
        if not self.is_authenticated:
            logger.error("未认证")
            return False
        
        try:
            if symbol.startswith('6'):
                stock_id = f"{symbol}.SH"
            else:
                stock_id = f"{symbol}.SZ"
            
            order_result = jqdatasdk.order_target_value(stock_id, target_value)
            logger.info(f"目标仓位：{symbol} 目标市值{target_value}元")
            return order_result is not None
        except Exception as e:
            logger.error(f"目标仓位失败 ({symbol}): {e}")
            return False
    
    def get_order_history(self, days=1) -> List[Dict]:
        """
        获取订单历史
        
        Args:
            days: 天数
            
        Returns:
            订单历史列表
        """
        if not self.is_authenticated:
            logger.error("未认证")
            return []
        
        try:
            orders = jqdatasdk.get_orders(order_id=None, days=days)
            
            result = []
            for order in orders:
                result.append({
                    'order_id': order.order_id,
                    'symbol': order.sec_code,
                    'action': 'buy' if order.amount > 0 else 'sell',
                    'quantity': abs(order.amount),
                    'price': order.price,
                    'status': order.status,
                    'time': order.time
                })
            
            return result
        except Exception as e:
            logger.error(f"获取订单历史失败：{e}")
            return []
    
    def print_account_status(self):
        """打印账户状态"""
        if not self.is_authenticated:
            print("未认证")
            return
        
        account = self.get_account_info()
        positions = self.get_positions()
        
        print("\n" + "=" * 60)
        print("聚宽账户状态")
        print("=" * 60)
        print(f"总资产：{account.get('total_value', 0):.2f}元")
        print(f"可用资金：{account.get('cash', 0):.2f}元")
        print(f"持仓市值：{account.get('positions_value', 0):.2f}元")
        print(f"总盈亏：{account.get('pnl', 0):.2f}元 ({account.get('pnl_ratio', 0)*100:.2f}%)")
        
        if positions:
            print(f"\n持仓 ({len(positions)}只):")
            for pos in positions:
                print(f"  {pos['symbol']}: {pos['quantity']}股，盈亏{pos['pnl']:.2f}元")
        
        print("=" * 60)


# 测试
if __name__ == "__main__":
    print("=" * 60)
    print("聚宽 JoinQuant API 测试")
    print("=" * 60)
    
    # 提示用户输入凭证
    print("\n请输入聚宽账号信息:")
    username = input("用户名 (手机号): ").strip()
    password = input("密码：").strip()
    
    if not username or not password:
        print("❌ 未输入账号信息")
        print("\n提示:")
        print("1. 访问 https://www.joinquant.com/ 注册账号")
        print("2. 开通量化交易权限")
        print("3. 获取 API 凭证")
        exit(1)
    
    # 创建交易接口
    trader = JoinQuantTrader(username, password)
    
    if not trader.is_authenticated:
        print("❌ 认证失败，请检查账号密码")
        exit(1)
    
    print("\n✅ 认证成功!")
    
    # 测试获取账户信息
    print("\n【1】测试账户信息...")
    trader.print_account_status()
    
    # 测试获取价格
    print("\n【2】测试获取价格...")
    test_stocks = ['000533', '605268', '000001']
    for symbol in test_stocks:
        price = trader.get_realtime_price(symbol)
        if price:
            print(f"  {symbol}: {price:.2f}元")
        else:
            print(f"  {symbol}: 获取失败")
    
    # 测试获取 K 线
    print("\n【3】测试获取 K 线...")
    kline = trader.get_kline('000533', count=10)
    if kline is not None and len(kline) > 0:
        print(f"  000533: {len(kline)}条数据")
        print(kline.tail(3))
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)
