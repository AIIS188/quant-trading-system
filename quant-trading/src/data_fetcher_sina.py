"""
K 线数据获取 - 新浪财经 API
稳定可靠的 HTTP 接口
"""

import requests
import pandas as pd
from datetime import datetime
import time
import random


class SinaKLineFetcher:
    """新浪财经 K 线数据获取器"""
    
    def __init__(self, max_retries=3, retry_delay=1):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.base_url = "http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData"
    
    def _fetch_with_retry(self, url, params):
        """带重试的 HTTP 请求"""
        for i in range(self.max_retries):
            try:
                resp = requests.get(url, params=params, timeout=15)
                if resp.status_code == 200:
                    return resp.json()
                time.sleep(self.retry_delay * (i + 1))
            except Exception as e:
                if i < self.max_retries - 1:
                    time.sleep(self.retry_delay * (i + 1))
                else:
                    raise e
        return None
    
    def get_daily_kline(self, symbol: str, count=100) -> pd.DataFrame:
        """
        获取日线数据
        :param symbol: 股票代码 (如 000001)
        :param count: 获取条数 (最多 100)
        :return: DataFrame
        """
        # 格式化股票代码
        if symbol.startswith('6'):
            # 上交所
            stock_code = f"sh{symbol}"
        else:
            # 深交所
            stock_code = f"sz{symbol}"
        
        params = {
            'symbol': stock_code,
            'scale': 240,  # 日线
            'ma': 'no',
            'datalen': min(count, 100)
        }
        
        try:
            data = self._fetch_with_retry(self.base_url, params)
            
            if data and len(data) > 0:
                # 转换为 DataFrame
                df = pd.DataFrame(data)
                
                # 重命名列
                df = df.rename(columns={
                    'day': '日期',
                    'open': '开盘',
                    'high': '最高',
                    'low': '最低',
                    'close': '收盘',
                    'volume': '成交量'
                })
                
                # 转换数据类型
                df['日期'] = pd.to_datetime(df['日期'])
                numeric_cols = ['开盘', '最高', '最低', '收盘', '成交量']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 添加成交额估算 (收盘 * 成交量)
                df['成交额'] = df['收盘'] * df['成交量']
                
                # 添加换手率 (需要流通股本，这里先估算)
                # df['换手率'] = df['成交量'] / float_shares * 100
                
                return df
            else:
                return None
                
        except Exception as e:
            print(f"获取 K 线失败 ({symbol}): {e}")
            return None
    
    def get_weekly_kline(self, symbol: str, count=100) -> pd.DataFrame:
        """获取周线数据"""
        if symbol.startswith('6'):
            stock_code = f"sh{symbol}"
        else:
            stock_code = f"sz{symbol}"
        
        params = {
            'symbol': stock_code,
            'scale': 241,  # 周线
            'ma': 'no',
            'datalen': min(count, 100)
        }
        
        try:
            data = self._fetch_with_retry(self.base_url, params)
            
            if data and len(data) > 0:
                df = pd.DataFrame(data)
                df = df.rename(columns={
                    'day': '日期',
                    'open': '开盘',
                    'high': '最高',
                    'low': '最低',
                    'close': '收盘',
                    'volume': '成交量'
                })
                
                df['日期'] = pd.to_datetime(df['日期'])
                numeric_cols = ['开盘', '最高', '最低', '收盘', '成交量']
                for col in numeric_cols:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                return df
            else:
                return None
                
        except Exception as e:
            print(f"获取周线失败 ({symbol}): {e}")
            return None
    
    def get_batch_kline(self, symbols: list, count=100, delay=0.5) -> dict:
        """
        批量获取 K 线数据
        :param symbols: 股票代码列表
        :param count: 每只股票获取条数
        :param delay: 请求间隔 (秒)
        :return: {symbol: DataFrame}
        """
        results = {}
        
        for i, symbol in enumerate(symbols):
            if i > 0:
                time.sleep(delay + random.uniform(0, 0.5))
            
            df = self.get_daily_kline(symbol, count)
            if df is not None:
                results[symbol] = df
        
        return results


# 测试
if __name__ == "__main__":
    fetcher = SinaKLineFetcher()
    
    print("测试新浪财经 K 线数据...")
    print("=" * 60)
    
    # 测试单只股票
    print("\n1. 单只股票 (000001)...")
    df = fetcher.get_daily_kline('000001', count=30)
    if df is not None:
        print(f"   ✅ 获取 {len(df)} 条")
        print(f"   字段：{list(df.columns)}")
        print(f"\n   最近 5 日:")
        print(df[['日期', '开盘', '最高', '最低', '收盘', '成交量']].tail(5).to_string())
    
    # 测试批量
    print("\n2. 批量获取 (5 只股票)...")
    symbols = ['000001', '000002', '600519', '000858', '002415']
    results = fetcher.get_batch_kline(symbols, count=10, delay=0.3)
    
    print(f"   成功：{len(results)}/{len(symbols)}")
    for symbol, df in results.items():
        print(f"   • {symbol}: {len(df)} 条")
    
    print("\n" + "=" * 60)
