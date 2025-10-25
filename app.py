"""
표준편차 매매법 백테스트 대시보드
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import time

from data_fetcher import DataFetcher
from strategy import StandardDeviationStrategy
from backtest import Backtester


# 데이터 가져오기 함수 (캐싱 적용)
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker: str, period: str, extra_days: int = 0):
    """
    주가 데이터 가져오기 (1시간 캐시)

    Args:
        ticker: 종목 티커
        period: 백테스트 기간
        extra_days: 표준편차 계산을 위한 추가 거래일 수
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            fetcher = DataFetcher(ticker)
            data = fetcher.get_historical_data(period=period, extra_days=extra_days)
            info = fetcher.get_info()
            return data, info
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
                continue
            else:
                raise e


@st.cache_data(ttl=3600, show_spinner=False)
def get_available_periods(ticker: str):
    """
    종목의 가능한 데이터 기간 목록 가져오기 (1시간 캐시)

    Args:
        ticker: 종목 티커

    Returns:
        list: 가능한 기간 목록 ['1y', '2y', ...]
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            fetcher = DataFetcher(ticker)
            periods = fetcher.get_available_periods()
            return periods
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            else:
                # 에러 발생 시 기본값 반환
                return ["1y", "2y", "3y", "5y", "max"]


# 페이지 설정
st.set_page_config(
    page_title="표준편차 매매 백테스터",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# TradingView 스타일 CSS
st.markdown("""
<style>
    /* TradingView 다크 테마 색상 - 가독성 개선 */
    :root {
        --tv-bg-primary: #131722;
        --tv-bg-secondary: #1E222D;
        --tv-border: #363A45;
        --tv-text-primary: #FFFFFF;
        --tv-text-secondary: #E8E8E8;
        --tv-blue: #2962FF;
        --tv-green: #26A69A;
        --tv-red: #EF5350;
    }

    /* 메인 배경 */
    .main {
        background-color: var(--tv-bg-primary);
    }

    .stApp {
        background-color: var(--tv-bg-primary);
    }

    /* 헤더 스타일 */
    h1, h2, h3 {
        color: var(--tv-text-primary) !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    }

    p {
        color: var(--tv-text-primary);
    }

    /* 메트릭 카드 */
    .metric-card {
        background: var(--tv-bg-secondary);
        border-radius: 8px;
        padding: 20px;
        border: 1px solid var(--tv-border);
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }

    /* 사이드바 */
    [data-testid="stSidebar"] {
        background-color: var(--tv-bg-secondary);
        border-right: 1px solid var(--tv-border);
    }

    [data-testid="stSidebar"] * {
        color: var(--tv-text-primary) !important;
    }

    /* 버튼 */
    .stButton>button {
        background-color: var(--tv-blue);
        color: white;
        border-radius: 6px;
        border: none;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        background-color: #1E53E5;
        box-shadow: 0 4px 12px rgba(41, 98, 255, 0.4);
    }

    /* 입력 필드 */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stSelectbox>div>div>select {
        background-color: #2A2E39;
        color: var(--tv-text-primary);
        border: 1px solid #434651;
        border-radius: 4px;
    }

    /* 슬라이더 */
    .stSlider>div>div>div>div {
        background-color: var(--tv-blue);
    }

    /* 탭 */
    .stTabs [data-baseweb="tab-list"] {
        background-color: var(--tv-bg-secondary);
        border-radius: 8px 8px 0 0;
        gap: 2px;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: var(--tv-text-secondary);
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--tv-bg-primary);
        color: var(--tv-blue);
    }

    /* 테이블 */
    .dataframe {
        background-color: var(--tv-bg-secondary) !important;
        border: 1px solid var(--tv-border) !important;
        color: var(--tv-text-primary) !important;
    }

    .dataframe th {
        background-color: #2A2E39 !important;
        color: var(--tv-text-primary) !important;
        font-weight: 600 !important;
    }

    .dataframe td {
        color: var(--tv-text-primary) !important;
    }

    /* 성공/경고/정보 메시지 */
    .stSuccess, .stWarning, .stInfo {
        background-color: var(--tv-bg-secondary);
        border: 1px solid var(--tv-border);
        color: var(--tv-text-primary);
    }

    /* 체크박스 */
    .stCheckbox>label {
        color: var(--tv-text-primary);
    }

    /* 라디오 버튼 */
    .stRadio>label {
        color: var(--tv-text-primary);
    }

    /* 레이블 */
    label {
        color: var(--tv-text-primary) !important;
    }

    /* 도움말 텍스트 */
    .stMarkdown small {
        color: var(--tv-text-secondary) !important;
    }
</style>
""", unsafe_allow_html=True)

# 헤더
st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <h1 style='margin-bottom: 5px;'>📊 표준편차 매매 백테스터</h1>
    <p style='font-size: 16px; opacity: 0.9;'>Statistical Trading Strategy Analyzer</p>
</div>
""", unsafe_allow_html=True)

