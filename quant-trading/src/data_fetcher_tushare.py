"""
数据获取模块 - Tushare Pro 版本
稳定可靠的 A 股数据源
"""

import tushare as ts
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import time

class TushareFetcher:
    """Tushare Pro 数据获取器"""
    
    def __init__(self, token, cache_dir="data/cache"):
        self.token = token
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # 初始化 tushare
        ts.set_token(token)
        self.pro = ts.pro_api()
        
        print(f"✅ Tushare 初始化成功")
        
        # 检查积分
        try:
            info = self.pro.user_info()
            if info is not None and not info.empty:
                points = info.iloc[0].get('points', 0)
                print(f"   用户积分：{points}")
                self._check_permission(points)
        except Exception as e:
            print(f"   ⚠️ 无法获取用户信息：{e}")
    
    def _check_permission(self, points):
        """检查权限"""
        # Tushare 权限说明
        # 基础积分：120 分可以获取基础数据
        # 更高积分可以获取更高级数据
        if points < 120:
            print(f"   ⚠️ 积分较低，部分数据可能无法访问")
        else:
            print(f"   ✅ 积分充足")
    
    def get_stock_list(self):
        """获取 A 股股票列表"""
        try:
            df = self.pro.stock_basic(
                exchange='',
                list_status='L',
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            return df
        except Exception as e:
            print(f"获取股票列表失败：{e}")
            return None
    
    def get_limit_up(self, date=None):
        """
        获取涨停板数据 - 使用 akshare (Tushare 限流)
        :param date: 日期，格式 YYYYMMDD
        """
        # Tushare 限流：每小时 1 次，改用 akshare
        return None  # 由统一接口的备用方案处理
    
    def get_limit_down(self, date=None):
        """获取跌停板数据"""
        # Tushare 限流，改用 akshare
        return None
    
    def get_longhu_list(self, date=None):
        """获取龙虎榜数据"""
        # Tushare 接口名问题，改用 akshare
        return None
    
    def get_sector_flow(self, date=None):
        """获取板块资金流向"""
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        try:
            # 行业资金流
            df = self.pro.moneyflow_industry(
                trade_date=date
            )
            return df
        except Exception as e:
            print(f"获取板块资金流失败：{e}")
            return None
    
    def get_north_flow(self, date=None):
        """获取北向资金流向"""
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.smbare_moneyflow(
                trade_date=date
            )
            return df
        except Exception as e:
            print(f"获取北向资金失败：{e}")
            return None
    
    def get_kline(self, symbol, period="daily", start_date=None, end_date=None, cache=True):
        """
        获取 K 线数据 (Tushare Pro)
        :param symbol: 股票代码 (如 000001 或 000001.SZ)
        :param period: 周期 (daily/weekly/monthly)
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        :param cache: 是否缓存
        """
        # 格式化股票代码
        if '.' not in symbol:
            if symbol.startswith('6'):
                symbol = f"{symbol}.SH"
            else:
                symbol = f"{symbol}.SZ"
        
        # 尝试缓存
        if cache:
            cache_file = f"kline_tushare_{symbol}_{period}_{start_date}_{end_date}.csv"
            cached = self.load_cache(cache_file)
            if cached is not None:
                return cached
        
        try:
            if period == "daily":
                df = self.pro.daily(
                    ts_code=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            elif period == "weekly":
                df = self.pro.weekly(
                    ts_code=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            elif period == "monthly":
                df = self.pro.monthly(
                    ts_code=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                df = self.pro.daily(
                    ts_code=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
            
            if df is not None and not df.empty:
                # 重命名列
                df = df.rename(columns={
                    'trade_date': '日期',
                    'open': '开盘',
                    'high': '最高',
                    'low': '最低',
                    'close': '收盘',
                    'vol': '成交量',
                    'amount': '成交额'
                })
                
                # 缓存
                if cache:
                    self.save_cache(df, cache_file)
                
                return df
            
            return None
        except Exception as e:
            # print(f"Tushare K 线失败：{e}")
            return None
    
    def get_realtime_quotes(self, symbols=None):
        """
        获取实时行情
        :param symbols: 股票代码列表
        """
        try:
            df = self.pro.quote_daily()
            if symbols:
                df = df[df['ts_code'].isin(symbols)]
            return df
        except Exception as e:
            print(f"获取实时行情失败：{e}")
            return None
    
    def get_turnover_rank(self, date=None):
        """获取换手率排行"""
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        try:
            df = self.pro.moneyflow(
                trade_date=date
            )
            if df is not None and not df.empty:
                df = df.sort_values('turnover_rate', ascending=False)
            return df
        except Exception as e:
            print(f"获取换手率排行失败：{e}")
            return None
    
    def get_stock_info(self, symbol):
        """获取股票基本信息"""
        try:
            df = self.pro.stock_basic(
                ts_code=symbol,
                fields='ts_code,symbol,name,area,industry,market,list_date'
            )
            return df
        except Exception as e:
            print(f"获取股票信息失败：{e}")
            return None
    
    def get_news(self, keyword="A 股", start_date=None, end_date=None):
        """获取财经新闻"""
        try:
            # Tushare 新闻接口
            df = self.pro.news(
                src="",
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            print(f"获取新闻失败：{e}")
            return None
    
    def save_cache(self, data, filename):
        """保存数据到缓存"""
        filepath = os.path.join(self.cache_dir, filename)
        if isinstance(data, pd.DataFrame):
            data.to_csv(filepath, index=False)
        else:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_cache(self, filename):
        """从缓存加载数据"""
        filepath = os.path.join(self.cache_dir, filename)
        if os.path.exists(filepath):
            if filename.endswith('.csv'):
                return pd.read_csv(filepath)
            else:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return None


# 测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = os.environ.get('TUSHARE_TOKEN', '')
    
    if not token:
        print("请提供 Tushare Token")
        sys.exit(1)
    
    fetcher = TushareFetcher(token)
    
    print("\n测试数据获取...")
    
    # 测试股票列表
    print("\n1. 股票列表...")
    stock_list = fetcher.get_stock_list()
    if stock_list is not None:
        print(f"   共 {len(stock_list)} 只股票")
        print(stock_list.head())
    
    # 测试涨停板
    print("\n2. 今日涨停...")
    limit_up = fetcher.get_limit_up()
    if limit_up is not None:
        print(f"   今日涨停 {len(limit_up)} 只")
        print(limit_up[['ts_code', 'name', 'close', 'change_pct']].head())
    
    # 测试 K 线
    print("\n3. K 线数据 (000001.SZ)...")
    kline = fetcher.get_kline('000001.SZ', period='daily', 
                              start_date='20240101', end_date='20240131')
    if kline is not None:
        print(f"   获取 {len(kline)} 条")
        print(kline.head())
