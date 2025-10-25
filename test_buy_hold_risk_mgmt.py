import pandas as pd
import pytest

from backtest import Backtester


def test_buy_hold_risk_management_final_liquidation_does_not_double_count():
    dates = pd.date_range('2023-01-01', periods=60, freq='D')
    data = pd.DataFrame({
        'Close': 100.0,
        'Signal': 0,
        'MA_20': 100.0,
    }, index=dates)

    backtester = Backtester(
        data=data,
        initial_capital=1000,
        position_size=1000,
        buy_hold_splits=1,
        buy_hold_use_risk_mgmt=True,
        use_stop_loss=False,
        use_trailing_stop=False,
        take_profit_pct=10,
    )

    results = backtester.run()

    assert results['buy_hold_final_value'] == pytest.approx(1000)
    assert results['buy_hold_stats']['shares'] == 0
