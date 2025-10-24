"""
백테스트 엔진
"""
import pandas as pd
import numpy as np


class Backtester:
    """
    표준편차 매매법 백테스트

    전략:
    - 1σ 또는 2σ 하락 시 매수
    - 매도 조건: 일정 수익률 달성 또는 이동평균선 회귀
    """

    def __init__(
        self,
        data: pd.DataFrame,
        initial_capital: float = 10000,
        position_size: float = 1000,
        sigma_level: int = 1,
        take_profit_pct: float = 10.0,
        use_ma_exit: bool = True,
        use_stop_loss: bool = False,
        stop_loss_pct: float = 5.0,
        use_trailing_stop: bool = False,
        trailing_stop_pct: float = 10.0,
        buy_hold_splits: int = 1,
        buy_hold_use_risk_mgmt: bool = False
    ):
        """
        Args:
            data: 전략이 적용된 데이터 (StandardDeviationStrategy.data)
            initial_capital: 초기 자본금
            position_size: 1회 매수 금액
            sigma_level: 매수 기준 (1 또는 2)
            take_profit_pct: 목표 수익률 (%)
            use_ma_exit: 이동평균선 회귀 시 매도 여부
            use_stop_loss: 손절선 사용 여부
            stop_loss_pct: 손절 비율 (%)
            use_trailing_stop: 트레일링 스톱 사용 여부
            trailing_stop_pct: 트레일링 스톱 비율 (%)
            buy_hold_splits: Buy & Hold 분할 매수 횟수
            buy_hold_use_risk_mgmt: Buy & Hold에도 위험 관리 적용 여부
        """
        self.data = data.copy()
        self.initial_capital = initial_capital
        self.position_size = position_size
        self.sigma_level = sigma_level
        self.take_profit_pct = take_profit_pct / 100
        self.use_ma_exit = use_ma_exit
        self.use_stop_loss = use_stop_loss
        self.stop_loss_pct = stop_loss_pct / 100
        self.use_trailing_stop = use_trailing_stop
        self.trailing_stop_pct = trailing_stop_pct / 100
        self.buy_hold_splits = buy_hold_splits
        self.buy_hold_use_risk_mgmt = buy_hold_use_risk_mgmt

        self.positions = []
        self.trades = []
        self.portfolio_value = []

    def run(self) -> dict:
        """백테스트 실행"""
        cash = self.initial_capital
        holdings = []  # (매수가격, 수량, 매수일자)

        for idx, row in self.data.iterrows():
            current_price = row['Close']
            signal = row['Signal']
            ma_20 = row['MA_20']

            # 매수 조건 체크
            buy_signal = False
            if self.sigma_level == 1 and signal >= 1:
                buy_signal = True
            elif self.sigma_level == 2 and signal == 2:
                buy_signal = True

            # 매수 실행
            if buy_signal and cash >= self.position_size:
                shares = self.position_size / current_price
                holdings.append({
                    'buy_price': current_price,
                    'shares': shares,
                    'buy_date': idx,
                    'buy_signal': signal,
                    'peak_price': current_price  # 트레일링 스톱용 최고가
                })
                cash -= self.position_size

            # 매도 조건 체크 (보유 포지션이 있을 때)
            new_holdings = []
            for position in holdings:
                profit_pct = (current_price - position['buy_price']) / position['buy_price']
                should_sell = False
                sell_reason = ''

                # 최고가 업데이트 (트레일링 스톱용)
                if current_price > position['peak_price']:
                    position['peak_price'] = current_price

                # 1. 손절선 (Stop Loss)
                if self.use_stop_loss and profit_pct <= -self.stop_loss_pct:
                    should_sell = True
                    sell_reason = 'Stop Loss'

                # 2. 트레일링 스톱 (Trailing Stop)
                elif self.use_trailing_stop:
                    drawdown_from_peak = (current_price - position['peak_price']) / position['peak_price']
                    if drawdown_from_peak <= -self.trailing_stop_pct:
                        should_sell = True
                        sell_reason = 'Trailing Stop'

                # 3. 목표 수익률 달성
                elif profit_pct >= self.take_profit_pct:
                    should_sell = True
                    sell_reason = 'Take Profit'

                # 4. 이동평균선 회귀 (MA20 돌파)
                elif self.use_ma_exit and current_price > ma_20 and not pd.isna(ma_20):
                    if position['buy_price'] < ma_20:  # 매수가가 MA 아래였다면
                        should_sell = True
                        sell_reason = 'MA Cross'

                if should_sell:
                    # 매도 실행
                    sell_amount = position['shares'] * current_price
                    cash += sell_amount

                    # 거래 기록
                    self.trades.append({
                        'buy_date': position['buy_date'],
                        'sell_date': idx,
                        'buy_price': position['buy_price'],
                        'sell_price': current_price,
                        'shares': position['shares'],
                        'profit_pct': profit_pct * 100,
                        'profit_amount': sell_amount - (position['shares'] * position['buy_price']),
                        'sell_reason': sell_reason,
                        'holding_days': (idx - position['buy_date']).days
                    })
                else:
                    new_holdings.append(position)

            holdings = new_holdings

            # 포트폴리오 가치 계산
            holdings_value = sum([h['shares'] * current_price for h in holdings])
            total_value = cash + holdings_value

            self.portfolio_value.append({
                'date': idx,
                'cash': cash,
                'holdings_value': holdings_value,
                'total_value': total_value,
                'num_positions': len(holdings)
            })

        # 백테스트 종료 시 보유 중인 모든 포지션 청산
        if holdings:
            final_date = self.data.index[-1]
            final_price = self.data['Close'].iloc[-1]

            for position in holdings:
                profit_pct = (final_price - position['buy_price']) / position['buy_price']
                sell_amount = position['shares'] * final_price
                cash += sell_amount

                # 거래 기록
                self.trades.append({
                    'buy_date': position['buy_date'],
                    'sell_date': final_date,
                    'buy_price': position['buy_price'],
                    'sell_price': final_price,
                    'shares': position['shares'],
                    'profit_pct': profit_pct * 100,
                    'profit_amount': sell_amount - (position['shares'] * position['buy_price']),
                    'sell_reason': 'End of Backtest',
                    'holding_days': (final_date - position['buy_date']).days
                })

        # 최종 결과 계산
        return self.calculate_performance()

    def calculate_performance(self) -> dict:
        """성과 지표 계산"""
        if not self.portfolio_value:
            return {}

        portfolio_df = pd.DataFrame(self.portfolio_value)
        final_value = portfolio_df['total_value'].iloc[-1]

        total_return = (final_value - self.initial_capital) / self.initial_capital * 100

        # 거래 통계
        trades_df = pd.DataFrame(self.trades) if self.trades else pd.DataFrame()

        if not trades_df.empty:
            win_trades = trades_df[trades_df['profit_pct'] > 0]
            win_rate = len(win_trades) / len(trades_df) * 100
            avg_profit = trades_df['profit_pct'].mean()
            avg_win = win_trades['profit_pct'].mean() if len(win_trades) > 0 else 0
            avg_loss = trades_df[trades_df['profit_pct'] < 0]['profit_pct'].mean()
            avg_loss = avg_loss if not pd.isna(avg_loss) else 0
            max_profit = trades_df['profit_pct'].max()
            max_loss = trades_df['profit_pct'].min()
            avg_holding_days = trades_df['holding_days'].mean()
        else:
            win_rate = 0
            avg_profit = 0
            avg_win = 0
            avg_loss = 0
            max_profit = 0
            max_loss = 0
            avg_holding_days = 0

        # Buy & Hold 전략 시뮬레이션 (정확한 계산)
        buy_hold_stats = self.calculate_buy_and_hold()
        buy_hold_return = buy_hold_stats['return_pct']
        buy_hold_final_value = buy_hold_stats['final_value']
        buy_hold_shares = buy_hold_stats['shares']
        buy_hold_mdd = buy_hold_stats['max_drawdown_pct']
        buy_hold_portfolio_values = buy_hold_stats['portfolio_values']
        buy_hold_avg_buy_price = buy_hold_stats['avg_buy_price']
        buy_hold_buy_points = buy_hold_stats['buy_points']
        buy_hold_n_splits = buy_hold_stats['n_splits']
        # 전체 buy_hold_stats를 결과에 포함 (trades 정보 포함)

        # 최대 낙폭 (MDD)
        portfolio_df['cummax'] = portfolio_df['total_value'].cummax()
        portfolio_df['drawdown'] = (portfolio_df['total_value'] - portfolio_df['cummax']) / portfolio_df['cummax'] * 100
        max_drawdown = portfolio_df['drawdown'].min()

        return {
            'initial_capital': self.initial_capital,
            'final_value': final_value,
            'total_return_pct': total_return,
            'total_trades': len(trades_df),
            'win_rate': win_rate,
            'avg_profit_pct': avg_profit,
            'avg_win_pct': avg_win,
            'avg_loss_pct': avg_loss,
            'max_profit_pct': max_profit,
            'max_loss_pct': max_loss,
            'avg_holding_days': avg_holding_days,
            'buy_hold_return_pct': buy_hold_return,
            'buy_hold_final_value': buy_hold_final_value,
            'buy_hold_shares': buy_hold_shares,
            'buy_hold_mdd': buy_hold_mdd,
            'buy_hold_portfolio_values': buy_hold_portfolio_values,
            'buy_hold_avg_buy_price': buy_hold_avg_buy_price,
            'buy_hold_buy_points': buy_hold_buy_points,
            'buy_hold_n_splits': buy_hold_n_splits,
            'buy_hold_stats': buy_hold_stats,  # 전체 Buy & Hold 통계 (trades 포함)
            'max_drawdown_pct': max_drawdown,
            'portfolio_df': portfolio_df,
            'trades_df': trades_df
        }

    def calculate_buy_and_hold(self) -> dict:
        """
        Buy & Hold 전략 정확한 계산 (분할 매수 + 선택적 위험 관리)

        전략:
        - 전체 기간을 n등분하여 분할 매수
        - 각 시점에 (초기 자본 / n) 만큼 매수
        - 선택적으로 위험 관리 적용 (손절선, 트레일링 스톱, 목표 수익률)
        - 실제 주식 수량 기반 계산

        Returns:
            shares: 총 매수한 주식 수량
            avg_buy_price: 평균 매수 가격
            final_price: 최종 가격
            final_value: 최종 자산 가치
            return_pct: 수익률 (%)
            max_drawdown_pct: 최대 낙폭 (%)
            buy_points: 매수 시점 정보
            trades: 거래 내역 (위험 관리 적용 시)
        """
        total_days = len(self.data)
        n_splits = self.buy_hold_splits

        # 분할 매수 간격 계산
        if n_splits == 1:
            buy_indices = [0]
        else:
            buy_indices = [int(i * total_days / n_splits) for i in range(n_splits)]

        # 각 분할 시 투입할 금액
        capital_per_split = self.initial_capital / n_splits

        # 포트폴리오 상태
        cash_remaining = self.initial_capital
        holdings = []  # [{'buy_price': price, 'shares': shares, 'buy_date': date, 'peak_price': price}]
        buy_idx_set = set(buy_indices)
        portfolio_values = []
        buy_points = []
        trades = []  # 위험 관리로 인한 거래 기록

        # 매일 시뮬레이션
        for i, (idx, row) in enumerate(self.data.iterrows()):
            current_price = row['Close']

            # 매수 시점이면 주식 매수
            if i in buy_idx_set and cash_remaining >= capital_per_split:
                shares = capital_per_split / current_price
                holdings.append({
                    'buy_price': current_price,
                    'shares': shares,
                    'buy_date': idx,
                    'peak_price': current_price
                })
                cash_remaining -= capital_per_split

                buy_points.append({
                    'date': idx,
                    'price': current_price,
                    'shares': shares,
                    'amount': capital_per_split
                })

            # 위험 관리 적용 시 매도 조건 체크
            if self.buy_hold_use_risk_mgmt and holdings:
                new_holdings = []
                for position in holdings:
                    profit_pct = (current_price - position['buy_price']) / position['buy_price']
                    should_sell = False
                    sell_reason = ''

                    # 최고가 업데이트 (트레일링 스톱용)
                    if current_price > position['peak_price']:
                        position['peak_price'] = current_price

                    # 1. 손절선
                    if self.use_stop_loss and profit_pct <= -self.stop_loss_pct:
                        should_sell = True
                        sell_reason = 'Stop Loss'

                    # 2. 트레일링 스톱
                    elif self.use_trailing_stop:
                        drawdown_from_peak = (current_price - position['peak_price']) / position['peak_price']
                        if drawdown_from_peak <= -self.trailing_stop_pct:
                            should_sell = True
                            sell_reason = 'Trailing Stop'

                    # 3. 목표 수익률
                    elif profit_pct >= self.take_profit_pct:
                        should_sell = True
                        sell_reason = 'Take Profit'

                    if should_sell:
                        # 매도 실행
                        sell_amount = position['shares'] * current_price
                        cash_remaining += sell_amount

                        # 거래 기록
                        trades.append({
                            'buy_date': position['buy_date'],
                            'sell_date': idx,
                            'buy_price': position['buy_price'],
                            'sell_price': current_price,
                            'shares': position['shares'],
                            'profit_pct': profit_pct * 100,
                            'profit_amount': sell_amount - (position['shares'] * position['buy_price']),
                            'sell_reason': sell_reason
                        })
                    else:
                        new_holdings.append(position)

                holdings = new_holdings

            # 현재 포트폴리오 가치 = 보유 주식 가치 + 현금
            holdings_value = sum([h['shares'] * current_price for h in holdings])
            current_value = holdings_value + cash_remaining
            portfolio_values.append(current_value)

        # 백테스트 종료 시 보유 중인 모든 포지션 청산 (위험 관리 사용 시 거래 기록)
        if holdings and self.buy_hold_use_risk_mgmt:
            final_date = self.data.index[-1]
            final_price = self.data['Close'].iloc[-1]

            for position in holdings:
                profit_pct = (final_price - position['buy_price']) / position['buy_price']
                sell_amount = position['shares'] * final_price
                cash_remaining += sell_amount

                # 거래 기록
                trades.append({
                    'buy_date': position['buy_date'],
                    'sell_date': final_date,
                    'buy_price': position['buy_price'],
                    'sell_price': final_price,
                    'shares': position['shares'],
                    'profit_pct': profit_pct * 100,
                    'profit_amount': sell_amount - (position['shares'] * position['buy_price']),
                    'sell_reason': 'End of Backtest'
                })

        # 최종 결과 계산
        total_shares = sum([h['shares'] for h in holdings])
        final_value = cash_remaining + sum([h['shares'] * self.data['Close'].iloc[-1] for h in holdings])

        # 평균 매수가 계산
        if buy_points:
            total_invested = sum([bp['amount'] for bp in buy_points])
            total_bought_shares = sum([bp['shares'] for bp in buy_points])
            avg_buy_price = total_invested / total_bought_shares if total_bought_shares > 0 else 0
        else:
            avg_buy_price = 0

        # 수익률
        return_pct = (final_value - self.initial_capital) / self.initial_capital * 100

        # MDD 계산
        portfolio_series = pd.Series(portfolio_values)
        cummax = portfolio_series.cummax()
        drawdown = (portfolio_series - cummax) / cummax * 100
        max_drawdown_pct = drawdown.min()

        return {
            'shares': total_shares,
            'avg_buy_price': avg_buy_price,
            'buy_price': self.data['Close'].iloc[0],  # 첫날 가격 (참고용)
            'final_price': self.data['Close'].iloc[-1],
            'final_value': final_value,
            'return_pct': return_pct,
            'max_drawdown_pct': max_drawdown_pct,
            'portfolio_values': portfolio_values,
            'buy_points': buy_points,
            'n_splits': n_splits,
            'trades': trades,
            'use_risk_mgmt': self.buy_hold_use_risk_mgmt
        }
