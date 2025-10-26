"""
계좌 전체 수익률 기준 목표 수익률 테스트
"""
import pandas as pd
import numpy as np
from strategy import StandardDeviationStrategy
from backtest import Backtester

# 테스트 데이터 생성 (상승 추세 데이터)
np.random.seed(42)
dates = pd.date_range('2023-01-01', periods=300, freq='D')
# 상승 추세를 위해 drift를 추가
prices = 100 * (1 + np.random.randn(300) * 0.02 + 0.001).cumprod()  # 0.1% daily drift

test_data = pd.DataFrame({
    'Close': prices,
    'Open': prices * 0.99,
    'High': prices * 1.01,
    'Low': prices * 0.98,
    'Volume': np.random.randint(1000000, 10000000, 300)
}, index=dates)

print("=" * 80)
print("계좌 전체 수익률 기준 목표 수익률 테스트")
print("=" * 80)

# 전략 적용
strategy = StandardDeviationStrategy(test_data, lookback_period=20)
print(f"\n데이터 기간: {strategy.data.index[0]} ~ {strategy.data.index[-1]}")
print(f"총 데이터: {len(strategy.data)}일")
print(f"시작 가격: ${strategy.data['Close'].iloc[0]:.2f}")
print(f"종료 가격: ${strategy.data['Close'].iloc[-1]:.2f}")
print(f"가격 변화: {((strategy.data['Close'].iloc[-1] / strategy.data['Close'].iloc[0]) - 1) * 100:.2f}%")

# 테스트 1: 목표 수익률 비활성화 (기존 동작)
print("\n" + "=" * 80)
print("테스트 1: 목표 수익률 비활성화")
print("=" * 80)

backtester_no_tp = Backtester(
    data=strategy.data,
    initial_capital=10000,
    position_size=1000,
    position_sizing_method="fixed",
    sigma_level=1,
    use_take_profit=False,
    take_profit_pct=20,
    use_ma_exit=False,
    use_trailing_stop=False,
    use_stop_loss=False
)
results_no_tp = backtester_no_tp.run()

print(f"\n최종 결과:")
print(f"  - 총 매수 횟수: {results_no_tp['buy_count']}회")
print(f"  - 총 매도 횟수: {results_no_tp['sell_count']}회")
print(f"  - 최종 자산: ${results_no_tp['final_value']:,.2f}")
print(f"  - 총 수익률: {results_no_tp['total_return_pct']:.2f}%")

if results_no_tp['sell_count'] > 0:
    print(f"\n매도 사유:")
    sell_reasons = results_no_tp['trades_df']['sell_reason'].value_counts()
    for reason, count in sell_reasons.items():
        print(f"  - {reason}: {count}회")

# 테스트 2: 목표 수익률 활성화 (20%)
print("\n" + "=" * 80)
print("테스트 2: 목표 수익률 활성화 (계좌 전체 20%)")
print("=" * 80)

backtester_with_tp = Backtester(
    data=strategy.data,
    initial_capital=10000,
    position_size=1000,
    position_sizing_method="fixed",
    sigma_level=1,
    use_take_profit=True,
    take_profit_pct=20,
    use_ma_exit=False,
    use_trailing_stop=False,
    use_stop_loss=False
)
results_with_tp = backtester_with_tp.run()

print(f"\n최종 결과:")
print(f"  - 총 매수 횟수: {results_with_tp['buy_count']}회")
print(f"  - 총 매도 횟수: {results_with_tp['sell_count']}회")
print(f"  - 최종 자산: ${results_with_tp['final_value']:,.2f}")
print(f"  - 총 수익률: {results_with_tp['total_return_pct']:.2f}%")

if results_with_tp['sell_count'] > 0:
    print(f"\n매도 사유:")
    sell_reasons = results_with_tp['trades_df']['sell_reason'].value_counts()
    for reason, count in sell_reasons.items():
        print(f"  - {reason}: {count}회")

    # Take Profit로 매도된 거래 확인
    tp_trades = results_with_tp['trades_df'][
        results_with_tp['trades_df']['sell_reason'].str.contains('Take Profit', na=False)
    ]

    if not tp_trades.empty:
        print(f"\n✅ 목표 수익률 달성으로 청산된 거래: {len(tp_trades)}건")
        print("\n상세 내역:")
        for idx, trade in tp_trades.iterrows():
            print(f"  매도일: {trade['sell_date'].date()}")
            print(f"  매도 가격: ${trade['sell_price']:.2f}")
            print(f"  수익률: {trade['profit_pct']:.2f}%")
            print(f"  사유: {trade['sell_reason']}")
            print()
    else:
        print("\n⚠️ 목표 수익률 달성 거래가 없습니다.")
