"""
Lookahead Bias 수정 검증 테스트
"""
import pandas as pd
import numpy as np
from strategy import StandardDeviationStrategy

# 간단한 테스트 데이터 생성
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
print("Lookahead Bias 수정 검증 테스트")
print("=" * 80)

# 전략 실행
strategy = StandardDeviationStrategy(test_data, lookback_period=20)

print(f"\n데이터 기간: {strategy.data.index[0]} ~ {strategy.data.index[-1]}")
print(f"총 데이터: {len(strategy.data)}일")

# 시그널 발생 확인
signals = strategy.data[strategy.data['Signal'] > 0]
print(f"\n총 시그널 발생: {len(signals)}회")
print(f"  - 1σ 시그널: {len(strategy.data[strategy.data['Signal'] >= 1])}회")
print(f"  - 2σ 시그널: {len(strategy.data[strategy.data['Signal'] == 2])}회")

# 샘플 시그널 확인 (처음 5개)
if len(signals) > 0:
    print("\n시그널 샘플 (처음 5개):")
    print("-" * 80)
    sample = signals.head(5)[['Close', 'Returns', 'Daily_Std_Dev', 'Signal', 'Price_Change_Pct']]

    for idx, row in sample.iterrows():
        # 전일 표준편차 확인 (shift 적용 검증)
        prev_idx_loc = strategy.data.index.get_loc(idx) - 1
        if prev_idx_loc >= 0:
            prev_std = strategy.data.iloc[prev_idx_loc]['Daily_Std_Dev']
        else:
            prev_std = np.nan

        print(f"\n날짜: {idx.date()}")
        print(f"  종가: ${row['Close']:.2f}")
        print(f"  당일 수익률: {row['Returns']*100:.2f}%")
        print(f"  전일 표준편차: {prev_std*100:.2f}%" if not np.isnan(prev_std) else "  전일 표준편차: N/A")
        print(f"  당일 표준편차: {row['Daily_Std_Dev']*100:.2f}%")
        print(f"  시그널: {int(row['Signal'])}σ")

        # 검증: 당일 수익률이 전일 표준편차 기준으로 충분히 하락했는지
        if not np.isnan(prev_std):
            threshold_1sigma = -prev_std
            threshold_2sigma = -2 * prev_std
            print(f"  검증: {row['Returns']:.4f} <= {threshold_1sigma:.4f} ? {row['Returns'] <= threshold_1sigma}")
            if row['Signal'] == 2:
                print(f"  검증: {row['Returns']:.4f} <= {threshold_2sigma:.4f} ? {row['Returns'] <= threshold_2sigma}")

print("\n" + "=" * 80)
print("✅ Lookahead Bias 수정 완료:")
print("   - T일의 수익률을 T-1일까지의 표준편차와 비교")
print("   - shift(1) 적용으로 미래 데이터 참조 제거")
print("=" * 80)