# 표준편차 매매법 설명
with st.expander("📖 표준편차 매매법이란?", expanded=False):
    st.markdown("""
    ### 🎯 거래 방식

    **표준편차 매매법**은 통계적 평균 회귀(Mean Reversion) 원리를 활용한 매매 전략입니다.

    #### 📉 매수 타이밍
    - 주가가 20일 이동평균선(MA20)에서 **1σ(표준편차) 또는 2σ 이상 하락**했을 때 매수합니다
    - 1σ 하락: 통계적으로 연간 약 20회 발생 (약 16% 하락)
    - 2σ 하락: 통계적으로 연간 약 10회 발생 (약 32% 하락)

    #### 📈 매도 타이밍
    - **목표 수익률 달성** 시 매도
    - **이동평균선 회귀** 시 매도 (옵션)
    - **손절선/트레일링 스톱** 도달 시 매도 (옵션)

    ---

    ### 💡 기대 효과

    #### 1. 통계적 확률 기반 저가 매수
    - 정규분포 원리상 과도하게 하락한 주가는 평균으로 회귀하려는 성질이 있습니다
    - 감정적 판단이 아닌 **객관적 통계 지표**로 매수 시점을 포착합니다

    #### 2. 변동성을 수익으로 전환
    - 특히 **레버리지 ETF**(QLD, TQQQ, SOXL 등)의 높은 변동성을 활용합니다
    - 큰 하락 후 반등 시 높은 수익률을 기대할 수 있습니다

    #### 3. 분산 매수를 통한 리스크 관리
    - 여러 차례에 걸쳐 분할 매수하여 평균 단가를 낮춥니다
    - 추가 하락 시에도 더 좋은 가격에 매수 기회를 얻습니다

    #### 4. 체계적인 위험 관리
    - 손절선, 트레일링 스톱으로 손실을 제한합니다
    - 손절 후 쿨다운 기간을 두어 연속 손실을 방지합니다

    ---

    ⚠️ **주의사항**: 이 전략은 과거 데이터 기반 백테스트이며, 미래 수익을 보장하지 않습니다.
    레버리지 ETF는 높은 변동성과 시간 가치 감소 위험이 있으므로 충분히 이해하고 투자하시기 바랍니다.
    """)

# 사이드바 설정
st.sidebar.header("⚙️ 설정")

# 종목 입력
ticker = st.sidebar.text_input(
    "종목 티커",
    value="QLD",
    help="예: QLD, SOXL, TQQQ, SPY, NVDA 등"
).upper()

# 데이터 기간 (티커별 가능한 기간 동적 생성)
try:
    with st.spinner(f"{ticker} 가능 기간 확인 중..."):
        available_periods = get_available_periods(ticker)

    # 5y가 있으면 그걸 기본값으로, 없으면 마지막에서 두 번째 (max 제외한 가장 긴 기간)
    if "5y" in available_periods:
        default_index = available_periods.index("5y")
    elif len(available_periods) > 1:
        # max를 제외한 가장 긴 기간
        default_index = len(available_periods) - 2 if available_periods[-1] == "max" else len(available_periods) - 1
    else:
        default_index = 0

    period = st.sidebar.selectbox(
        "데이터 기간",
        options=available_periods,
        index=default_index,
        help=f"백테스트에 사용할 과거 데이터 기간 (상장일부터 사용 가능)"
    )
except Exception as e:
    st.sidebar.warning(f"⚠️ 기간 목록을 가져올 수 없습니다. 기본값을 사용합니다.")
    period = st.sidebar.selectbox(
        "데이터 기간",
        options=["1y", "2y", "3y", "5y", "max"],
        index=3,
        help="백테스트에 사용할 과거 데이터 기간"
    )

# 표준편차 계산 기간
lookback = st.sidebar.number_input(
    "표준편차 계산 기간 (거래일)",
    min_value=50,
    max_value=500,
    value=252,
    step=10,
    help="1년 = 252 거래일"
)

st.sidebar.markdown("---")
st.sidebar.subheader("백테스트 설정")

# 초기 자본금
initial_capital = st.sidebar.number_input(
    "초기 자본금 ($)",
    min_value=1000,
    max_value=1000000,
    value=10000,
    step=1000
)

# 1회 매수 금액
position_size = st.sidebar.number_input(
    "1회 매수 금액 ($)",
    min_value=100,
    max_value=100000,
    value=1000,
    step=100
)

# 매수 기준
sigma_level = st.sidebar.radio(
    "매수 시그널 기준",
    options=[1, 2],
    format_func=lambda x: f"{x}σ (표준편차)",
    help="1σ: 연간 약 20회 / 2σ: 연간 약 10회"
)

# 목표 수익률
take_profit = st.sidebar.slider(
    "목표 수익률 (%)",
    min_value=5,
    max_value=900,
    value=900,
    step=5,
    help="""
    매수가 대비 목표 수익률 달성 시 매도합니다.

    📊 효과:
    • 낮은 값 (5-20%): 빠른 수익 실현, 거래 횟수 증가, 큰 상승 추세 놓칠 수 있음
    • 중간 값 (20-100%): 균형잡힌 전략, 적당한 수익과 거래 빈도
    • 높은 값 (100%+): 큰 수익 추구, 거래 횟수 감소, 조정 시 미실현 손실 위험

    💡 레버리지 ETF는 변동성이 크므로 높은 목표 수익률도 달성 가능합니다.
    """
)

# 이동평균선 매도 사용
use_ma_exit = st.sidebar.checkbox(
    "이동평균선(MA20) 회귀 시 매도",
    value=False,
    help="가격이 MA20을 상향 돌파하면 매도"
)

st.sidebar.markdown("---")
st.sidebar.subheader("위험 관리")

