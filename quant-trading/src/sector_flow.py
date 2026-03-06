"""
板块资金流 - 同花顺 API
"""

import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


class SectorFlowFetcher:
    """板块资金流获取器"""
    
    def __init__(self):
        self.base_url = "http://data.10jqka.com.cn/funds/hyzjl/"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'http://data.10jqka.com.cn/funds/hyzjl/'
        }
    
    def get_sector_flow(self):
        """
        获取行业资金流数据
        :return: DataFrame
        """
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15)
            
            if resp.status_code != 200:
                return None
            
            # 解析 HTML
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # 查找表格
            table = soup.find('table', {'id': 'h2h-table'})
            if not table:
                # 尝试其他表格
                table = soup.find('table')
            
            if not table:
                return None
            
            # 解析表格数据
            rows = []
            tbody = table.find('tbody')
            if tbody:
                trs = tbody.find_all('tr')
            else:
                trs = table.find_all('tr')[1:]  # 跳过表头
            
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) >= 5:
                    try:
                        row = {
                            '排名': tds[0].get_text(strip=True),
                            '行业': tds[1].get_text(strip=True),
                            '涨跌幅': tds[2].get_text(strip=True).replace('%', ''),
                            '流入资金': tds[3].get_text(strip=True),
                            '流出资金': tds[4].get_text(strip=True),
                        }
                        
                        # 如果有净额字段
                        if len(tds) >= 6:
                            row['净额'] = tds[5].get_text(strip=True)
                        
                        # 转换数值
                        for key in ['涨跌幅']:
                            try:
                                row[key] = float(row[key]) if row[key] else 0
                            except:
                                row[key] = 0
                        
                        rows.append(row)
                    except Exception as e:
                        continue
            
            if not rows:
                return None
            
            df = pd.DataFrame(rows)
            return df
            
        except Exception as e:
            # print(f"获取板块资金流失败：{e}")
            return None
    
    def get_concept_flow(self):
        """
        获取概念板块资金流
        :return: DataFrame
        """
        try:
            url = "http://data.10jqka.com.cn/funds/gnzjl/"
            resp = requests.get(url, headers=self.headers, timeout=15)
            
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            table = soup.find('table')
            
            if not table:
                return None
            
            rows = []
            tbody = table.find('tbody')
            if tbody:
                trs = tbody.find_all('tr')
            else:
                trs = table.find_all('tr')[1:]
            
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) >= 5:
                    row = {
                        '排名': tds[0].get_text(strip=True),
                        '概念': tds[1].get_text(strip=True),
                        '涨跌幅': tds[2].get_text(strip=True).replace('%', ''),
                        '流入资金': tds[3].get_text(strip=True),
                        '流出资金': tds[4].get_text(strip=True),
                    }
                    
                    try:
                        row['涨跌幅'] = float(row['涨跌幅']) if row['涨跌幅'] else 0
                    except:
                        row['涨跌幅'] = 0
                    
                    rows.append(row)
            
            if not rows:
                return None
            
            df = pd.DataFrame(rows)
            return df
            
        except Exception as e:
            return None


# 测试
if __name__ == "__main__":
    fetcher = SectorFlowFetcher()
    
    print("测试板块资金流...")
    print("=" * 60)
    
    # 行业资金流
    print("\n1. 行业资金流...")
    df = fetcher.get_sector_flow()
    if df is not None and len(df) > 0:
        print(f"   ✅ 成功：{len(df)}个行业")
        print(f"   字段：{list(df.columns)}")
        print(f"\n   前 5 行业:")
        print(df[['行业', '涨跌幅', '流入资金', '流出资金']].head().to_string())
    else:
        print("   ❌ 获取失败")
    
    # 概念资金流
    print("\n2. 概念资金流...")
    df = fetcher.get_concept_flow()
    if df is not None and len(df) > 0:
        print(f"   ✅ 成功：{len(df)}个概念")
        print(f"\n   前 5 概念:")
        print(df.head().to_string())
    else:
        print("   ❌ 获取失败")
    
    print("\n" + "=" * 60)
