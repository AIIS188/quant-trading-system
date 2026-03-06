#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
资金流数据获取模块
- 板块资金流 (行业/概念)
- 北向资金流
- 个股资金流

数据源：Akshare (东方财富)
"""

import akshare as ak
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class FundFlowFetcher:
    """资金流数据获取器"""
    
    def __init__(self):
        self.last_update = None
    
    def get_industry_fund_flow(self, symbol: str = '即时') -> pd.DataFrame:
        """
        获取行业资金流数据
        
        Args:
            symbol: '即时' or '今日' or '3 日' or '5 日' or '10 日'
            
        Returns:
            DataFrame with columns: 序号，行业，行业指数，行业 - 涨跌幅，流入资金，流出资金，净额，公司家数，领涨股，领涨股 - 涨跌幅，当前价
        """
        try:
            logger.info(f"获取行业资金流数据，symbol={symbol}")
            data = ak.stock_fund_flow_industry(symbol=symbol)
            self.last_update = datetime.now()
            logger.info(f"成功获取行业资金流，共 {len(data)} 个行业")
            return data
        except Exception as e:
            logger.error(f"获取行业资金流失败：{e}")
            return pd.DataFrame()
    
    def get_concept_fund_flow(self, symbol: str = '即时') -> pd.DataFrame:
        """
        获取概念板块资金流数据
        
        Args:
            symbol: '即时' or '今日' or '3 日' or '5 日' or '10 日'
            
        Returns:
            DataFrame with columns: 序号，行业，行业指数，行业 - 涨跌幅，流入资金，流出资金，净额，公司家数，领涨股，领涨股 - 涨跌幅，当前价
        """
        try:
            logger.info(f"获取概念资金流数据，symbol={symbol}")
            data = ak.stock_fund_flow_concept(symbol=symbol)
            self.last_update = datetime.now()
            logger.info(f"成功获取概念资金流，共 {len(data)} 个概念")
            return data
        except Exception as e:
            logger.error(f"获取概念资金流失败：{e}")
            return pd.DataFrame()
    
    def get_north_fund_flow(self) -> pd.DataFrame:
        """
        获取北向资金汇总数据
        
        Returns:
            DataFrame with 沪股通/深股通 北向资金流向
        """
        try:
            logger.info("获取北向资金汇总数据")
            data = ak.stock_hsgt_fund_flow_summary_em()
            self.last_update = datetime.now()
            logger.info(f"成功获取北向资金汇总，共 {len(data)} 条记录")
            return data
        except Exception as e:
            logger.error(f"获取北向资金汇总失败：{e}")
            return pd.DataFrame()
    
    def get_north_flow_history(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        获取北向资金历史数据
        
        Args:
            start_date: 开始日期，格式 '20260306'
            end_date: 结束日期，格式 '20260306'
            
        Returns:
            北向资金历史流向数据
        """
        try:
            logger.info(f"获取北向资金历史数据，{start_date} to {end_date}")
            data = ak.stock_hsgt_hist_em(start_date=start_date, end_date=end_date)
            self.last_update = datetime.now()
            logger.info(f"成功获取北向资金历史数据，共 {len(data)} 条记录")
            return data
        except Exception as e:
            logger.error(f"获取北向资金历史数据失败：{e}")
            return pd.DataFrame()
    
    def get_individual_fund_flow(self, stock: str = '600094', market: str = 'sh') -> pd.DataFrame:
        """
        获取个股资金流数据
        
        Args:
            stock: 股票代码
            market: 'sh' or 'sz'
            
        Returns:
            个股资金流明细
        """
        try:
            logger.info(f"获取个股资金流，stock={stock}, market={market}")
            data = ak.stock_individual_fund_flow(stock=stock, market=market)
            self.last_update = datetime.now()
            logger.info(f"成功获取个股资金流")
            return data
        except Exception as e:
            logger.error(f"获取个股资金流失败：{e}")
            return pd.DataFrame()
    
    def get_top_fund_flow_stocks(self, indicator: str = '今日') -> pd.DataFrame:
        """
        获取资金流排行个股
        
        Args:
            indicator: '今日' or '3 日' or '5 日' or '10 日'
            
        Returns:
            资金流排行数据
        """
        try:
            logger.info(f"获取资金流排行个股，indicator={indicator}")
            data = ak.stock_individual_fund_flow_rank(indicator=indicator)
            self.last_update = datetime.now()
            logger.info(f"成功获取资金流排行，共 {len(data)} 只股票")
            return data
        except Exception as e:
            logger.error(f"获取资金流排行失败：{e}")
            return pd.DataFrame()
    
    def get_main_fund_flow(self, stock: str = '600094') -> pd.DataFrame:
        """
        获取个股主力资金流
        
        Args:
            stock: 股票代码
            
        Returns:
            主力资金流数据
        """
        try:
            logger.info(f"获取个股主力资金流，stock={stock}")
            data = ak.stock_main_fund_flow(stock=stock)
            self.last_update = datetime.now()
            logger.info(f"成功获取主力资金流")
            return data
        except Exception as e:
            logger.error(f"获取主力资金流失败：{e}")
            return pd.DataFrame()
    
    def get_top_industries(self, period: str = '即时', top_n: int = 10) -> pd.DataFrame:
        """
        获取净流入排名前 N 的行业
        
        Args:
            period: 时间周期
            top_n: 返回数量
            
        Returns:
            前 N 个行业
        """
        data = self.get_industry_fund_flow(symbol=period)
        if data.empty:
            return pd.DataFrame()
        return data.nlargest(top_n, '净额')
    
    def get_top_concepts(self, period: str = '即时', top_n: int = 10) -> pd.DataFrame:
        """
        获取净流入排名前 N 的概念
        
        Args:
            period: 时间周期
            top_n: 返回数量
            
        Returns:
            前 N 个概念
        """
        data = self.get_concept_fund_flow(symbol=period)
        if data.empty:
            return pd.DataFrame()
        return data.nlargest(top_n, '净额')
    
    def get_full_market_fund_flow(self) -> Dict[str, Any]:
        """
        获取全市场资金流概览
        
        Returns:
            包含行业、概念、北向资金的字典
        """
        logger.info("获取全市场资金流概览")
        
        result = {
            'timestamp': datetime.now().isoformat(),
            'industry': self.get_industry_fund_flow(symbol='即时'),
            'concept': self.get_concept_fund_flow(symbol='即时'),
            'north': self.get_north_fund_flow(),
        }
        
        # 计算净流入排行
        if not result['industry'].empty:
            result['industry_top'] = result['industry'].nlargest(10, '净额')
            result['industry_bottom'] = result['industry'].nsmallest(10, '净额')
        
        if not result['concept'].empty:
            result['concept_top'] = result['concept'].nlargest(10, '净额')
            result['concept_bottom'] = result['concept'].nsmallest(10, '净额')
        
        logger.info("全市场资金流概览完成")
        return result
    
    def analyze_market_sentiment(self) -> Dict[str, Any]:
        """
        分析市场情绪 (基于资金流)
        
        Returns:
            情绪分析结果
        """
        industry = self.get_industry_fund_flow(symbol='即时')
        concept = self.get_concept_fund_flow(symbol='即时')
        north = self.get_north_fund_flow()
        
        sentiment = {
            'timestamp': datetime.now().isoformat(),
            'industry_stats': {},
            'concept_stats': {},
            'north_sentiment': 'neutral',
            'overall_score': 50,
        }
        
        if not industry.empty:
            net_inflow = industry['净额'].sum()
            up_count = len(industry[industry['净额'] > 0])
            sentiment['industry_stats'] = {
                'total_net_inflow': float(net_inflow),
                'up_industries': up_count,
                'down_industries': len(industry) - up_count,
                'up_ratio': round(up_count / len(industry) * 100, 2),
            }
        
        if not concept.empty:
            net_inflow = concept['净额'].sum()
            up_count = len(concept[concept['净额'] > 0])
            sentiment['concept_stats'] = {
                'total_net_inflow': float(net_inflow),
                'up_concepts': up_count,
                'down_concepts': len(concept) - up_count,
                'up_ratio': round(up_count / len(concept) * 100, 2),
            }
        
        # 北向资金情绪
        if not north.empty:
            north_net = north['资金净流入'].sum()
            if north_net > 50:
                sentiment['north_sentiment'] = 'bullish'
            elif north_net < -50:
                sentiment['north_sentiment'] = 'bearish'
            else:
                sentiment['north_sentiment'] = 'neutral'
        
        # 计算综合情绪得分 (0-100)
        score = 50
        if 'industry_stats' in sentiment and sentiment['industry_stats']:
            score += (sentiment['industry_stats']['up_ratio'] - 50) * 0.3
        if 'concept_stats' in sentiment and sentiment['concept_stats']:
            score += (sentiment['concept_stats']['up_ratio'] - 50) * 0.3
        if sentiment['north_sentiment'] == 'bullish':
            score += 10
        elif sentiment['north_sentiment'] == 'bearish':
            score -= 10
        
        sentiment['overall_score'] = round(max(0, min(100, score)), 2)
        
        return sentiment


