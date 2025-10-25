"""
주가 데이터를 가져오는 모듈
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta


class DataFetcher:
    """야후 파이낸스에서 주가 데이터를 가져오는 클래스"""

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        # User-Agent를 설정하여 403 오류 방지
        self.stock = yf.Ticker(self.ticker)
        # 세션 설정
        import requests
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.stock.session = session

    def get_historical_data(self, period: str = "2y", extra_days: int = 0) -> pd.DataFrame:
        """
        과거 주가 데이터 가져오기

        Args:
            period: 기간 (1y, 2y, 5y, max 등)
            extra_days: 추가로 가져올 거래일 수 (표준편차 계산용 등)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            # max period는 extra_days와 관계없이 그대로 사용
            if period.lower() == "max":
                df = self.stock.history(period="max")
            # extra_days가 있으면 start/end date를 직접 계산
            elif extra_days > 0:
                from datetime import datetime, timedelta

                # period를 일수로 변환
                period_days = self._period_to_days(period)

                # 총 필요 일수 (주말 포함하여 1.5배로 계산)
                total_days = int((period_days + extra_days) * 1.5)

                end_date = datetime.now()
                start_date = end_date - timedelta(days=total_days)

                df = self.stock.history(start=start_date, end=end_date)
            else:
                df = self.stock.history(period=period)

            if df.empty:
                raise ValueError(f"No data found for ticker {self.ticker}")
            return df
        except Exception as e:
            raise Exception(f"Error fetching data for {self.ticker}: {str(e)}")

    def _period_to_days(self, period: str) -> int:
        """period 문자열을 거래일수로 변환"""
        period = period.lower()
        if period.endswith('y'):
            years = int(period[:-1])
            return years * 252  # 1년 = 252 거래일
        elif period.endswith('mo'):
            months = int(period[:-2])
            return months * 21  # 1개월 = 21 거래일
        elif period.endswith('d'):
            return int(period[:-1])
        elif period == 'max':
            return 252 * 20  # 20년으로 가정
        else:
            return 252 * 2  # 기본값 2년

    def get_current_price(self) -> float:
        """현재가 가져오기"""
        try:
            data = self.stock.history(period="1d")
            if data.empty:
                raise ValueError(f"No current price data for {self.ticker}")
            return data['Close'].iloc[-1]
        except Exception as e:
            raise Exception(f"Error fetching current price: {str(e)}")

    def get_info(self) -> dict:
        """종목 정보 가져오기"""
        try:
            info = self.stock.info
            return {
                'name': info.get('longName', self.ticker),
                'sector': info.get('sector', 'N/A'),
                'industry': info.get('industry', 'N/A'),
                'description': info.get('longBusinessSummary', 'N/A')
            }
        except:
            return {
                'name': self.ticker,
                'sector': 'N/A',
                'industry': 'N/A',
                'description': 'N/A'
            }

    def get_first_trade_date(self) -> datetime:
        """
        종목의 최초 거래일(상장일) 가져오기

        Returns:
            datetime: 최초 거래일
        """
        try:
            # max 기간의 데이터 가져오기
            df = self.stock.history(period="max")
            if df.empty:
                raise ValueError(f"No historical data found for {self.ticker}")

            # 첫 거래일 반환
            first_date = df.index[0]
            return first_date
        except Exception as e:
            raise Exception(f"Error fetching first trade date: {str(e)}")

    def get_available_periods(self) -> list:
        """
        종목의 상장일부터 현재까지 1년 단위로 가능한 기간 목록 반환

        Returns:
            list: ['1y', '2y', '3y', ..., '10y', 'max'] 형태의 기간 목록
            - 1년~10년까지는 1년 단위로 표시
            - 10년 이상인 경우 max 옵션 추가
        """
        try:
            first_date = self.get_first_trade_date()
            now = datetime.now()

            # 상장일부터 현재까지의 기간 (년 단위)
            years_available = (now - first_date).days / 365.25

            # 1년부터 10년까지 (또는 데이터가 있는 년수까지 중 작은 값)
            max_year = min(10, int(years_available))
            periods = []
            for year in range(1, max_year + 1):
                periods.append(f"{year}y")

            # 10년 이상 데이터가 있으면 max 옵션 추가
            if years_available > 10:
                periods.append("max")

            return periods if periods else ["1y"]  # 최소한 1y는 반환
        except Exception as e:
            # 에러 발생 시 기본값 반환 (1y~10y, max)
            return ["1y", "2y", "3y", "4y", "5y", "6y", "7y", "8y", "9y", "10y", "max"]