# 손절선 (Stop Loss)
use_stop_loss = st.sidebar.checkbox(
    "손절선 사용",
    value=False,
    help="매수가 대비 일정 비율 이상 손실 시 매도"
)

stop_loss_pct = st.sidebar.slider(
    "손절 비율 (%)",
    min_value=1,
    max_value=50,
    value=10,
    step=1,
    disabled=not use_stop_loss,
    help="매수가 대비 -n% 하락 시 손절 매도"
)

# 트레일링 스톱 (Trailing Stop)
use_trailing_stop = st.sidebar.checkbox(
    "트레일링 스톱 사용",
    value=True,
    help="보유 중 최고가 대비 일정 비율 하락 시 매도"
)

trailing_stop_pct = st.sidebar.slider(
    "트레일링 스톱 비율 (%)",
    min_value=1,
    max_value=50,
    value=30,
    step=1,
    disabled=not use_trailing_stop,
    help="보유 중 최고가 대비 -n% 하락 시 매도"
)

# 손절 후 대기 기간 (Cooldown Period)
cooldown_months = st.sidebar.number_input(
    "손절 후 대기 기간 (개월)",
    min_value=0,
    max_value=12,
    value=0,
    step=1,
    help="Stop Loss 또는 Trailing Stop 후 N개월 동안 매수를 금지합니다 (0=대기없음)"
)

if cooldown_months > 0:
    st.sidebar.info(f"💡 손절 후 {cooldown_months}개월 동안 매수가 금지됩니다.")

st.sidebar.markdown("---")
st.sidebar.subheader("Buy & Hold 설정")

# 데이터 기간에 따른 개월수 계산
if period.lower() == "max":
    default_months = 120  # max는 10년(120개월)으로 설정
elif period.lower().endswith('y'):
    # "10y" -> 10 * 12 = 120개월
    years = int(period[:-1])
    default_months = years * 12
else:
    default_months = 12  # 기본값

# Buy & Hold 분할 매수
buy_hold_splits = st.sidebar.number_input(
    "분할 매수 기간 (개월)",
    min_value=1,
    max_value=240,
    value=default_months,
    step=1,
    help="Buy & Hold 전략 시 n개월 동안 매월 첫 거래일에 분할 매수 (Dollar Cost Averaging)"
)

if buy_hold_splits > 1:
    st.sidebar.info(f"💡 {buy_hold_splits}개월 동안 매월 첫 거래일에 균등 매수합니다.")

# Buy & Hold 위험 관리 적용
buy_hold_use_risk_mgmt = st.sidebar.checkbox(
    "Buy & Hold에도 위험 관리 적용",
    value=False,
    help="체크 시 Buy & Hold 전략에도 손절선, 트레일링 스톱, 목표 수익률이 적용됩니다"
)

# 데이터 로드 버튼
if st.sidebar.button("🔄 분석 시작", type="primary"):
    try:
        with st.spinner(f"{ticker} 데이터를 가져오는 중..."):
            # 캐싱된 함수로 데이터 가져오기
            # 표준편차 계산용으로 lookback 기간만큼 추가 데이터 요청
            data, info = fetch_stock_data(ticker, period, extra_days=lookback)

            # 표준편차 계산용 + 백테스트용 최소 데이터 확인
            min_required = lookback + 100  # lookback + 최소 100일의 백테스트 기간
            if len(data) < min_required:
                st.error(f"데이터가 충분하지 않습니다. 최소 {min_required}일의 데이터가 필요합니다 (현재: {len(data)}일).")
                st.stop()

            st.success(f"✅ {info['name']} 데이터 로드 완료! (총 {len(data)}일)")

            # 전략 적용
            with st.spinner("전략 계산 중..."):
                strategy = StandardDeviationStrategy(data, lookback_period=lookback)
                current_stats = strategy.get_current_stats()
                overall_stats = strategy.calculate_statistics()

            # 백테스트 실행
            with st.spinner("백테스트 실행 중..."):
                backtester = Backtester(
                    data=strategy.data,
                    initial_capital=initial_capital,
                    position_size=position_size,
                    sigma_level=sigma_level,
                    take_profit_pct=take_profit,
                    use_ma_exit=use_ma_exit,
                    use_stop_loss=use_stop_loss,
                    stop_loss_pct=stop_loss_pct,
                    use_trailing_stop=use_trailing_stop,
                    trailing_stop_pct=trailing_stop_pct,
                    cooldown_months=cooldown_months,
                    buy_hold_splits=buy_hold_splits,
                    buy_hold_use_risk_mgmt=buy_hold_use_risk_mgmt
                )
                backtest_results = backtester.run()

            # 결과 저장 (세션 상태)
            st.session_state['ticker'] = ticker
            st.session_state['data'] = data
            st.session_state['strategy'] = strategy
            st.session_state['current_stats'] = current_stats
            st.session_state['overall_stats'] = overall_stats
            st.session_state['backtest_results'] = backtest_results
            st.session_state['info'] = info

    except Exception as e:
        st.error(f"❌ 오류 발생: {str(e)}")

        # 도움말 표시
        with st.expander("💡 문제 해결 방법"):
            st.markdown("""
            **일반적인 오류 해결:**

            1. **종목 티커 확인**
               - 올바른 티커인지 확인 (예: SOXL, TQQQ, SPY)
               - [Yahoo Finance](https://finance.yahoo.com)에서 검색 가능

            2. **데이터 로드 실패**
               - 잠시 후 다시 시도
               - 다른 종목으로 테스트

            3. **메모리 부족**
               - 데이터 기간을 줄여보세요 (2y → 1y)
               - 브라우저 새로고침

            4. **연결 문제**
               - 인터넷 연결 확인
               - VPN 사용 시 해제 후 시도
            """)
        st.stop()

