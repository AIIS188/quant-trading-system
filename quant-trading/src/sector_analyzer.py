"""
板块分析模块 - 基于涨停股行业分布
替代方案：当板块资金流数据不可用时
"""

import pandas as pd
from datetime import datetime
from collections import Counter


class SectorAnalyzer:
    """板块热度分析器"""
    
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
        self.sector_history = {}
    
    def analyze_limit_up_sectors(self, limit_up_data):
        """
        分析涨停股的行业分布 - 基于名称关键词
        :param limit_up_data: 涨停板数据
        :return: 板块热度统计
        """
        if limit_up_data is None or len(limit_up_data) == 0:
            return None
        
        # 关键词到板块的映射
        sector_keywords = {
            '芯片': ['芯片', '半导体', '集成'],
            'AI': ['AI', '人工智能', '智能'],
            '新能源': ['新能源', '光伏', '风电', '锂电'],
            '汽车': ['汽车', '整车', '汽配'],
            '医药': ['医药', '生物', '医疗'],
            '消费': ['消费', '食品', '饮料', '酒'],
            '金融': ['银行', '保险', '券商'],
            '科技': ['科技', '电子', '信息'],
            '制造': ['制造', '机械', '设备'],
            '化工': ['化工', '材料', '新材'],
        }
        
        # 统计涨停股的板块分布
        sectors = []
        for _, stock in limit_up_data.iterrows():
            name = stock.get('名称', '')
            sector = self._match_sector(name, sector_keywords)
            sectors.append(sector)
        
        # 统计
        sector_counts = Counter(sectors)
        
        # 转换为 DataFrame
        result = []
        for sector, count in sector_counts.most_common():
            result.append({
                '板块': sector,
                '涨停家数': count,
                '占比': count / len(limit_up_data) * 100
            })
        
        df = pd.DataFrame(result)
        
        return df
    
    def _match_sector(self, stock_name, sector_keywords):
        """根据股票名称匹配板块"""
        for sector, keywords in sector_keywords.items():
            for keyword in keywords:
                if keyword in stock_name:
                    return sector
        return '其他'
    
    def get_hot_sectors(self, limit_up_data, top_n=5):
        """
        获取热门板块
        :param limit_up_data: 涨停板数据
        :param top_n: 返回前 N 个
        :return: 热门板块列表
        """
        sector_df = self.analyze_limit_up_sectors(limit_up_data)
        
        if sector_df is None:
            return []
        
        # 返回前 N 个板块
        return sector_df.head(top_n).to_dict('records')
    
    def calculate_sector_strength(self, sector_data):
        """
        计算板块强度得分
        :param sector_data: 板块数据 (包含涨停家数、占比等)
        :return: 强度得分 (0-100)
        """
        if not sector_data:
            return 0
        
        # 强度 = 涨停家数 * 10 + 占比 * 2
        count = sector_data.get('涨停家数', 0)
        ratio = sector_data.get('占比', 0)
        
        score = count * 10 + ratio * 2
        
        # 限制在 0-100
        return min(100, max(0, score))
    
    def get_sector_sentiment(self, limit_up_data, limit_down_data=None):
        """
        基于涨跌停比计算板块情绪
        :param limit_up_data: 涨停板数据
        :param limit_down_data: 跌停板数据
        :return: 情绪得分
        """
        if limit_up_data is None:
            return 0
        
        up_count = len(limit_up_data)
        down_count = len(limit_down_data) if limit_down_data is not None else 0
        
        # 涨跌停比
        if down_count == 0:
            ratio = up_count  # 没有跌停，全是涨停
        else:
            ratio = up_count / down_count
        
        # 转换为 0-100 分
        #  ratio >= 10 → 100 分
        #  ratio = 1 → 50 分
        #  ratio = 0 → 0 分
        score = min(100, ratio * 10)
        
        return score
    
    def generate_sector_report(self, limit_up_data, limit_down_data=None):
        """
        生成板块分析报告
        :param limit_up_data: 涨停板数据
        :param limit_down_data: 跌停板数据
        :return: 报告 dict
        """
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'hot_sectors': [],
            'sector_strength': {},
            'sentiment_score': 0,
            'recommendations': []
        }
        
        # 热门板块
        hot_sectors = self.get_hot_sectors(limit_up_data, top_n=10)
        report['hot_sectors'] = hot_sectors
        
        # 板块强度
        for sector in hot_sectors[:3]:
            strength = self.calculate_sector_strength(sector)
            report['sector_strength'][sector['板块']] = strength
        
        # 市场情绪
        report['sentiment_score'] = self.get_sector_sentiment(limit_up_data, limit_down_data)
        
        # 建议
        if hot_sectors:
            top_sector = hot_sectors[0]['板块']
            top_count = hot_sectors[0]['涨停家数']
            
            if top_count >= 10:
                report['recommendations'].append(f"主线板块：{top_sector} ({top_count}只涨停)")
                report['recommendations'].append("建议：关注该板块的龙头股")
            elif top_count >= 5:
                report['recommendations'].append(f"热点板块：{top_sector} ({top_count}只涨停)")
                report['recommendations'].append("建议：精选个股参与")
            else:
                report['recommendations'].append("板块分散，无明确主线")
                report['recommendations'].append("建议：谨慎参与，控制仓位")
        
        return report


# 测试
if __name__ == "__main__":
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    analyzer = SectorAnalyzer(fetcher)
    
    print("测试板块分析模块...")
    print("=" * 60)
    
    # 获取涨停板
    limit_up = fetcher.get_limit_up()
    limit_down = fetcher.get_limit_down()
    
    if limit_up is not None:
        print(f"\n涨停家数：{len(limit_up)}")
        
        # 板块分析
        report = analyzer.generate_sector_report(limit_up, limit_down)
        
        print(f"\n热门板块 TOP5:")
        for i, sector in enumerate(report['hot_sectors'][:5], 1):
            print(f"  {i}. {sector['板块']}: {sector['涨停家数']}只 ({sector['占比']:.1f}%)")
        
        print(f"\n板块情绪得分：{report['sentiment_score']}")
        
        print(f"\n建议:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    print("\n" + "=" * 60)