def test_fund_flow():
    """测试资金流数据获取模块"""
    fetcher = FundFlowFetcher()
    
    print("=" * 60)
    print("测试资金流数据获取模块")
    print("=" * 60)
    
    # 1. 行业资金流
    print("\n【1】行业资金流 (即时)")
    industry = fetcher.get_industry_fund_flow(symbol='即时')
    if not industry.empty:
        print(f"共 {len(industry)} 个行业")
        print("净流入前 5 行业:")
        print(industry.iloc[:, [1, 6, 3]].head())  # 行业，净额，行业 - 涨跌幅
    
    # 2. 概念资金流
    print("\n【2】概念资金流 (即时)")
    concept = fetcher.get_concept_fund_flow(symbol='即时')
    if not concept.empty:
        print(f"共 {len(concept)} 个概念")
        print("净流入前 5 概念:")
        print(concept.iloc[:, [1, 6, 3]].head())  # 行业，净额，行业 - 涨跌幅
    
    # 3. 北向资金
    print("\n【3】北向资金汇总")
    north = fetcher.get_north_fund_flow()
    if not north.empty:
        print(north[['交易日', '板块', '资金方向', '资金净流入']].to_string())
    
    # 4. 资金流排行
    print("\n【4】个股资金流排行 (今日)")
    rank = fetcher.get_top_fund_flow_stocks(indicator='今日')
    if not rank.empty:
        print(f"共 {len(rank)} 只股票")
        print("净流入前 5:")
        # 根据实际列名调整
        cols = rank.columns.tolist()
        print(cols)
        print(rank.head())
    
    # 5. 市场情绪分析
    print("\n【5】市场情绪分析")
    sentiment = fetcher.analyze_market_sentiment()
    print(f"情绪得分：{sentiment['overall_score']}")
    print(f"北向情绪：{sentiment['north_sentiment']}")
    if sentiment.get('industry_stats'):
        print(f"行业上涨比例：{sentiment['industry_stats']['up_ratio']}%")
    
    print("\n" + "=" * 60)
    print("测试完成!")
    print("=" * 60)
    
    return fetcher


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    test_fund_flow()
