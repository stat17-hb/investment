"""
포지션 사이징 방식 테스트
"""
import pandas as pd
import numpy as np
from strategy import StandardDeviationStrategy
from backtest import Backtester

# 테스트 데이터 생성
np.random.seed(42)
dates = pd.date_range('2023-01-01', periods=300, freq='D')
prices = 100 * (1 + np.random.randn(300) * 0.02).cumprod()

test_data = pd.DataFrame({
    'Close': prices,
    'Open': prices * 0.99,
    'High': prices * 1.01,
    'Low': prices * 0.98,
    'Volume': np.random.randint(1000000, 10000000, 300)
}, index=dates)

print("=" * 80)
print("포지션 사이징 방식 비교 테스트")
print("=" * 80)

# 전략 적용
strategy = StandardDeviationStrategy(test_data, lookback_period=20)
print(f"\n데이터 기간: {strategy.data.index[0]} ~ {strategy.data.index[-1]}")
print(f"총 데이터: {len(strategy.data)}일")

# 1. 고정 금액 방식
print("\n" + "=" * 80)
print("1. 고정 금액 방식 ($1,000)")
print("=" * 80)

backtester_fixed = Backtester(
    data=strategy.data,
    initial_capital=10000,
    position_size=1000,
    position_sizing_method="fixed",
    sigma_level=1,
    take_profit_pct=20,
    use_trailing_stop=True,
    trailing_stop_pct=30
)
results_fixed = backtester_fixed.run()

print(f"\n최종 결과:")
print(f"  - 총 매수 횟수: {results_fixed['buy_count']}회")
print(f"  - 총 매수 금액: ${results_fixed['total_invested']:,.2f}")
print(f"  - 최종 자산: ${results_fixed['final_value']:,.2f}")
print(f"  - 총 수익률: {results_fixed['total_return_pct']:.2f}%")

# 첫 5개 매수 내역 확인
if results_fixed['buy_count'] >= 1:
    print(f"\n처음 3회 매수 시뮬레이션:")
    print(f"  매수1: $1,000 투입 → 남은 현금: $9,000")
    print(f"  매수2: $1,000 투입 → 남은 현금: $8,000")
    print(f"  매수3: $1,000 투입 → 남은 현금: $7,000")
    print(f"  (항상 고정 금액)")

# 2. 동적 포지션 사이징 (현금의 20%)
print("\n" + "=" * 80)
print("2. 동적 포지션 사이징 (현금의 20%)")
print("=" * 80)

backtester_dynamic = Backtester(
    data=strategy.data,
    initial_capital=10000,
    position_sizing_method="dynamic",
    cash_allocation_pct=20,
    sigma_level=1,
    take_profit_pct=20,
    use_trailing_stop=True,
    trailing_stop_pct=30
)
results_dynamic = backtester_dynamic.run()

print(f"\n최종 결과:")
print(f"  - 총 매수 횟수: {results_dynamic['buy_count']}회")
print(f"  - 총 매수 금액: ${results_dynamic['total_invested']:,.2f}")
print(f"  - 최종 자산: ${results_dynamic['final_value']:,.2f}")
print(f"  - 총 수익률: {results_dynamic['total_return_pct']:.2f}%")

print(f"\n처음 3회 매수 시뮬레이션 (수익 없다고 가정):")
print(f"  매수1: $10,000 × 20% = $2,000 투입 → 남은 현금: $8,000")
print(f"  매수2: $8,000 × 20% = $1,600 투입 → 남은 현금: $6,400")
print(f"  매수3: $6,400 × 20% = $1,280 투입 → 남은 현금: $5,120")
print(f"  (매수 금액이 점점 감소)")

print(f"\n만약 매도로 수익 발생 시:")
print(f"  매수 후 매도로 $2,000 수익 → 현금: $12,000")
print(f"  다음 매수: $12,000 × 20% = $2,400 투입")
print(f"  (복리 효과!)")

# 비교
print("\n" + "=" * 80)
print("비교 결과")
print("=" * 80)
print(f"\n고정 금액 방식:")
print(f"  - 총 매수 금액: ${results_fixed['total_invested']:,.2f}")
print(f"  - 총 수익률: {results_fixed['total_return_pct']:.2f}%")

print(f"\n동적 포지션 사이징:")
print(f"  - 총 매수 금액: ${results_dynamic['total_invested']:,.2f}")
print(f"  - 총 수익률: {results_dynamic['total_return_pct']:.2f}%")

print(f"\n수익률 차이: {results_dynamic['total_return_pct'] - results_fixed['total_return_pct']:.2f}%p")

print("\n" + "=" * 80)
print("✅ 포지션 사이징 구현 완료")
print("   - 고정 금액: 매번 같은 금액 투입")
print("   - 동적 (현금 비율): 복리 효과로 더 높은 수익 가능")
print("=" * 80)
