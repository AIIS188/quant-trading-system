"""
每日复盘模块
自动生成交易日志和策略分析
"""

import pandas as pd
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict


class DailyReviewer:
    """每日复盘生成器"""
    
    def __init__(self, logs_dir="logs"):
        self.logs_dir = Path(logs_dir)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_daily_report(self, trades: List[Dict], positions: List[Dict], 
                             market_data: Dict = None) -> Dict:
        """
        生成每日复盘报告
        :param trades: 今日交易记录
        :param positions: 当前持仓
        :param market_data: 市场数据
        :return: 复盘报告
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 交易统计
        total_trades = len(trades)
        buy_trades = [t for t in trades if t.get('action') == 'buy']
        sell_trades = [t for t in trades if t.get('action') == 'sell']
        
        # 盈亏统计
        total_pnl = sum(t.get('pnl', 0) for t in sell_trades)
        winning_trades = [t for t in sell_trades if t.get('pnl', 0) > 0]
        losing_trades = [t for t in sell_trades if t.get('pnl', 0) < 0]
        
        win_count = len(winning_trades)
        loss_count = len(losing_trades)
        win_rate = win_count / len(sell_trades) * 100 if sell_trades else 0
        
        # 成功/失败分析
        success_reasons = []
        failure_reasons = []
        
        for trade in winning_trades:
            reason = trade.get('reason', '')
            if reason:
                success_reasons.append({
                    'stock': trade.get('stock_code'),
                    'pnl': trade.get('pnl'),
                    'reason': reason
                })
        
        for trade in losing_trades:
            reason = trade.get('reason', '')
            if reason:
                failure_reasons.append({
                    'stock': trade.get('stock_code'),
                    'pnl': trade.get('pnl'),
                    'reason': reason
                })
        
        # 策略表现
        strategy_stats = {}
        for trade in sell_trades:
            strategy = trade.get('strategy', '未知')
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {'total': 0, 'win': 0, 'pnl': 0}
            
            strategy_stats[strategy]['total'] += 1
            if trade.get('pnl', 0) > 0:
                strategy_stats[strategy]['win'] += 1
            strategy_stats[strategy]['pnl'] += trade.get('pnl', 0)
        
        # 计算策略胜率
        for strategy in strategy_stats:
            stats = strategy_stats[strategy]
            stats['win_rate'] = stats['win'] / stats['total'] * 100 if stats['total'] > 0 else 0
        
        # 持仓分析
        position_analysis = []
        for pos in positions:
            pnl = (pos.get('current_price', 0) - pos.get('cost_price', 0)) * pos.get('quantity', 0)
            pnl_pct = (pos.get('current_price', 0) - pos.get('cost_price', 0)) / pos.get('cost_price', 1) * 100
            position_analysis.append({
                'stock_code': pos.get('stock_code'),
                'stock_name': pos.get('stock_name'),
                'quantity': pos.get('quantity'),
                'cost_price': pos.get('cost_price'),
                'current_price': pos.get('current_price'),
                'pnl': pnl,
                'pnl_pct': pnl_pct,
                'days_held': (datetime.now() - pos.get('buy_date', datetime.now())).days
            })
        
        # 市场情绪 (如果有数据)
        market_analysis = {}
        if market_data:
            market_analysis = {
                '涨停家数': market_data.get('limit_up_count', 0),
                '跌停家数': market_data.get('limit_down_count', 0),
                '连板高度': market_data.get('max_continuous', 0),
                '情绪得分': market_data.get('emotion_score', 50)
            }
        
        # 生成改进建议
        improvements = []
        
        if win_rate < 50 and total_trades > 3:
            improvements.append("胜率偏低，建议重新审视选股标准")
        
        if total_pnl < 0:
            improvements.append("今日亏损，建议复盘交易逻辑，检查是否严格执行策略")
        
        if len(positions) > 5:
            improvements.append("持仓过多，建议集中注意力于优质标的")
        
        if not improvements:
            improvements.append("今日表现良好，继续保持")
        
        # 组装报告
        report = {
            'date': today,
            'summary': {
                '交易次数': total_trades,
                '买入次数': len(buy_trades),
                '卖出次数': len(sell_trades),
                '盈利次数': win_count,
                '亏损次数': loss_count,
                '胜率': f"{win_rate:.1f}%",
                '总盈亏': f"{total_pnl:.2f}"
            },
            'market_analysis': market_analysis,
            'strategy_performance': strategy_stats,
            'position_analysis': position_analysis,
            'success_cases': success_reasons,
            'failure_cases': failure_reasons,
            'improvements': improvements,
            'raw_trades': trades,
            'raw_positions': positions
        }
        
        return report
    
    def save_report(self, report: Dict, filepath: str = None):
        """保存复盘报告"""
        if filepath is None:
            filepath = self.logs_dir / f"daily_review_{datetime.now().strftime('%Y%m%d')}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"复盘报告已保存：{filepath}")
    
    def print_report(self, report: Dict):
        """打印复盘报告"""
        print("\n" + "=" * 60)
        print(f"每日复盘报告 - {report['date']}")
        print("=" * 60)
        
        print("\n【交易统计】")
        for k, v in report['summary'].items():
            print(f"  {k}: {v}")
        
        if report['market_analysis']:
            print("\n【市场分析】")
            for k, v in report['market_analysis'].items():
                print(f"  {k}: {v}")
        
        if report['strategy_performance']:
            print("\n【策略表现】")
            for strategy, stats in report['strategy_performance'].items():
                print(f"  {strategy}:")
                print(f"    交易次数：{stats['total']}, 胜率：{stats['win_rate']:.1f}%, 盈亏：{stats['pnl']:.2f}")
        
        if report['position_analysis']:
            print("\n【持仓分析】")
            for pos in report['position_analysis']:
                pnl_symbol = "+" if pos['pnl'] >= 0 else ""
                print(f"  {pos['stock_code']} {pos['stock_name']}: "
                      f"{pnl_symbol}{pos['pnl']:.2f} ({pnl_symbol}{pos['pnl_pct']:.1f}%)")
        
        if report['success_cases']:
            print("\n【成功案例】")
            for case in report['success_cases'][:3]:  # 只显示前 3 个
                print(f"  {case['stock']}: +{case['pnl']:.2f} - {case['reason']}")
        
        if report['failure_cases']:
            print("\n【失败案例】")
            for case in report['failure_cases'][:3]:  # 只显示前 3 个
                print(f"  {case['stock']}: {case['pnl']:.2f} - {case['reason']}")
        
        print("\n【改进建议】")
        for imp in report['improvements']:
            print(f"  • {imp}")
        
        print("=" * 60 + "\n")
    
    def load_history(self, days: int = 30) -> List[Dict]:
        """加载历史复盘报告"""
        reports = []
        pattern = "daily_review_*.json"
        
        for filepath in sorted(self.logs_dir.glob(pattern), reverse=True)[:days]:
            with open(filepath, 'r', encoding='utf-8') as f:
                reports.append(json.load(f))
        
        return reports
    
    def generate_weekly_summary(self) -> Dict:
        """生成周度总结"""
        reports = self.load_history(days=7)
        
        if not reports:
            return {}
        
        total_pnl = 0
        total_trades = 0
        total_wins = 0
        strategy_weekly = {}
        
        for report in reports:
            total_pnl += float(report['summary'].get('总盈亏', '0').replace(',', ''))
            total_trades += report['summary'].get('交易次数', 0)
            win_rate_str = report['summary'].get('胜率', '0%').replace('%', '')
            wins = int(float(win_rate_str) / 100 * report['summary'].get('卖出次数', 0))
            total_wins += wins
            
            # 策略表现汇总
            for strategy, stats in report.get('strategy_performance', {}).items():
                if strategy not in strategy_weekly:
                    strategy_weekly[strategy] = {'total': 0, 'win': 0, 'pnl': 0}
                strategy_weekly[strategy]['total'] += stats.get('total', 0)
                strategy_weekly[strategy]['win'] += stats.get('win', 0)
                strategy_weekly[strategy]['pnl'] += stats.get('pnl', 0)
        
        # 计算策略胜率
        for strategy in strategy_weekly:
            stats = strategy_weekly[strategy]
            stats['win_rate'] = stats['win'] / stats['total'] * 100 if stats['total'] > 0 else 0
        
        return {
            'period': '周度总结',
            '总盈亏': total_pnl,
            '总交易次数': total_trades,
            '总盈利次数': total_wins,
            '周胜率': f"{total_wins / total_trades * 100 if total_trades > 0 else 0:.1f}%",
            '策略表现': strategy_weekly
        }


# 测试
if __name__ == "__main__":
    reviewer = DailyReviewer()
    
    # 模拟数据
    trades = [
        {'stock_code': '000001', 'action': 'buy', 'price': 10.5, 'quantity': 1000, 'strategy': '龙头回调', 'reason': '回调 8%, 缩量'},
        {'stock_code': '000001', 'action': 'sell', 'price': 11.2, 'quantity': 1000, 'strategy': '龙头回调', 'pnl': 630, 'reason': '达到目标位'},
        {'stock_code': '000002', 'action': 'buy', 'price': 20.0, 'quantity': 500, 'strategy': '突破', 'reason': '突破平台，放量'},
        {'stock_code': '000002', 'action': 'sell', 'price': 19.5, 'quantity': 500, 'strategy': '突破', 'pnl': -280, 'reason': '假突破'}
    ]
    
    positions = [
        {'stock_code': '000003', 'stock_name': '测试股票', 'quantity': 1000, 'cost_price': 15.0, 
         'current_price': 15.8, 'buy_date': datetime.now()}
    ]
    
    market_data = {
        'limit_up_count': 45,
        'limit_down_count': 8,
        'max_continuous': 5,
        'emotion_score': 65
    }
    
    report = reviewer.generate_daily_report(trades, positions, market_data)
    reviewer.print_report(report)
    reviewer.save_report(report)
