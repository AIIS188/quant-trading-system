"""
数据获取模块 - 市场扫描
负责获取 A 股市场各类数据
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import time
import random

class DataFetcher:
    """A 股市场数据获取器"""
    
    def __init__(self, cache_dir="data/cache", max_retries=3, retry_delay=2):
        self.cache_dir = cache_dir
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        os.makedirs(cache_dir, exist_ok=True)
    
    def _fetch_with_retry(self, func, *args, **kwargs):
        """带重试的数据获取"""
        for i in range(self.max_retries):
            try:
                result = func(*args, **kwargs)
                # 短暂延迟，避免触发限流
                time.sleep(random.uniform(0.5, 1.5))
                return result
            except Exception as e:
                if i < self.max_retries - 1:
                    # print(f"重试 {i+1}/{self.max_retries}: {e}")
                    time.sleep(self.retry_delay * (i + 1))
                else:
                    return None
        return None
    
    def get_stock_list(self):
        """获取 A 股股票列表"""
        try:
            df = ak.stock_info_a_code_name()
            return df
        except Exception as e:
            print(f"获取股票列表失败：{e}")
            return None
    
    def get_limit_up(self, date=None):
        """
        获取涨停板数据
        :param date: 日期，格式 YYYYMMDD，默认今天
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        try:
            df = ak.stock_zt_pool_em(date=date)
            return df
        except Exception as e:
            print(f"获取涨停板数据失败：{e}")
            return None
    
    def get_limit_down(self, date=None):
        """获取跌停板数据"""
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        try:
            # 尝试不同的 API 名称
            df = ak.stock_zt_pool_dtgc_em(date=date)
            return df
        except Exception as e:
            # print(f"获取跌停板数据失败：{e}")
            return None
    
    def get_longhu_list(self, date=None):
        """
        获取龙虎榜数据
        :param date: 日期，格式 YYYYMMDD
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        try:
            # 使用正确的 API (不带 date 参数)
            df = ak.stock_lhb_detail_em()
            return df
        except Exception as e:
            # print(f"获取龙虎榜数据失败：{e}")
            return None
    
    def get_sector_flow(self):
        """获取板块资金流向"""
        try:
            df = ak.stock_board_industry_name_em()
            return df
        except Exception as e:
            # print(f"获取板块资金流失败：{e}")
            return None
    
    def get_turnover_rank(self, date=None):
        """
        获取换手率排行
        :param date: 日期，格式 YYYYMMDD
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        try:
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="个股")
            return df
        except Exception as e:
            print(f"获取换手率排行失败：{e}")
            return None
    
    def get_north_flow(self, date=None):
        """
        获取北向资金流向
        :param date: 日期，格式 YYYYMMDD
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")
        try:
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北向资金")
            return df
        except Exception as e:
            print(f"获取北向资金失败：{e}")
            return None
    
    def get_stock_info(self, symbol):
        """获取个股基本信息"""
        try:
            df = ak.stock_individual_info_em(symbol=symbol)
            return df
        except Exception as e:
            print(f"获取股票信息失败：{e}")
            return None
    
    def get_realtime_quotes(self, symbol):
        """获取实时行情"""
        try:
            df = ak.stock_zh_a_spot_em()
            if symbol:
                df = df[df['代码'] == symbol]
            return df
        except Exception as e:
            print(f"获取实时行情失败：{e}")
            return None
    
    def get_kline(self, symbol, period="daily", start_date=None, end_date=None, cache=True):
        """
        获取 K 线数据 - 使用新浪财经 API
        :param symbol: 股票代码
        :param period: 周期 (daily/weekly/monthly)
        :param start_date: 开始日期 YYYYMMDD (暂不支持，返回最近 N 条)
        :param end_date: 结束日期 YYYYMMDD (暂不支持)
        :param cache: 是否使用缓存
        """
        # 尝试从缓存加载
        if cache:
            cache_file = f"kline_{symbol}_{period}.csv"
            cached = self.load_cache(cache_file)
            if cached is not None:
                return cached
        
        # 使用新浪财经 API
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent))
        from data_fetcher_sina import SinaKLineFetcher
        sina_fetcher = SinaKLineFetcher(max_retries=3, retry_delay=1)
        
        if period == "daily":
            df = sina_fetcher.get_daily_kline(symbol, count=100)
        elif period == "weekly":
            df = sina_fetcher.get_weekly_kline(symbol, count=100)
        else:
            df = sina_fetcher.get_daily_kline(symbol, count=100)
        
        # 保存到缓存
        if df is not None and cache:
            self.save_cache(df, cache_file)
        
        return df
    
    def get_news(self, keyword="A 股", start_date=None, end_date=None):
        """获取财经新闻"""
        try:
            df = ak.stock_news_em(symbol=keyword)
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
    fetcher = DataFetcher()
    print("测试数据获取模块...")
    
    # 获取股票列表
    print("\n1. 获取 A 股股票列表...")
    stock_list = fetcher.get_stock_list()
    if stock_list is not None:
        print(f"   共 {len(stock_list)} 只股票")
        print(stock_list.head())
    
    # 获取涨停板
    print("\n2. 获取今日涨停板...")
    limit_up = fetcher.get_limit_up()
    if limit_up is not None:
        print(f"   今日涨停 {len(limit_up)} 只")
        print(limit_up[['代码', '名称', '最新价', '涨跌幅', '封板资金']].head())
    
    print("\n数据获取测试完成!")
