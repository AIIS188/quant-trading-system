"""
热点分析模块
分析市场热点、情绪周期、龙头股识别
"""

import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

class HotspotAnalyzer:
    """市场热点分析器"""
    
    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
        self.sector_history = defaultdict(list)
        self.emotion_index = []
    
    def analyze_sector_strength(self, sector_data):
        """
        分析板块强度
        :param sector_data: 板块数据 DataFrame
        :return: 板块强度排序
        """
        if sector_data is None or len(sector_data) == 0:
            return None
        
        # 计算板块强度得分
        # 考虑：涨跌幅、资金流入、成交量
        sector_data = sector_data.copy()
        
        # 强度得分 = 涨跌幅 * 0.4 + 资金流入归一化 * 0.4 + 换手率 * 0.2
        if '涨跌幅' in sector_data.columns:
            sector_data['强度得分'] = (
                sector_data['涨跌幅'] * 0.4 +
                sector_data.get('主力净流入', 0) * 0.4 +
                sector_data.get('换手率', 0) * 0.2
            )
        
        # 排序
        sector_data = sector_data.sort_values('强度得分', ascending=False)
        return sector_data
    
    def identify_leader_stocks(self, limit_up_data, sector_data):
        """
        识别龙头股
        :param limit_up_data: 涨停板数据
        :param sector_data: 板块数据
        :return: 龙头股列表
        """
        if limit_up_data is None or len(limit_up_data) == 0:
            return []
        
        leaders = []
        
        # 按连板数排序
        if '连板数' in limit_up_data.columns:
            limit_up_sorted = limit_up_data.sort_values('连板数', ascending=False)
            
            # 取连板数最高的前几只
            for _, row in limit_up_sorted.head(5).iterrows():
                leader = {
                    '代码': row.get('代码', ''),
                    '名称': row.get('名称', ''),
                    '连板数': row.get('连板数', 0),
                    '涨停时间': row.get('涨停时间', ''),
                    '封板资金': row.get('封板资金', 0),
                    '板块': self._get_stock_sector(row.get('代码', ''))
                }
                leaders.append(leader)
        
        return leaders
    
    def _get_stock_sector(self, stock_code):
        """获取股票所属板块（简化版）"""
        # 实际应该从数据中获取
        return "未知板块"
    
    def calculate_emotion_cycle(self, market_data):
        """
        计算市场情绪周期
        :param market_data: 市场数据
        :return: 情绪指标 (0-100, 越高越乐观)
        """
        emotion_score = 50  # 中性
        
        if market_data is not None:
            # 涨停家数
            limit_up_count = market_data.get('limit_up_count', 0)
            # 跌停家数
            limit_down_count = market_data.get('limit_down_count', 0)
            # 连板高度
            max_continuous = market_data.get('max_continuous', 0)
            
            # 情绪计算
            if limit_up_count > 50:
                emotion_score += 20
            elif limit_up_count > 30:
                emotion_score += 10
            elif limit_up_count < 10:
                emotion_score -= 20
            
            if limit_down_count > 30:
                emotion_score -= 20
            elif limit_down_count > 15:
                emotion_score -= 10
            
            if max_continuous >= 7:
                emotion_score += 15
            elif max_continuous >= 5:
                emotion_score += 10
            elif max_continuous <= 3:
                emotion_score -= 10
            
            # 限制在 0-100
            emotion_score = max(0, min(100, emotion_score))
        
        # 记录情绪历史
        self.emotion_index.append({
            'date': datetime.now().strftime('%Y-%m-%d'),
            'score': emotion_score
        })
        
        return emotion_score
    
    def get_emotion_stage(self, emotion_score):
        """
        根据情绪得分判断情绪阶段
        :param emotion_score: 情绪得分 (0-100)
        :return: 情绪阶段描述
        """
        if emotion_score >= 80:
            return "高潮期 - 风险积聚，考虑减仓"
        elif emotion_score >= 60:
            return "上升期 - 积极做多，参与龙头"
        elif emotion_score >= 40:
            return "震荡期 - 精选个股，控制仓位"
        elif emotion_score >= 20:
            return "退潮期 - 防守为主，减少操作"
        else:
            return "冰点期 - 等待机会，准备抄底"
    
    def analyze_hotspot_continuity(self, sector_name, days=5):
        """
        分析热点持续性
        :param sector_name: 板块名称
        :param days: 分析天数
        :return: 持续性评分 (0-100)
        """
        # 获取历史数据
        history = self.sector_history.get(sector_name, [])
        
        if len(history) < days:
            return 50  # 数据不足，中性
        
        # 计算持续性
        recent = history[-days:]
        
        # 如果连续上涨，持续性高
        up_days = sum(1 for d in recent if d.get('change', 0) > 0)
        continuity_score = (up_days / days) * 100
        
        return continuity_score
    
    def generate_daily_report(self):
        """生成每日热点分析报告"""
        report = {
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'emotion_score': self.calculate_emotion_cycle({}),
            'emotion_stage': self.get_emotion_stage(self.calculate_emotion_cycle({})),
            'hot_sectors': [],
            'leader_stocks': [],
            'recommendations': []
        }
        
        # 获取板块数据
        sector_data = self.data_fetcher.get_sector_flow()
        if sector_data is not None:
            strong_sectors = self.analyze_sector_strength(sector_data)
            if strong_sectors is not None:
                report['hot_sectors'] = strong_sectors.head(10).to_dict('records')
        
        # 获取涨停数据
        limit_up = self.data_fetcher.get_limit_up()
        if limit_up is not None:
            leaders = self.identify_leader_stocks(limit_up, sector_data)
            report['leader_stocks'] = leaders
        
        # 生成建议
        emotion = report['emotion_score']
        if emotion >= 60:
            report['recommendations'].append("市场情绪良好，可积极参与龙头股")
            report['recommendations'].append("关注主线板块的持续性")
        elif emotion >= 40:
            report['recommendations'].append("市场震荡，控制仓位在 5 成以内")
            report['recommendations'].append("精选个股，快进快出")
        else:
            report['recommendations'].append("市场情绪低迷，建议空仓或轻仓")
            report['recommendations'].append("等待明确信号再入场")
        
        return report
    
    def update_sector_history(self, sector_data):
        """更新板块历史数据"""
        if sector_data is None:
            return
        
        for _, row in sector_data.iterrows():
            sector_name = row.get('板块名称', '')
            if sector_name:
                self.sector_history[sector_name].append({
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'change': row.get('涨跌幅', 0),
                    'flow': row.get('主力净流入', 0)
                })
                
                # 只保留最近 30 天
                if len(self.sector_history[sector_name]) > 30:
                    self.sector_history[sector_name] = self.sector_history[sector_name][-30:]


# 测试
if __name__ == "__main__":
    from data_fetcher import DataFetcher
    
    fetcher = DataFetcher()
    analyzer = HotspotAnalyzer(fetcher)
    
    print("测试热点分析模块...")
    report = analyzer.generate_daily_report()
    
    print(f"\n日期：{report['date']}")
    print(f"情绪得分：{report['emotion_score']}")
    print(f"情绪阶段：{report['emotion_stage']}")
    print(f"\n建议:")
    for rec in report['recommendations']:
        print(f"  - {rec}")