# 결과 표시
if 'backtest_results' in st.session_state:
    ticker = st.session_state['ticker']
    data = st.session_state['data']
    strategy = st.session_state['strategy']
    current_stats = st.session_state['current_stats']
    overall_stats = st.session_state['overall_stats']
    backtest_results = st.session_state['backtest_results']
    info = st.session_state['info']

    # 탭 생성
    tab1, tab2, tab3, tab4 = st.tabs(["📊 현재 분석", "📈 백테스트 결과", "💹 차트", "📋 거래 내역"])

    # 탭 1: 현재 분석
    with tab1:
        st.markdown(f"## {ticker} - {info['name']}")
        st.markdown("<br>", unsafe_allow_html=True)

        # 메트릭 카드 (3단 그리드)
        col1, col2, col3 = st.columns(3)

        with col1:
            price_change = ((current_stats['current_price'] - current_stats['ma_20']) / current_stats['ma_20']) * 100
            color = "#26A69A" if price_change > 0 else "#EF5350"
            st.markdown(f"""
            <div class='metric-card'>
                <p style='color: #E8E8E8; margin: 0; font-size: 14px;'>현재 가격</p>
                <p style='color: #FFFFFF; font-size: 36px; font-weight: 700; margin: 10px 0;'>
                    ${current_stats['current_price']:.2f}
                </p>
                <p style='color: {color}; margin: 0; font-size: 16px;'>
                    MA20 대비 {price_change:+.2f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <p style='color: #E8E8E8; margin: 0; font-size: 14px;'>1σ 매수 가격</p>
                <p style='color: #2962FF; font-size: 36px; font-weight: 700; margin: 10px 0;'>
                    ${current_stats['buy_1sigma_price']:.2f}
                </p>
                <p style='color: #E8E8E8; margin: 0; font-size: 16px;'>
                    현재가 대비 {((current_stats['buy_1sigma_price'] - current_stats['current_price']) / current_stats['current_price'] * 100):.1f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class='metric-card'>
                <p style='color: #E8E8E8; margin: 0; font-size: 14px;'>2σ 매수 가격</p>
                <p style='color: #EF5350; font-size: 36px; font-weight: 700; margin: 10px 0;'>
                    ${current_stats['buy_2sigma_price']:.2f}
                </p>
                <p style='color: #E8E8E8; margin: 0; font-size: 16px;'>
                    현재가 대비 {((current_stats['buy_2sigma_price'] - current_stats['current_price']) / current_stats['current_price'] * 100):.1f}%
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 추가 지표 (4단 그리드)
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.markdown(f"""
            <div class='metric-card' style='text-align: center;'>
                <p style='color: #E8E8E8; margin: 0; font-size: 14px;'>연율화 표준편차</p>
                <p style='color: #2962FF; font-size: 28px; font-weight: 700; margin: 10px 0;'>
                    {current_stats['std_dev_pct']:.2f}%
                </p>
                <p style='color: #9E9E9E; font-size: 12px; margin: -4px 0 0;'>일간 σ: {current_stats['daily_std_dev_pct']:.2f}%</p>
            </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
            <div class='metric-card' style='text-align: center;'>
                <p style='color: #E8E8E8; margin: 0; font-size: 14px;'>RSI</p>
                <p style='color: #2962FF; font-size: 28px; font-weight: 700; margin: 10px 0;'>
                    {current_stats['rsi']:.1f}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
            <div class='metric-card' style='text-align: center;'>
                <p style='color: #E8E8E8; margin: 0; font-size: 14px;'>MA20</p>
                <p style='color: #FFA726; font-size: 28px; font-weight: 700; margin: 10px 0;'>
                    ${current_stats['ma_20']:.2f}
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col4:
            signal_text = {0: "관망", 1: "1σ 매수", 2: "2σ 매수"}
            signal_color_map = {0: "#E8E8E8", 1: "#26A69A", 2: "#2962FF"}
            signal_val = int(current_stats['signal'])
            st.markdown(f"""
            <div class='metric-card' style='text-align: center;'>
                <p style='color: #E8E8E8; margin: 0; font-size: 14px;'>현재 시그널</p>
                <p style='color: {signal_color_map[signal_val]}; font-size: 24px; font-weight: 700; margin: 10px 0;'>
                    {signal_text[signal_val]}
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 통계 정보
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 전략 통계")
            st.write(f"- **분석 기간**: {overall_stats['total_days']}일")
            st.write(f"- **평균 표준편차 (연율화)**: {overall_stats['avg_std_dev']:.2f}%")
            st.write(f"- **평균 일간 표준편차**: {overall_stats['avg_daily_std_dev']:.2f}%")
            st.write(f"- **현재 표준편차 (연율화)**: {overall_stats['current_std_dev']:.2f}%")
            st.write(f"- **현재 일간 표준편차**: {overall_stats['current_daily_std_dev']:.2f}%")

        with col2:
            st.subheader("🎯 매수 기회")
            st.write(f"- **1σ 시그널**: {overall_stats['signals_1sigma_count']}회")
            st.write(f"- **2σ 시그널**: {overall_stats['signals_2sigma_count']}회")
            st.write(f"- **연간 1σ 시그널**: {overall_stats['signals_1sigma_per_year']:.1f}회")
            st.write(f"- **연간 2σ 시그널**: {overall_stats['signals_2sigma_per_year']:.1f}회")

        # 최근 매수 시그널
        st.subheader(f"🔔 최근 {sigma_level}σ 매수 시그널")
        signals = strategy.get_buy_signals(sigma_level=sigma_level)
        if not signals.empty:
            recent_signals = signals.tail(10).sort_index(ascending=False)
            recent_signals_display = recent_signals.rename(columns={
                'Std_Dev': 'Annualized_Std_Dev'
            })
            st.dataframe(
                recent_signals_display.style.format({
                    'Close': '${:.2f}',
                    'Annualized_Std_Dev': '{:.2%}',
                    'Daily_Std_Dev': '{:.2%}',
                    'Price_Change_Pct': '{:.2f}%',
                    'RSI': '{:.1f}'
                }),
                use_container_width=True
            )
        else:
            st.info("매수 시그널이 발생하지 않았습니다.")

    # 탭 2: 백테스트 결과
    with tab2:
        st.header("📊 백테스트 성과 비교")

        # 비교 테이블 - 주요 성과 지표
        buy_hold_stats = backtest_results.get('buy_hold_stats', {})

        # 섹션 1: 수익성 지표
        st.subheader("💰 수익성 지표")
        performance_df = pd.DataFrame({
            '지표': [
                '초기 자본',
                '총 매수 금액',
                '최종 자산',
                '총 수익률',
                '연평균 수익률 (CAGR)'
            ],
            '표준편차 매매법': [
                f"${backtest_results['initial_capital']:,.2f}",
                f"${backtest_results['total_invested']:,.2f}",
                f"${backtest_results['final_value']:,.2f}",
                f"{backtest_results['total_return_pct']:.2f}%",
                f"{backtest_results['cagr']:.2f}%"
            ],
            f"Buy & Hold ({backtest_results['buy_hold_n_splits']}개월)": [
                f"${backtest_results['initial_capital']:,.2f}",
                f"${backtest_results['buy_hold_total_invested']:,.2f}",
                f"${backtest_results['buy_hold_final_value']:,.2f}",
                f"{backtest_results['buy_hold_return_pct']:.2f}%",
                f"{backtest_results['buy_hold_cagr']:.2f}%"
            ]
        })

        st.dataframe(performance_df, use_container_width=True, hide_index=True)

        # 섹션 2: 위험 조정 성과 지표
        st.subheader("📈 위험 조정 성과 지표")
        st.caption("높을수록 위험 대비 수익이 좋음을 의미합니다.")
        risk_adjusted_df = pd.DataFrame({
            '지표': [
                '샤프 비율 (Sharpe Ratio)',
                '소티노 비율 (Sortino Ratio)',
                '칼마 비율 (Calmar Ratio)'
            ],
            '표준편차 매매법': [
                f"{backtest_results['sharpe_ratio']:.2f}",
                f"{backtest_results['sortino_ratio']:.2f}",
                f"{backtest_results['calmar_ratio']:.2f}"
            ],
            f"Buy & Hold ({backtest_results['buy_hold_n_splits']}개월)": [
                f"{backtest_results['buy_hold_sharpe']:.2f}",
                "N/A",
                f"{backtest_results['buy_hold_calmar']:.2f}"
            ]
        })

        st.dataframe(risk_adjusted_df, use_container_width=True, hide_index=True)

        # 섹션 3: 위험 지표
        st.subheader("⚠️ 위험 지표")
        risk_df = pd.DataFrame({
            '지표': [
                '최대 낙폭 (MDD)',
                '변동성 (연율화)'
            ],
            '표준편차 매매법': [
                f"{backtest_results['max_drawdown_pct']:.2f}%",
                f"{backtest_results['volatility']:.2f}%"
            ],
            f"Buy & Hold ({backtest_results['buy_hold_n_splits']}개월)": [
                f"{backtest_results['buy_hold_mdd']:.2f}%",
                f"{backtest_results['buy_hold_volatility']:.2f}%"
            ]
        })

        st.dataframe(risk_df, use_container_width=True, hide_index=True)

        # 섹션 4: 거래 지표
        st.subheader("💼 거래 지표")
        trading_df = pd.DataFrame({
            '지표': [
                '총 매수 횟수',
                '총 매도 횟수',
                '승률',
                '손익비 (Profit Factor)',
                '평균 보유 기간',
                '평균 수익 거래',
                '평균 손실 거래'
            ],
            '표준편차 매매법': [
                f"{backtest_results['buy_count']}회",
                f"{backtest_results['sell_count']}회",
                f"{backtest_results['win_rate']:.1f}%",
                f"{backtest_results['profit_factor']:.2f}",
                f"{backtest_results['avg_holding_days']:.1f}일",
                f"{backtest_results['avg_win_pct']:.2f}%",
                f"{backtest_results['avg_loss_pct']:.2f}%"
            ],
            f"Buy & Hold ({backtest_results['buy_hold_n_splits']}개월)": [
                f"{backtest_results['buy_hold_buy_count']}회",
                f"{backtest_results['buy_hold_sell_count']}회" if backtest_results['buy_hold_sell_count'] > 0 else "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A",
                "N/A"
            ]
        })

        st.dataframe(trading_df, use_container_width=True, hide_index=True)

        # 지표 설명
        with st.expander("📖 주요 지표 설명"):
            st.markdown("""
            ### 수익성 지표
            - **CAGR (연평균 복리 수익률)**: 투자 기간을 연 단위로 환산한 복리 수익률. 장기 성과 비교에 유용합니다.

            ### 위험 조정 성과 지표
            - **샤프 비율**: 위험 대비 초과 수익률. 1 이상이면 양호, 2 이상이면 우수합니다.
            - **소티노 비율**: 샤프 비율과 유사하지만 하방 변동성만 고려. 손실 위험에 더 집중한 지표입니다.
            - **칼마 비율**: 연평균 수익률을 최대 낙폭으로 나눈 값. 낙폭 대비 수익성을 평가합니다.

            ### 위험 지표
            - **MDD (최대 낙폭)**: 최고점 대비 최대 하락폭. 투자자가 경험할 수 있는 최악의 손실입니다.
            - **변동성**: 수익률의 표준편차 (연율화). 가격 변동의 크기를 측정합니다.

            ### 거래 지표
            - **총 매수 횟수**: 매수한 총 횟수입니다.
            - **총 매도 횟수**: 매도한 총 횟수입니다. 승률은 매도 횟수 기준입니다.
            - **손익비 (Profit Factor)**: 총 이익 / 총 손실. 1보다 커야 수익 전략입니다.
            - **승률**: 전체 거래 중 수익을 낸 거래의 비율입니다.

            💡 **총 매수 금액 vs 초기 자본**: 총 매수 금액은 재투자를 포함한 누적 금액이므로 초기 자본보다 클 수 있습니다.
            """)

        st.markdown("---")

        # 초과 수익률 강조
        outperformance = backtest_results['total_return_pct'] - backtest_results['buy_hold_return_pct']
        cagr_outperformance = backtest_results['cagr'] - backtest_results['buy_hold_cagr']

        col1, col2 = st.columns(2)
        with col1:
            if outperformance > 0:
                st.success(f"✅ **총 수익률 차이**\n\n표준편차 매매법이 Buy & Hold 대비 **{outperformance:+.2f}%** 초과 수익")
            elif outperformance < 0:
                st.warning(f"⚠️ **총 수익률 차이**\n\n표준편차 매매법이 Buy & Hold 대비 **{outperformance:.2f}%** 저조")
            else:
                st.info("ℹ️ **총 수익률 차이**\n\n표준편차 매매법과 Buy & Hold의 수익률이 동일합니다")

        with col2:
            if cagr_outperformance > 0:
                st.success(f"✅ **CAGR 차이**\n\n표준편차 매매법이 Buy & Hold 대비 **{cagr_outperformance:+.2f}%** 높음")
            elif cagr_outperformance < 0:
                st.warning(f"⚠️ **CAGR 차이**\n\n표준편차 매매법이 Buy & Hold 대비 **{cagr_outperformance:.2f}%** 낮음")
            else:
                st.info("ℹ️ **CAGR 차이**\n\n표준편차 매매법과 Buy & Hold의 CAGR이 동일합니다")

        st.markdown("---")

        # 분할 매수 상세 정보 (2개월 이상일 때만)
        if backtest_results['buy_hold_n_splits'] > 1:
            with st.expander(f"📅 {backtest_results['buy_hold_n_splits']}개월 DCA 매수 상세 내역"):
                buy_points_df = pd.DataFrame(backtest_results['buy_hold_buy_points'])
                buy_points_df['date'] = pd.to_datetime(buy_points_df['date'])

                st.dataframe(
                    buy_points_df.style.format({
                        'price': '${:.2f}',
                        'shares': '{:.4f}주',
                        'amount': '${:.2f}'
                    }),
                    use_container_width=True
                )

        # Buy & Hold 거래 내역 (위험 관리 적용 시)
        buy_hold_stats = backtest_results.get('buy_hold_stats', {})
        if buy_hold_stats.get('use_risk_mgmt', False) and buy_hold_stats.get('trades'):
            with st.expander(f"📊 Buy & Hold 거래 내역 (위험 관리 적용) - {len(buy_hold_stats['trades'])}건"):
                bh_trades_df = pd.DataFrame(buy_hold_stats['trades'])
                st.dataframe(
                    bh_trades_df.style.format({
                        'buy_price': '${:.2f}',
                        'sell_price': '${:.2f}',
                        'shares': '{:.4f}',
                        'profit_pct': '{:.2f}%',
                        'profit_amount': '${:.2f}'
                    }),
                    use_container_width=True
                )

                # 위험 관리 통계
                st.write("**매도 사유별 통계:**")
                sell_reasons = bh_trades_df['sell_reason'].value_counts()
                for reason, count in sell_reasons.items():
                    st.write(f"- {reason}: {count}회")

        # 포트폴리오 가치 변화 차트 (TradingView 스타일)
        st.subheader("📈 포트폴리오 가치 변화")
        portfolio_df = backtest_results['portfolio_df']

        fig_portfolio = go.Figure()

        # 표준편차 매매법 (면적 차트)
        fig_portfolio.add_trace(go.Scatter(
            x=portfolio_df['date'],
            y=portfolio_df['total_value'],
            mode='lines',
            name='표준편차 매매법',
            line=dict(color='#2962FF', width=3),
            fill='tozeroy',
            fillcolor='rgba(41, 98, 255, 0.1)'
        ))

        # Buy & Hold
        fig_portfolio.add_trace(go.Scatter(
            x=portfolio_df['date'],
            y=backtest_results['buy_hold_portfolio_values'],
            mode='lines',
            name='Buy & Hold',
            line=dict(color='#E8E8E8', width=2, dash='dash')
        ))

        # 초기 자본 기준선
        fig_portfolio.add_hline(
            y=initial_capital,
            line_dash="dot",
            line_color="#2A2E39",
            annotation_text="초기 자본",
            annotation_position="right"
        )

        # TradingView 스타일 적용
        fig_portfolio.update_layout(
            template='plotly_dark',
            paper_bgcolor='#131722',
            plot_bgcolor='#1E222D',
            font=dict(
                family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif",
                color='#FFFFFF'
            ),
            xaxis=dict(
                gridcolor='#2A2E39',
                showgrid=True,
                zeroline=False
            ),
            yaxis=dict(
                gridcolor='#2A2E39',
                showgrid=True,
                zeroline=False,
                side='right',
                tickprefix='$'
            ),
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(30, 34, 45, 0.8)',
                bordercolor='#2A2E39',
                borderwidth=1
            ),
            height=500,
            margin=dict(l=0, r=80, t=40, b=0)
        )

        st.plotly_chart(fig_portfolio, use_container_width=True, config={'displayModeBar': False})

    # 탭 3: 차트
    with tab3:
        st.header("가격 차트 & 표준편차 밴드")

        # 차트 기간 선택
        chart_period = st.selectbox(
            "표시 기간",
            options=["전체", "최근 6개월", "최근 3개월", "최근 1개월"],
            index=1
        )

        # 데이터 필터링
        chart_data = strategy.data.copy()
        if chart_period == "최근 6개월":
            chart_data = chart_data.tail(126)
        elif chart_period == "최근 3개월":
            chart_data = chart_data.tail(63)
        elif chart_period == "최근 1개월":
            chart_data = chart_data.tail(21)

        # TradingView 스타일 서브플롯 생성
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            row_heights=[0.7, 0.3],
            subplot_titles=('', '')
        )

        # 캔들스틱 차트 (TradingView 스타일)
        fig.add_trace(
            go.Candlestick(
                x=chart_data.index,
                open=chart_data['Open'],
                high=chart_data['High'],
                low=chart_data['Low'],
                close=chart_data['Close'],
                increasing_line_color='#26A69A',  # TradingView 상승
                decreasing_line_color='#EF5350',  # TradingView 하락
                increasing_fillcolor='#26A69A',
                decreasing_fillcolor='#EF5350',
                name='가격'
            ),
            row=1, col=1
        )

        # 표준편차 밴드 (상단)
        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['Sell_2Sigma'],
                mode='lines',
                name='+2σ',
                line=dict(color='rgba(239, 83, 80, 0.3)', width=1, dash='dot'),
                showlegend=True
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['Sell_1Sigma'],
                mode='lines',
                name='+1σ',
                line=dict(color='rgba(239, 83, 80, 0.5)', width=1, dash='dash'),
                showlegend=True
            ),
            row=1, col=1
        )

        # 표준편차 밴드 (하단)
        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['Buy_1Sigma'],
                mode='lines',
                name='-1σ',
                line=dict(color='rgba(41, 98, 255, 0.5)', width=2),
                showlegend=True
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['Buy_2Sigma'],
                mode='lines',
                name='-2σ',
                line=dict(color='rgba(41, 98, 255, 0.3)', width=1, dash='dash'),
                fill='tonexty',
                fillcolor='rgba(41, 98, 255, 0.05)',
                showlegend=True
            ),
            row=1, col=1
        )

        # 이동평균선
        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['MA_20'],
                mode='lines',
                name='MA20',
                line=dict(color='#FFA726', width=1.5),
                showlegend=True
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['MA_60'],
                mode='lines',
                name='MA60',
                line=dict(color='#AB47BC', width=1.5),
                showlegend=True
            ),
            row=1, col=1
        )

        # 매수 시그널 마커
        buy_signals = chart_data[chart_data['Signal'] > 0]
        if not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals['Low'] * 0.98,  # 캔들 아래에 표시
                    mode='markers',
                    name='매수 시그널',
                    marker=dict(
                        symbol='triangle-up',
                        size=12,
                        color=['#26A69A' if s == 1 else '#2962FF' for s in buy_signals['Signal']],
                        line=dict(color='white', width=1)
                    ),
                    showlegend=True
                ),
                row=1, col=1
            )

        # RSI 차트 (하단)
        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='#2962FF', width=2),
                fill='tozeroy',
                fillcolor='rgba(41, 98, 255, 0.1)',
                showlegend=False
            ),
            row=2, col=1
        )

        # RSI 과매수/과매도 라인
        fig.add_hline(
            y=70,
            line_dash="dash",
            line_color="rgba(239, 83, 80, 0.5)",
            row=2, col=1,
            annotation_text="과매수",
            annotation_position="right"
        )
        fig.add_hline(
            y=30,
            line_dash="dash",
            line_color="rgba(38, 166, 154, 0.5)",
            row=2, col=1,
            annotation_text="과매도",
            annotation_position="right"
        )

        # TradingView 스타일 레이아웃
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='#131722',
            plot_bgcolor='#1E222D',
            font=dict(
                family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif",
                color='#FFFFFF',
                size=12
            ),
            xaxis=dict(
                gridcolor='#2A2E39',
                showgrid=True,
                zeroline=False,
                rangeslider_visible=False
            ),
            yaxis=dict(
                gridcolor='#2A2E39',
                showgrid=True,
                zeroline=False,
                side='right'  # TradingView처럼 오른쪽에 y축
            ),
            xaxis2=dict(
                gridcolor='#2A2E39',
                showgrid=True
            ),
            yaxis2=dict(
                gridcolor='#2A2E39',
                showgrid=True,
                side='right',
                range=[0, 100]
            ),
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                bgcolor='rgba(30, 34, 45, 0.8)',
                bordercolor='#2A2E39',
                borderwidth=1
            ),
            margin=dict(l=0, r=80, t=40, b=0),
            height=800
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': True, 'displaylogo': False})

    # 탭 4: 거래 내역
    with tab4:
        st.header("거래 내역")

        trades_df = backtest_results['trades_df']

        if not trades_df.empty:
            # 필터링 옵션
            col1, col2 = st.columns(2)

            with col1:
                trade_filter = st.selectbox(
                    "거래 필터",
                    options=["전체", "수익 거래", "손실 거래"]
                )

            with col2:
                sort_by = st.selectbox(
                    "정렬 기준",
                    options=["날짜 (최신)", "날짜 (오래된)", "수익률 (높은)", "수익률 (낮은)"]
                )

            # 필터 적용
            filtered_trades = trades_df.copy()
            if trade_filter == "수익 거래":
                filtered_trades = filtered_trades[filtered_trades['profit_pct'] > 0]
            elif trade_filter == "손실 거래":
                filtered_trades = filtered_trades[filtered_trades['profit_pct'] < 0]

            # 정렬
            if sort_by == "날짜 (최신)":
                filtered_trades = filtered_trades.sort_values('sell_date', ascending=False)
            elif sort_by == "날짜 (오래된)":
                filtered_trades = filtered_trades.sort_values('sell_date', ascending=True)
            elif sort_by == "수익률 (높은)":
                filtered_trades = filtered_trades.sort_values('profit_pct', ascending=False)
            elif sort_by == "수익률 (낮은)":
                filtered_trades = filtered_trades.sort_values('profit_pct', ascending=True)

            # 테이블 표시
            st.dataframe(
                filtered_trades.style.format({
                    'buy_price': '${:.2f}',
                    'sell_price': '${:.2f}',
                    'shares': '{:.4f}',
                    'profit_pct': '{:.2f}%',
                    'profit_amount': '${:.2f}',
                    'holding_days': '{:.0f}'
                }).applymap(
                    lambda x: 'background-color: #1A4D2E; color: #A8E6CF' if isinstance(x, (int, float)) and x > 0
                    else 'background-color: #4D1A1A; color: #FFADAD' if isinstance(x, (int, float)) and x < 0
                    else '',
                    subset=['profit_pct', 'profit_amount']
                ),
                use_container_width=True
            )

            # 다운로드 버튼
            csv = filtered_trades.to_csv(index=False)
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv,
                file_name=f"{ticker}_trades_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("거래 내역이 없습니다. 백테스트 설정을 조정해보세요.")

else:
    # 초기 화면
    st.info("👈 왼쪽 사이드바에서 종목과 설정을 입력한 후 '분석 시작' 버튼을 클릭하세요.")

    # 빠른 시작 가이드
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("🚀 빠른 시작")
        st.markdown("""
        1. **종목 티커** 입력 (예: QLD, SOXL, TQQQ, SPY)
        2. **백테스트 설정** 조정 (기본값도 좋습니다)
        3. **분석 시작** 클릭
        4. **결과 확인** 및 CSV 다운로드
        """)

    with col2:
        st.subheader("📊 데모 영상")
        st.info("곧 제공 예정")

    st.markdown("---")

    # 예시 종목
    st.subheader("💡 추천 종목")
    st.markdown("""
    **3배 레버리지 ETF:**
    - `SOXL`: 반도체 3배 레버리지
    - `TQQQ`: 나스닥 3배 레버리지
    - `UPRO`: S&P500 3배 레버리지
    - `TMF`: 미국 채권 3배 레버리지

    **2배 레버리지 ETF:**
    - `QLD`: 나스닥 2배 레버리지
    - `SSO`: S&P500 2배 레버리지
    - `UWM`: 러셀2000 2배 레버리지
    - `USD`: 반도체 2배 레버리지

    **일반 ETF:**
    - `SPY`: S&P500
    - `QQQ`: 나스닥100
    - `SMH`: 반도체

    **개별 종목:**
    - `NVDA`: 엔비디아
    - `TSLA`: 테슬라
    - `AAPL`: 애플
    """)

# 푸터
st.markdown("---")
st.caption("표준편차 매매법 대시보드 | 과거 성과가 미래 수익을 보장하지 않습니다.")
