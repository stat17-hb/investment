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

    def get_historical_data(self, period: str = "2y") -> pd.DataFrame:
        """
        과거 주가 데이터 가져오기

        Args:
            period: 기간 (1y, 2y, 5y, max 등)

        Returns:
            DataFrame with OHLCV data
        """
        try:
            df = self.stock.history(period=period)
            if df.empty:
                raise ValueError(f"No data found for ticker {self.ticker}")
            return df
        except Exception as e:
            raise Exception(f"Error fetching data for {self.ticker}: {str(e)}")

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
