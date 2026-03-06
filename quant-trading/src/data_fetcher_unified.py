"""
统一数据获取接口
自动选择 Tushare 或 akshare
"""

import os
from pathlib import Path

class UnifiedDataFetcher:
    """统一数据获取器 - 混合使用 Tushare + 新浪财经 + akshare"""
    
    def __init__(self, tushare_token=None, cache_dir="data/cache"):
        self.tushare_token = tushare_token or os.environ.get('TUSHARE_TOKEN', '')
        self.cache_dir = cache_dir
        self.use_tushare = False
        self.tushare = None
        self.akshare = None
        
        # 尝试初始化 Tushare (用于 K 线等基础数据)
        if self.tushare_token:
            try:
                from data_fetcher_tushare import TushareFetcher
                self.tushare = TushareFetcher(self.tushare_token, cache_dir=cache_dir)
                # 测试日线数据
                test = self.tushare.get_kline('000001.SZ', period='daily', start_date='20240101', end_date='20240110')
                if test is not None and len(test) > 0:
                    self.use_tushare = True
                    print("✅ Tushare Pro 已启用 (K 线数据)")
                else:
                    print("⚠️ Tushare 测试失败")
            except Exception as e:
                print(f"⚠️ Tushare 不可用：{e}")
        
        # 初始化 akshare (用于涨停板、龙虎榜等)
        try:
            from data_fetcher import DataFetcher
            self.akshare = DataFetcher(cache_dir=cache_dir, max_retries=3, retry_delay=2)
            print("✅ akshare 已启用 (涨停板/龙虎榜)")
        except Exception as e:
            print(f"⚠️ akshare 初始化失败：{e}")
        
        # 总结
        if self.use_tushare:
            print("📊 数据源：Tushare(K 线) + akshare(市场数据)")
        elif self.akshare:
            print("📊 数据源：akshare + 新浪财经 (K 线)")
    
    def _call(self, tushare_method, akshare_method, *args, **kwargs):
        """调用方法，优先 Tushare"""
        if self.use_tushare and self.tushare:
            try:
                method = getattr(self.tushare, tushare_method)
                return method(*args, **kwargs)
            except Exception as e:
                # print(f"Tushare {tushare_method} 失败，尝试 akshare: {e}")
                pass
        
        if self.akshare:
            try:
                method = getattr(self.akshare, akshare_method)
                return method(*args, **kwargs)
            except Exception as e:
                # print(f"akshare {akshare_method} 失败：{e}")
                pass
        
        return None
    
    def get_stock_list(self):
        """获取股票列表"""
        return self._call('get_stock_list', 'get_stock_list')
    
    def get_limit_up(self, date=None):
        """获取涨停板 - 只用 akshare (Tushare 限流)"""
        if self.akshare:
            return self.akshare.get_limit_up(date)
        return None
    
    def get_limit_down(self, date=None):
        """获取跌停板 - 只用 akshare"""
        if self.akshare:
            return self.akshare.get_limit_down(date)
        return None
    
    def get_longhu_list(self, date=None):
        """获取龙虎榜 - 只用 akshare"""
        if self.akshare:
            return self.akshare.get_longhu_list(date)
        return None
    
    def get_sector_flow(self, date=None):
        """获取板块资金流"""
        return self._call('get_sector_flow', 'get_sector_flow', date)
    
    def get_north_flow(self, date=None):
        """获取北向资金"""
        return self._call('get_north_flow', 'get_north_flow', date)
    
    def get_kline(self, symbol, period="daily", start_date=None, end_date=None, cache=True):
        """获取 K 线数据 - 优先 Tushare"""
        if self.use_tushare and self.tushare:
            df = self.tushare.get_kline(symbol, period, start_date, end_date, cache)
            if df is not None:
                return df
        
        # Tushare 失败时用新浪财经
        if self.akshare:
            return self.akshare.get_kline(symbol, period, start_date, end_date, cache)
        
        return None
    
    def get_realtime_quotes(self, symbols=None):
        """获取实时行情"""
        return self._call('get_realtime_quotes', 'get_realtime_quotes', symbols)
    
    def get_turnover_rank(self, date=None):
        """获取换手率排行"""
        return self._call('get_turnover_rank', 'get_turnover_rank', date)
    
    def get_stock_info(self, symbol):
        """获取股票信息"""
        return self._call('get_stock_info', 'get_stock_info', symbol)
    
    def save_cache(self, data, filename):
        """保存缓存"""
        if self.use_tushare and self.tushare:
            self.tushare.save_cache(data, filename)
        elif self.akshare:
            self.akshare.save_cache(data, filename)
    
    def load_cache(self, filename):
        """加载缓存"""
        if self.use_tushare and self.tushare:
            return self.tushare.load_cache(filename)
        elif self.akshare:
            return self.akshare.load_cache(filename)
        return None


# 测试
if __name__ == "__main__":
    fetcher = UnifiedDataFetcher()
    
    print("\n测试统一接口...")
    
    print("\n1. 涨停板...")
    limit_up = fetcher.get_limit_up()
    if limit_up is not None:
        print(f"   ✅ {len(limit_up)} 只")
    
    print("\n2. K 线数据 (000001)...")
    kline = fetcher.get_kline('000001', period='daily', 
                              start_date='20240101', end_date='20240110')
    if kline is not None:
        print(f"   ✅ {len(kline)} 条")
        print(kline[['日期', '开盘', '最高', '最低', '收盘']].head())
