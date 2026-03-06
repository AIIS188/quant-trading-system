#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日资金流数据获取脚本
- 获取行业/概念资金流
- 获取北向资金
- 保存到 data/fund_flow/ 目录
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from data_fetchers.fund_flow import FundFlowFetcher
import pandas as pd
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def save_fund_flow_data():
    """获取并保存资金流数据"""
    fetcher = FundFlowFetcher()
    today = datetime.now().strftime('%Y%m%d')
    
    # 创建数据目录
    data_dir = Path(__file__).parent.parent / 'data' / 'fund_flow'
    data_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"开始获取资金流数据，保存到 {data_dir}")
    
    # 1. 行业资金流
    logger.info("获取行业资金流...")
    industry = fetcher.get_industry_fund_flow(symbol='即时')
    if not industry.empty:
        industry_file = data_dir / f'industry_{today}.csv'
        industry.to_csv(industry_file, index=False, encoding='utf-8-sig')
        logger.info(f"行业资金流已保存：{industry_file} ({len(industry)} 个行业)")
    
    # 2. 概念资金流
    logger.info("获取概念资金流...")
    concept = fetcher.get_concept_fund_flow(symbol='即时')
    if not concept.empty:
        concept_file = data_dir / f'concept_{today}.csv'
        concept.to_csv(concept_file, index=False, encoding='utf-8-sig')
        logger.info(f"概念资金流已保存：{concept_file} ({len(concept)} 个概念)")
    
    # 3. 北向资金
    logger.info("获取北向资金...")
    north = fetcher.get_north_fund_flow()
    if not north.empty:
        north_file = data_dir / f'north_{today}.csv'
        north.to_csv(north_file, index=False, encoding='utf-8-sig')
        logger.info(f"北向资金已保存：{north_file}")
    
    # 4. 市场情绪分析
    logger.info("分析市场情绪...")
    sentiment = fetcher.analyze_market_sentiment()
    sentiment_file = data_dir / f'sentiment_{today}.json'
    with open(sentiment_file, 'w', encoding='utf-8') as f:
        json.dump(sentiment, f, ensure_ascii=False, indent=2)
    logger.info(f"市场情绪已保存：{sentiment_file}")
    
    # 5. 生成简报
    report = generate_daily_report(industry, concept, north, sentiment)
    report_file = data_dir / f'daily_report_{today}.md'
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    logger.info(f"每日简报已保存：{report_file}")
    
    return {
        'industry_count': len(industry),
        'concept_count': len(concept),
        'sentiment_score': sentiment['overall_score'],
        'north_sentiment': sentiment['north_sentiment'],
    }


def generate_daily_report(industry, concept, north, sentiment) -> str:
    """生成每日资金流简报"""
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    report = f"""# 每日资金流简报

**生成时间:** {today}

---

## 📊 市场情绪概览

- **情绪得分:** {sentiment['overall_score']} / 100
- **北向情绪:** {sentiment['north_sentiment']}
- **行业上涨比例:** {sentiment.get('industry_stats', {}).get('up_ratio', 'N/A')}%
- **概念上涨比例:** {sentiment.get('concept_stats', {}).get('up_ratio', 'N/A')}%

---

## 🔥 行业资金流 TOP10

| 排名 | 行业 | 净流入 (亿) | 涨跌幅 |
|------|------|-------------|--------|
"""
    
    if not industry.empty:
        top10 = industry.nlargest(10, '净额')
        for idx, row in top10.iterrows():
            report += f"| {idx+1} | {row['行业']} | {row['净额']:.2f} | {row['行业-涨跌幅']:.2f}% |\n"
    
    report += f"""
---

## 💡 概念资金流 TOP10

| 排名 | 概念 | 净流入 (亿) | 涨跌幅 |
|------|------|-------------|--------|
"""
    
    if not concept.empty:
        top10 = concept.nlargest(10, '净额')
        for idx, row in top10.iterrows():
            report += f"| {idx+1} | {row['行业']} | {row['净额']:.2f} | {row['行业-涨跌幅']:.2f}% |\n"
    
    report += f"""
---

## 🧭 北向资金

| 板块 | 资金方向 | 净流入 (亿) |
|------|----------|-------------|
"""
    
    if not north.empty:
        for idx, row in north.iterrows():
            report += f"| {row['板块']} | {row['资金方向']} | {row['资金净流入']:.2f} |\n"
    
    report += f"""
---

## 📈 操作建议

"""
    
    score = sentiment['overall_score']
    if score >= 70:
        report += "**情绪偏多**, 可积极关注热点板块龙头股机会。\n"
    elif score >= 50:
        report += "**情绪中性**, 精选个股，控制仓位。\n"
    elif score >= 30:
        report += "**情绪偏空**, 谨慎操作，降低仓位。\n"
    else:
        report += "**情绪低迷**, 建议空仓观望。\n"
    
    report += f"""
---

*数据源：东方财富 via Akshare*
"""
    
    return report


if __name__ == '__main__':
    try:
        result = save_fund_flow_data()
        print("\n✅ 资金流数据获取完成!")
        print(f"   行业：{result['industry_count']} 个")
        print(f"   概念：{result['concept_count']} 个")
        print(f"   情绪得分：{result['sentiment_score']}")
        print(f"   北向情绪：{result['north_sentiment']}")
    except Exception as e:
        logger.error(f"获取资金流数据失败：{e}")
        sys.exit(1)
