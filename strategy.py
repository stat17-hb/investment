"""
표준편차 매매 전략 로직
"""
import pandas as pd
import numpy as np


class StandardDeviationStrategy:
    """
    표준편차 매매법 전략

    핵심 개념:
    - 1년(252거래일) 기준 표준편차 계산
    - 1σ 하락 시 매수 (68% 확률 범위)
    - 2σ 하락 시 추가 매수 (95% 확률 범위)
    """

    def __init__(self, data: pd.DataFrame, lookback_period: int = 252):
        """
        Args:
            data: OHLCV 데이터
            lookback_period: 표준편차 계산 기간 (기본 252일 = 1년)
        """
        self.data = data.copy()
        self.lookback_period = lookback_period
        self.calculate_indicators()

    @staticmethod
    def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index) 계산

        Args:
            prices: 가격 시리즈
            window: RSI 계산 기간 (기본 14일)

        Returns:
            RSI 값 시리즈 (0-100)
        """
        delta = prices.diff()

        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))

        return rsi

    def calculate_indicators(self):
        """기술적 지표 계산"""
        # 일일 수익률 계산
        self.data['Returns'] = self.data['Close'].pct_change()

        # 일일 수익률의 롤링 표준편차 계산
        self.data['Daily_Std_Dev'] = self.data['Returns'].rolling(
            window=self.lookback_period
        ).std()

        # 연율화 표준편차 (연간 변동성)
        self.data['Std_Dev'] = self.data['Daily_Std_Dev'] * np.sqrt(252)

        # 표준편차를 가격으로 환산 (현재가 * 일일 표준편차)
        # 가격 밴드는 하루 변동폭을 기준으로 계산한다.
        self.data['Std_Dev_Price'] = self.data['Close'] * self.data['Daily_Std_Dev']

        # 1σ, 2σ 매수 가격 계산
        self.data['Buy_1Sigma'] = self.data['Close'] - self.data['Std_Dev_Price']
        self.data['Buy_2Sigma'] = self.data['Close'] - (2 * self.data['Std_Dev_Price'])

        # 상한선 (참고용)
        self.data['Sell_1Sigma'] = self.data['Close'] + self.data['Std_Dev_Price']
        self.data['Sell_2Sigma'] = self.data['Close'] + (2 * self.data['Std_Dev_Price'])

        # 이동평균선 (중심선)
        self.data['MA_20'] = self.data['Close'].rolling(window=20).mean()
        self.data['MA_60'] = self.data['Close'].rolling(window=60).mean()

        # RSI 계산 (직접 구현)
        self.data['RSI'] = self.calculate_rsi(self.data['Close'], window=14)

        # 매수 시그널 생성
        self.generate_signals()

        # 표준편차 계산이 완료된 유효한 데이터만 필터링
        # lookback_period 동안은 표준편차가 NaN이므로 제외
        # 이렇게 하면 Buy & Hold와 동일한 시작 시점에서 백테스트 가능
        self.data = self.data.dropna(subset=['Std_Dev', 'Daily_Std_Dev', 'MA_20', 'RSI'])

    def generate_signals(self):
        """
        매수/매도 시그널 생성 (Lookahead Bias 방지)

        핵심 원칙: T일의 매수 결정은 T-1일까지의 데이터로만 이루어져야 함

        로직:
        - T일의 수익률 = (Close[T] - Close[T-1]) / Close[T-1]
        - T-1일까지의 표준편차 = Daily_Std_Dev[T-1]
        - T일의 수익률이 T-1일까지의 표준편차 기준으로 충분히 하락했는지 판단
        - 조건 충족 시 T일 종가에 매수

        이는 "T일 장 마감 후 종가를 확인하고, 어제까지의 변동성 기준으로
        충분히 떨어졌다고 판단하여 종가 또는 시간외 거래로 매수"하는
        실제 가능한 시나리오입니다.
        """
        self.data['Signal'] = 0  # 0: 관망, 1: 1σ 매수, 2: 2σ 매수

        # 전일 대비 하락폭 계산
        self.data['Price_Change_Pct'] = self.data['Returns'] * 100

        # ⚠️ Lookahead Bias 방지: T-1일까지의 표준편차 사용
        # shift(1)을 사용하여 T일 시점에서는 T-1일의 표준편차만 알고 있음
        daily_std_lagged = self.data['Daily_Std_Dev'].shift(1)

        # 1σ 매수 시그널: T일의 수익률이 T-1일까지의 1σ 이하로 하락
        # 예: 어제까지의 일일 표준편차가 3%였고, 오늘 -3% 이상 하락 시 매수
        condition_1sigma = (self.data['Returns'] <= -daily_std_lagged)

        # 2σ 매수 시그널: T일의 수익률이 T-1일까지의 2σ 이하로 하락
        # 예: 어제까지의 일일 표준편차가 3%였고, 오늘 -6% 이상 하락 시 매수
        condition_2sigma = (self.data['Returns'] <= -2 * daily_std_lagged)

        self.data.loc[condition_1sigma, 'Signal'] = 1
        self.data.loc[condition_2sigma, 'Signal'] = 2

    def get_current_stats(self) -> dict:
        """현재 통계 정보 반환"""
        latest = self.data.iloc[-1]

        return {
            'current_price': latest['Close'],
            'std_dev_pct': latest['Std_Dev'] * 100,
            'daily_std_dev_pct': latest['Daily_Std_Dev'] * 100,
            'std_dev_price': latest['Std_Dev_Price'],
            'buy_1sigma_price': latest['Buy_1Sigma'],
            'buy_2sigma_price': latest['Buy_2Sigma'],
            'sell_1sigma_price': latest['Sell_1Sigma'],
            'sell_2sigma_price': latest['Sell_2Sigma'],
            'ma_20': latest['MA_20'],
            'ma_60': latest['MA_60'],
            'rsi': latest['RSI'],
            'signal': latest['Signal']
        }

    def get_buy_signals(self, sigma_level: int = 1) -> pd.DataFrame:
        """
        매수 시그널 발생 시점 반환

        Args:
            sigma_level: 1 또는 2 (1σ 또는 2σ)

        Returns:
            매수 시그널이 발생한 날짜와 가격
        """
        if sigma_level == 1:
            signals = self.data[self.data['Signal'] >= 1].copy()
        else:
            signals = self.data[self.data['Signal'] == 2].copy()

        return signals[['Close', 'Signal', 'Std_Dev', 'Daily_Std_Dev', 'Price_Change_Pct', 'RSI']]

    def calculate_statistics(self) -> dict:
        """전략 통계 계산"""
        total_days = len(self.data)
        signals_1sigma = len(self.data[self.data['Signal'] >= 1])
        signals_2sigma = len(self.data[self.data['Signal'] == 2])

        return {
            'total_days': total_days,
            'signals_1sigma_count': signals_1sigma,
            'signals_2sigma_count': signals_2sigma,
            'signals_1sigma_per_year': (signals_1sigma / total_days) * 252 if total_days > 0 else 0,
            'signals_2sigma_per_year': (signals_2sigma / total_days) * 252 if total_days > 0 else 0,
            'avg_std_dev': self.data['Std_Dev'].mean() * 100,
            'avg_daily_std_dev': self.data['Daily_Std_Dev'].mean() * 100,
            'current_std_dev': self.data['Std_Dev'].iloc[-1] * 100,
            'current_daily_std_dev': self.data['Daily_Std_Dev'].iloc[-1] * 100,
        }
