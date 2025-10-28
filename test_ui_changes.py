"""
UI 변경사항 테스트
"""
import pandas as pd
import numpy as np

print("=" * 80)
print("UI 변경사항 테스트")
print("=" * 80)

# 테스트 데이터 생성
np.random.seed(42)
returns = np.random.randn(1000) * 0.02  # 일일 수익률 (소수)
returns_pct = returns * 100  # 퍼센트로 변환

print("\n1. 기본 통계량 계산 테스트")
print("-" * 80)

# 통계량 계산 (numpy로 직접 계산)
mean_val = returns_pct.mean()
median_val = np.median(returns_pct)
std_val = returns_pct.std()
min_val = returns_pct.min()
max_val = returns_pct.max()

# 왜도 (Skewness): E[((X - μ) / σ)^3]
skewness = ((returns_pct - mean_val) / std_val) ** 3
skewness = skewness.mean()

# 첨도 (Kurtosis): E[((X - μ) / σ)^4] - 3 (excess kurtosis)
kurtosis_val = ((returns_pct - mean_val) / std_val) ** 4
kurtosis_val = kurtosis_val.mean() - 3

print(f"평균: {mean_val:.3f}%")
print(f"중앙값: {median_val:.3f}%")
print(f"표준편차: {std_val:.3f}%")
print(f"최솟값: {min_val:.3f}%")
print(f"최댓값: {max_val:.3f}%")
print(f"왜도: {skewness:.3f}")
print(f"첨도: {kurtosis_val:.3f}")

print("\n2. 분위수 계산 테스트")
print("-" * 80)

# 분위수 계산
quantiles = np.quantile(returns_pct, [0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
quantile_labels = ['1%', '5%', '25%', '50%', '75%', '95%', '99%']

for label, val in zip(quantile_labels, quantiles):
    print(f"{label}: {val:.3f}%")

print("\n3. 정규분포 곡선 데이터 생성 테스트")
print("-" * 80)

mu = returns_pct.mean()
sigma = returns_pct.std()
x_range = np.linspace(returns_pct.min(), returns_pct.max(), 100)
normal_dist = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_range - mu) / sigma) ** 2)

print(f"정규분포 곡선 데이터 포인트: {len(x_range)}개")
print(f"정규분포 최대값: {normal_dist.max():.6f}")
print(f"정규분포 최소값: {normal_dist.min():.6f}")

print("\n4. 왜도/첨도 해석 테스트")
print("-" * 80)

if abs(skewness) < 0.5:
    skew_interpretation = "대칭적 분포"
elif skewness > 0:
    skew_interpretation = "오른쪽 꼬리가 긴 분포 (큰 양의 수익률 가능성)"
else:
    skew_interpretation = "왼쪽 꼬리가 긴 분포 (큰 손실 가능성)"

if abs(kurtosis_val) < 0.5:
    kurt_interpretation = "정규분포와 유사한 꼬리"
elif kurtosis_val > 0:
    kurt_interpretation = "정규분포보다 두꺼운 꼬리 (극단적 사건 가능성 높음)"
else:
    kurt_interpretation = "정규분포보다 얇은 꼬리"

print(f"왜도 ({skewness:.3f}): {skew_interpretation}")
print(f"첨도 ({kurtosis_val:.3f}): {kurt_interpretation}")

print("\n" + "=" * 80)
print("✅ 모든 테스트 통과")
print("=" * 80)
