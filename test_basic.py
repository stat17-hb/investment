"""기본 동작을 검증하는 단위 테스트"""
import numpy as np
import pandas as pd
import pytest

from backtest import Backtester
from strategy import StandardDeviationStrategy


@pytest.fixture
def synthetic_price_data():
    """월별 납입금 테스트에 사용할 결정적인 가격 데이터"""
    trading_days = pd.bdate_range("2020-01-01", periods=260)

    rng = np.random.default_rng(42)
    daily_changes = rng.normal(0, 0.01, size=len(trading_days))
    # 몇몇 구간에 큰 하락을 추가해 매수 시그널이 발생하도록 유도
    drop_indices = [40, 80, 120, 160, 200, 240]
    for idx in drop_indices:
        if idx < len(daily_changes):
            daily_changes[idx] = -0.09

    prices = 100 * np.cumprod(1 + daily_changes)

    df = pd.DataFrame(
        {
            "Open": prices,
            "High": prices,
            "Low": prices,
            "Close": prices,
            "Volume": 1_000_000,
        },
        index=trading_days,
    )
    return df


def test_backtester_tracks_monthly_contributions(synthetic_price_data):
    strategy = StandardDeviationStrategy(synthetic_price_data, lookback_period=20)
    backtester = Backtester(
        data=strategy.data,
        initial_capital=10_000,
        position_sizing_method="fixed",
        position_size=1_000,
        sigma_level=1,
        monthly_contribution=1_000,
        buy_hold_splits=12,
        buy_hold_timing="first",
    )

    results = backtester.run()

    unique_months = strategy.data.index.to_period("M").nunique()
    expected_total = 10_000 + 1_000 * unique_months

    assert results["total_contributed"] == pytest.approx(expected_total)
    assert results["buy_hold_total_contributed"] == pytest.approx(expected_total)

    # 전략/Buy & Hold 모두에서 실제 매수가 발생했는지 확인
    assert results["buy_count"] > 0
    assert results["buy_hold_buy_count"] == backtester.buy_hold_splits


def test_buy_hold_fixed_amount_exceeds_initial_capital(synthetic_price_data):
    """Buy & Hold가 초기 자본을 초과하는 고정 납입액도 모두 투자하는지 확인"""

    strategy = StandardDeviationStrategy(synthetic_price_data, lookback_period=20)
    backtester = Backtester(
        data=strategy.data,
        initial_capital=5_000,
        position_sizing_method="fixed",
        position_size=1_000,
        sigma_level=1,
        monthly_contribution=0,
        buy_hold_splits=12,
        buy_hold_timing="first",
    )

    results = backtester.run()

    assert results["buy_hold_buy_count"] == backtester.buy_hold_splits
    assert results["buy_hold_total_invested"] == pytest.approx(12_000)
    assert results["buy_hold_total_contributed"] == pytest.approx(12_000)
