#!/usr/bin/env python3
"""
A 股量化交易系统 - 主程序
Quant Trading System for A-Share Market

作者：量化助手
创建日期：2026-03-05
"""

import sys
import os
import json
from datetime import datetime
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from data_fetcher_unified import UnifiedDataFetcher
from hotspot_analyzer import HotspotAnalyzer
from sector_analyzer import SectorAnalyzer
from sector_flow import SectorFlowFetcher
from strategy_engine import StrategyEngine
from strategy_simple import SimpleStrategyEngine
from risk_controller import RiskController
from paper_trading import PaperTrading
from backtest import BacktestEngine
from daily_review import DailyReviewer


class QuantTradingSystem:
    """量化交易系统主类"""
    
    def __init__(self, config_path="config/config.json"):
        # 加载配置
        self.config = self.load_config(config_path)
        
        # 加载 Tushare Token (如果有)
        token_file = Path("config/tushare_token.txt")
        tushare_token = ""
        if token_file.exists():
            with open(token_file, 'r') as f:
                tushare_token = f.read().strip()
        
        # 初始化模块 - 使用统一接口 (优先 Tushare，失败自动降级 akshare)
        try:
            self.fetcher = UnifiedDataFetcher(tushare_token=tushare_token, cache_dir="data/cache")
        except Exception as e:
            print(f"⚠️ 统一接口初始化失败：{e}")
            from data_fetcher import DataFetcher
            self.fetcher = DataFetcher(cache_dir="data/cache")
            print("✅ 使用 akshare 数据源")
        self.risk_controller = RiskController(total_capital=self.config.get('initial_capital', 100000))
        self.strategy_engine = StrategyEngine(self.fetcher, self.risk_controller) if self.fetcher else None
        self.simple_strategy = SimpleStrategyEngine(self.risk_controller)
        self.hotspot_analyzer = HotspotAnalyzer(self.fetcher) if self.fetcher else None
        self.sector_analyzer = SectorAnalyzer(self.fetcher) if self.fetcher else None
        self.sector_flow = SectorFlowFetcher()
        self.paper_trading = PaperTrading(initial_capital=self.config.get('initial_capital', 100000))
        self.backtest_engine = BacktestEngine(initial_capital=self.config.get('initial_capital', 100000))
        self.daily_reviewer = DailyReviewer(logs_dir="logs")
        
        print(f"✅ 量化交易系统初始化完成")
        print(f"   初始资金：¥{self.risk_controller.total_capital:,.2f}")
        print(f"   单笔仓位上限：¥{self.risk_controller.total_capital * 0.1:,.2f}")
        print(f"   最大回撤限制：¥{self.risk_controller.total_capital * 0.08:,.2f}")
        print(f"   模拟盘：已启用")
    
    def load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        default_config = {
            'initial_capital': 100000,
            'max_position_pct': 0.10,
            'max_drawdown': 0.08,
            'max_daily_loss': 0.03,
            'max_consecutive_loss': 3,
            'turnover_threshold': 10,
            'pullback_low': 5,
            'pullback_high': 10
        }
        
        config_file = Path(config_path)
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        else:
            # 创建默认配置
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False, indent=2)
            print(f"📝 创建默认配置文件：{config_path}")
        
        return default_config
    
    def daily_scan(self):
        """
        每日市场扫描
        执行完整的工作流程
        """
        print("\n" + "=" * 60)
        print(f"每日市场扫描 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 1. 获取市场数据
        print("\n【1】获取市场数据...")
        
        # 涨停板
        limit_up = self.fetcher.get_limit_up()
        if limit_up is not None:
            print(f"   ✅ 今日涨停：{len(limit_up)}只")
        else:
            print("   ❌ 获取涨停数据失败")
            limit_up = None
        
        # 跌停板
        limit_down = self.fetcher.get_limit_down()
        if limit_down is not None:
            print(f"   ✅ 今日跌停：{len(limit_down)}只")
        
        # 龙虎榜
        longhu = self.fetcher.get_longhu_list()
        if longhu is not None:
            print(f"   ✅ 龙虎榜数据获取成功")
        
        # 2. 热点分析
        print("\n【2】热点分析...")
        
        # 板块资金流 (新增)
        print("   获取板块资金流...", end=' ')
        sector_flow_data = self.sector_flow.get_sector_flow()
        if sector_flow_data is not None and len(sector_flow_data) > 0:
            print(f"✅ {len(sector_flow_data)}个行业")
            print(f"\n   资金流入前 5 行业:")
            for _, row in sector_flow_data.head(5).iterrows():
                print(f"     • {row.get('行业', 'N/A')}: {row.get('流入资金', 'N/A')}")
        else:
            print("⚠️ 获取失败，使用涨停股行业分布")
            sector_flow_data = None
        
        # 生成热点分析报告
        hotspot_report = self.hotspot_analyzer.generate_daily_report()
        
        print(f"\n   情绪得分：{hotspot_report['emotion_score']}")
        print(f"   情绪阶段：{hotspot_report['emotion_stage']}")
        
        # 板块分析
        if self.sector_analyzer and limit_up is not None:
            sector_report = self.sector_analyzer.generate_sector_report(limit_up, limit_down)
            print(f"\n   热门板块 (涨停分布):")
            for i, sector in enumerate(sector_report['hot_sectors'][:5], 1):
                print(f"     {i}. {sector['板块']}: {sector['涨停家数']}只 ({sector['占比']:.1f}%)")
            
            if sector_report['recommendations']:
                print(f"\n   板块建议:")
                for rec in sector_report['recommendations']:
                    print(f"     • {rec}")
        
        if hotspot_report['leader_stocks']:
            print(f"\n   龙头股:")
            for leader in hotspot_report['leader_stocks'][:5]:
                print(f"     • {leader.get('代码')} {leader.get('名称')} "
                      f"(连板：{leader.get('连板数', 0)})")
        
        if hotspot_report['recommendations']:
            print(f"\n   操作建议:")
            for rec in hotspot_report['recommendations']:
                print(f"     • {rec}")
        
        # 3. 策略扫描
        print("\n【3】策略扫描...")
        
        signals = []
        
        # 使用简化策略 (不依赖 K 线)
        if limit_up is not None:
            limit_up_list = limit_up.to_dict('records')
            signals = self.simple_strategy.generate_signals(
                limit_up_data=limit_up_list,
                longhu_data=longhu.to_dict('records') if longhu is not None else None,
                emotion_score=hotspot_report['emotion_score']
            )
            
            print(f"   涨停股数量：{len(limit_up_list)}只")
            print(f"   生成信号：{len(signals)}个")
            
            if signals:
                print(f"\n   交易信号:")
                for sig in signals[:5]:
                    print(f"     • {sig.stock_code} {sig.stock_name}")
                    print(f"       策略：{sig.strategy}")
                    print(f"       动作：{sig.action}")
                    print(f"       信心：{sig.confidence}")
                    print(f"       原因：{sig.reason}")
        else:
            print("   ⚠️ 无法获取涨停数据，跳过策略扫描")
        
        # 4. 执行信号 (模拟盘)
        print("\n【4】模拟盘执行...")
        
        if signals:
            emotion_score = hotspot_report['emotion_score']
            leaders = hotspot_report['leader_stocks']
            
            executable_signals = self.strategy_engine.execute_signals(
                signals, emotion_score, leaders
            )
            
            print(f"   通过风控信号：{len(executable_signals)}个")
            
            # 模拟盘自动执行 (无需确认)
            executed = 0
            for sig in executable_signals:
                if sig.action == 'buy' and sig.stock_code != 'MARKET':
                    # 获取当前价格
                    price = sig.price if sig.price > 0 else 10.0
                    quantity = sig.quantity if sig.quantity > 0 else 1000
                    
                    success = self.paper_trading.buy(
                        stock_code=sig.stock_code,
                        stock_name=sig.stock_name,
                        price=price,
                        quantity=quantity,
                        strategy=sig.strategy,
                        signal_reason=sig.reason
                    )
                    if success:
                        executed += 1
            
            if executed > 0:
                print(f"   ✅ 模拟盘自动执行：{executed}笔买入")
            else:
                print(f"   模拟盘执行：0 笔 (无符合条件的信号)")
        else:
            print("   无信号可执行")
        
        # 5. 风控报告
        print("\n【5】风控报告...")
        
        risk_report = self.risk_controller.get_daily_report()
        print(f"   总资金：{risk_report['总资金']}")
        print(f"   可用资金：{risk_report['可用资金']}")
        print(f"   持仓数量：{risk_report['持仓数量']}")
        print(f"   交易状态：{risk_report['交易状态']}")
        
        # 6. 模拟盘报告
        print("\n【6】模拟盘报告...")
        
        paper_report = self.paper_trading.get_report()
        print(f"   总资金：{paper_report['总资金']}")
        print(f"   可用资金：{paper_report['可用资金']}")
        print(f"   总盈亏：{paper_report['总盈亏']}")
        print(f"   交易次数：{paper_report['交易次数']}")
        print(f"   胜率：{paper_report['胜率']}")
        
        if paper_report['持仓明细']:
            print(f"\n   持仓明细:")
            for pos in paper_report['持仓明细'][:5]:
                pnl_symbol = "+" if pos['盈亏'] >= 0 else ""
                print(f"     • {pos['代码']} {pos['名称']}: {pnl_symbol}{pos['盈亏']:.2f} ({pnl_symbol}{pos['盈亏%']:.1f}%)")
        
        # 7. 保存数据
        print("\n【7】保存数据...")
        
        if limit_up is not None:
            self.fetcher.save_cache(limit_up, f"limit_up_{datetime.now().strftime('%Y%m%d')}.csv")
        
        # 保存热点分析报告
        with open(f"logs/hotspot_{datetime.now().strftime('%Y%m%d')}.json", 'w', encoding='utf-8') as f:
            json.dump(hotspot_report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"   ✅ 数据已保存")
        
        print("\n" + "=" * 60)
        print("每日扫描完成")
        print("=" * 60)
        
        return {
            'hotspot_report': hotspot_report,
            'signals': signals,
            'executable_signals': executable_signals,
            'risk_report': risk_report
        }
    
    def generate_daily_review(self):
        """生成每日复盘"""
        print("\n生成每日复盘...")
        
        # 获取今日交易记录
        today_trades = [t for t in self.risk_controller.trades 
                       if t.date.date() == datetime.now().date()]
        
        # 转换交易记录格式
        trades_data = []
        for t in today_trades:
            trades_data.append({
                'stock_code': t.stock_code,
                'action': t.action,
                'price': t.price,
                'quantity': t.quantity,
                'strategy': t.strategy,
                'pnl': t.pnl,
                'reason': f"{t.action} @ {t.price}"
            })
        
        # 获取持仓
        positions_data = []
        for p in self.risk_controller.positions:
            positions_data.append({
                'stock_code': p.stock_code,
                'stock_name': p.stock_name,
                'quantity': p.quantity,
                'cost_price': p.cost_price,
                'current_price': p.current_price,
                'buy_date': p.buy_date
            })
        
        # 生成报告
        report = self.daily_reviewer.generate_daily_report(
            trades_data, 
            positions_data
        )
        
        # 保存并打印
        self.daily_reviewer.save_report(report)
        self.daily_reviewer.print_report(report)
        
        return report
    
    def run_backtest(self, stock_code: str, start_date: str, end_date: str):
        """
        运行回测
        :param stock_code: 股票代码
        :param start_date: 开始日期 YYYYMMDD
        :param end_date: 结束日期 YYYYMMDD
        """
        print(f"\n回测股票：{stock_code}")
        print(f"回测区间：{start_date} - {end_date}")
        
        # 获取 K 线数据
        kline = self.fetcher.get_kline(stock_code, period="daily", 
                                       start_date=start_date, end_date=end_date)
        
        if kline is None or len(kline) == 0:
            print("❌ 获取 K 线数据失败")
            return None
        
        print(f"✅ 获取 K 线数据：{len(kline)}条")
        
        # 这里需要实现策略信号生成逻辑
        # 简化示例：生成模拟信号
        signals = []
        
        # 实际应该根据策略生成信号
        # 这里是示例
        print("⚠️ 回测功能需要完整的策略信号生成逻辑")
        print("   当前为演示版本")
        
        return None
    
    def show_status(self):
        """显示系统状态"""
        print("\n" + "=" * 60)
        print("量化交易系统状态")
        print("=" * 60)
        
        risk_report = self.risk_controller.get_daily_report()
        
        print(f"\n资金状态:")
        print(f"  总资金：¥{risk_report['总资金']}")
        print(f"  可用资金：¥{risk_report['可用资金']}")
        print(f"  总盈亏：{risk_report['总盈亏']}")
        
        print(f"\n风控状态:")
        print(f"  当前回撤：{risk_report['当前回撤']}")
        print(f"  连续亏损：{risk_report['连续亏损']}")
        print(f"  交易状态：{risk_report['交易状态']}")
        
        print(f"\n持仓: {risk_report['持仓数量']}只")
        if risk_report['持仓明细']:
            for pos in risk_report['持仓明细']:
                pnl_symbol = "+" if pos['盈亏'] >= 0 else ""
                print(f"  {pos['代码']} {pos['名称']}: {pnl_symbol}{pos['盈亏']:.2f}")
        
        print("=" * 60)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='A 股量化交易系统')
    parser.add_argument('--scan', action='store_true', help='执行每日市场扫描')
    parser.add_argument('--review', action='store_true', help='生成每日复盘')
    parser.add_argument('--status', action='store_true', help='显示系统状态')
    parser.add_argument('--backtest', type=str, help='回测股票代码')
    parser.add_argument('--start-date', type=str, help='回测开始日期 YYYYMMDD')
    parser.add_argument('--end-date', type=str, help='回测结束日期 YYYYMMDD')
    
    args = parser.parse_args()
    
    # 初始化系统
    system = QuantTradingSystem()
    
    if args.scan:
        system.daily_scan()
    
    if args.review:
        system.generate_daily_review()
    
    if args.status or (not args.scan and not args.review and not args.backtest):
        system.show_status()
    
    if args.backtest:
        start_date = args.start_date or "20240101"
        end_date = args.end_date or datetime.now().strftime("%Y%m%d")
        system.run_backtest(args.backtest, start_date, end_date)


if __name__ == "__main__":
    main()