else:
    print("\n⚠️ 매도가 발생하지 않았습니다. (데이터가 목표 수익률에 도달하지 못함)")

# 테스트 3: 포트폴리오 가치 추이 확인
print("\n" + "=" * 80)
print("테스트 3: 포트폴리오 가치 추이 비교")
print("=" * 80)

portfolio_no_tp = results_no_tp['portfolio_df']
portfolio_with_tp = results_with_tp['portfolio_df']

# 최고 계좌 가치 확인
max_value_no_tp = portfolio_no_tp['total_value'].max()
max_value_with_tp = portfolio_with_tp['total_value'].max()

max_profit_no_tp = (max_value_no_tp - 10000) / 10000 * 100
max_profit_with_tp = (max_value_with_tp - 10000) / 10000 * 100

print(f"\n목표 수익률 비활성화:")
print(f"  - 최고 계좌 가치: ${max_value_no_tp:,.2f}")
print(f"  - 최고 수익률: {max_profit_no_tp:.2f}%")

print(f"\n목표 수익률 활성화 (20%):")
print(f"  - 최고 계좌 가치: ${max_value_with_tp:,.2f}")
print(f"  - 최고 수익률: {max_profit_with_tp:.2f}%")

if max_profit_with_tp >= 20:
    print(f"\n✅ 계좌 수익률이 20%에 도달했습니다!")
else:
    print(f"\n⚠️ 계좌 수익률이 20%에 도달하지 못했습니다.")

# 테스트 4: Buy & Hold에도 적용 확인
print("\n" + "=" * 80)
print("테스트 4: Buy & Hold 전략에도 목표 수익률 적용 확인")
print("=" * 80)

backtester_bh_tp = Backtester(
    data=strategy.data,
    initial_capital=10000,
    position_size=1000,
    position_sizing_method="fixed",
    sigma_level=1,
    use_take_profit=True,
    take_profit_pct=30,
    use_ma_exit=False,
    use_trailing_stop=False,
    use_stop_loss=False,
    buy_hold_splits=12,
    buy_hold_use_risk_mgmt=True  # Buy & Hold에도 위험 관리 적용
)
results_bh_tp = backtester_bh_tp.run()

bh_stats = results_bh_tp['buy_hold_stats']
print(f"\nBuy & Hold 결과:")
print(f"  - 최종 자산: ${bh_stats['final_value']:,.2f}")
print(f"  - 총 수익률: {bh_stats['return_pct']:.2f}%")

if bh_stats.get('trades'):
    print(f"  - 총 매도 횟수: {len(bh_stats['trades'])}회")

    trades_df_bh = pd.DataFrame(bh_stats['trades'])
    sell_reasons_bh = trades_df_bh['sell_reason'].value_counts()
    print(f"\n  매도 사유:")
    for reason, count in sell_reasons_bh.items():
        print(f"    - {reason}: {count}회")

    # Take Profit로 매도된 거래 확인
    tp_trades_bh = trades_df_bh[trades_df_bh['sell_reason'].str.contains('Take Profit', na=False)]
    if not tp_trades_bh.empty:
        print(f"\n  ✅ Buy & Hold에서도 목표 수익률로 {len(tp_trades_bh)}건 청산됨")
else:
    print(f"  - 매도 없음 (보유 중)")

print("\n" + "=" * 80)
print("✅ 테스트 완료")
print("=" * 80)
print("\n주요 변경 사항:")
print("  1. 목표 수익률은 개별 포지션이 아닌 **계좌 전체 수익률** 기준")
print("  2. 계좌 전체 수익률이 목표치에 도달하면 **모든 포지션을 일괄 청산**")
print("  3. 매도 사유에 계좌 수익률 정보 포함 (예: 'Take Profit (Account: 20.5%)')")
print("  4. 실제 증권사 계좌와 동일한 방식으로 작동 (평균 단가 기준)")
print("=" * 80)
