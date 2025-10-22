"""
표준편차 매매법 백테스트 대시보드
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

from data_fetcher import DataFetcher
from strategy import StandardDeviationStrategy
from backtest import Backtester


# 페이지 설정
st.set_page_config(
    page_title="표준편차 매매법 대시보드",
    page_icon="📈",
    layout="wide"
)

st.title("📈 표준편차 매매법 백테스트 대시보드")
st.markdown("""
이 대시보드는 표준편차 매매법의 효과를 다양한 종목에서 테스트할 수 있습니다.

**전략 핵심:**
- 1년(252거래일) 기준 표준편차 계산
- 가격이 1σ 또는 2σ 하락 시 매수
- 목표 수익률 달성 또는 이동평균선 회귀 시 매도
""")

# 사이드바 설정
st.sidebar.header("⚙️ 설정")

# 종목 입력
ticker = st.sidebar.text_input(
    "종목 티커",
    value="SOXL",
    help="예: SOXL, TQQQ, SPY, NVDA 등"
).upper()

# 데이터 기간
period = st.sidebar.selectbox(
    "데이터 기간",
    options=["1y", "2y", "3y", "5y"],
    index=1,
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
    max_value=50,
    value=10,
    step=5
)

# 이동평균선 매도 사용
use_ma_exit = st.sidebar.checkbox(
    "이동평균선(MA20) 회귀 시 매도",
    value=True,
    help="가격이 MA20을 상향 돌파하면 매도"
)

# 데이터 로드 버튼
if st.sidebar.button("🔄 분석 시작", type="primary"):
    with st.spinner(f"{ticker} 데이터를 가져오는 중..."):
        try:
            # 데이터 가져오기
            fetcher = DataFetcher(ticker)
            data = fetcher.get_historical_data(period=period)

            if len(data) < lookback:
                st.error(f"데이터가 충분하지 않습니다. 최소 {lookback}일의 데이터가 필요합니다.")
                st.stop()

            # 종목 정보
            info = fetcher.get_info()

            st.success(f"✅ {info['name']} 데이터 로드 완료!")

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
                    use_ma_exit=use_ma_exit
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
        st.header(f"{ticker} - {info['name']}")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("현재가", f"${current_stats['current_price']:.2f}")
            st.metric("20일 이동평균", f"${current_stats['ma_20']:.2f}")

        with col2:
            st.metric("표준편차 (%)", f"{current_stats['std_dev_pct']:.2f}%")
            st.metric("표준편차 (가격)", f"${current_stats['std_dev_price']:.2f}")

        with col3:
            st.metric("1σ 매수가", f"${current_stats['buy_1sigma_price']:.2f}")
            st.metric("2σ 매수가", f"${current_stats['buy_2sigma_price']:.2f}")

        with col4:
            st.metric("RSI", f"{current_stats['rsi']:.1f}")
            signal_text = {0: "관망", 1: "1σ 매수", 2: "2σ 매수"}
            signal_color = {0: "🟡", 1: "🟢", 2: "🔵"}
            st.metric(
                "현재 시그널",
                f"{signal_color[int(current_stats['signal'])]} {signal_text[int(current_stats['signal'])]}"
            )

        st.markdown("---")

        # 통계 정보
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 전략 통계")
            st.write(f"- **분석 기간**: {overall_stats['total_days']}일")
            st.write(f"- **평균 표준편차**: {overall_stats['avg_std_dev']:.2f}%")
            st.write(f"- **현재 표준편차**: {overall_stats['current_std_dev']:.2f}%")

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
            st.dataframe(
                recent_signals.style.format({
                    'Close': '${:.2f}',
                    'Std_Dev': '{:.2%}',
                    'Price_Change_Pct': '{:.2f}%',
                    'RSI': '{:.1f}'
                }),
                use_container_width=True
            )
        else:
            st.info("매수 시그널이 발생하지 않았습니다.")

    # 탭 2: 백테스트 결과
    with tab2:
        st.header("백테스트 성과")

        # 주요 지표
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "총 수익률",
                f"{backtest_results['total_return_pct']:.2f}%",
                delta=f"{backtest_results['total_return_pct'] - backtest_results['buy_hold_return_pct']:.2f}% vs Buy&Hold"
            )
            st.metric("최종 자산", f"${backtest_results['final_value']:.2f}")

        with col2:
            st.metric("총 거래 횟수", f"{backtest_results['total_trades']}회")
            st.metric("승률", f"{backtest_results['win_rate']:.1f}%")

        with col3:
            st.metric("평균 수익률", f"{backtest_results['avg_profit_pct']:.2f}%")
            st.metric("평균 보유 기간", f"{backtest_results['avg_holding_days']:.1f}일")

        with col4:
            st.metric("최대 수익", f"{backtest_results['max_profit_pct']:.2f}%")
            st.metric("최대 손실", f"{backtest_results['max_loss_pct']:.2f}%")

        st.markdown("---")

        # 비교 차트
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 수익률 비교")
            comparison_data = pd.DataFrame({
                '전략': ['표준편차 매매법', 'Buy & Hold'],
                '수익률 (%)': [
                    backtest_results['total_return_pct'],
                    backtest_results['buy_hold_return_pct']
                ]
            })

            fig = go.Figure(data=[
                go.Bar(
                    x=comparison_data['전략'],
                    y=comparison_data['수익률 (%)'],
                    text=comparison_data['수익률 (%)'].apply(lambda x: f"{x:.2f}%"),
                    textposition='auto',
                    marker_color=['#00cc96' if x > 0 else '#ef553b'
                                  for x in comparison_data['수익률 (%)']]
                )
            ])
            fig.update_layout(
                yaxis_title="수익률 (%)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📈 포트폴리오 가치 변화")
            portfolio_df = backtest_results['portfolio_df']

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=portfolio_df['date'],
                y=portfolio_df['total_value'],
                mode='lines',
                name='포트폴리오 가치',
                line=dict(color='#00cc96', width=2)
            ))
            fig.add_hline(
                y=initial_capital,
                line_dash="dash",
                line_color="gray",
                annotation_text="초기 자본"
            )
            fig.update_layout(
                yaxis_title="가치 ($)",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True)

        # 상세 통계
        st.markdown("---")
        st.subheader("📋 상세 통계")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.write("**수익률 통계**")
            st.write(f"- 평균 수익: {backtest_results['avg_win_pct']:.2f}%")
            st.write(f"- 평균 손실: {backtest_results['avg_loss_pct']:.2f}%")
            st.write(f"- 최대 낙폭(MDD): {backtest_results['max_drawdown_pct']:.2f}%")

        with col2:
            st.write("**거래 통계**")
            st.write(f"- 총 거래: {backtest_results['total_trades']}회")
            st.write(f"- 승률: {backtest_results['win_rate']:.1f}%")
            st.write(f"- 평균 보유: {backtest_results['avg_holding_days']:.1f}일")

        with col3:
            st.write("**비교**")
            st.write(f"- Buy&Hold: {backtest_results['buy_hold_return_pct']:.2f}%")
            st.write(f"- 전략 수익: {backtest_results['total_return_pct']:.2f}%")
            outperformance = backtest_results['total_return_pct'] - backtest_results['buy_hold_return_pct']
            st.write(f"- 초과 수익: {outperformance:.2f}%")

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

        # 서브플롯 생성
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.5, 0.25, 0.25],
            subplot_titles=('가격 & 표준편차 밴드', 'RSI', '매수 시그널')
        )

        # 가격 & 밴드
        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['Sell_2Sigma'],
                mode='lines',
                name='+2σ',
                line=dict(color='rgba(255, 0, 0, 0.3)', dash='dash'),
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
                line=dict(color='rgba(255, 100, 0, 0.3)', dash='dash'),
                showlegend=True
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['MA_20'],
                mode='lines',
                name='MA20',
                line=dict(color='blue', width=1),
                showlegend=True
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['Close'],
                mode='lines',
                name='종가',
                line=dict(color='black', width=2),
                showlegend=True
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['Buy_1Sigma'],
                mode='lines',
                name='-1σ',
                line=dict(color='rgba(0, 200, 0, 0.3)', dash='dash'),
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
                line=dict(color='rgba(0, 255, 0, 0.3)', dash='dash'),
                showlegend=True
            ),
            row=1, col=1
        )

        # 매수 시그널 표시
        buy_signals = chart_data[chart_data['Signal'] > 0]
        if not buy_signals.empty:
            fig.add_trace(
                go.Scatter(
                    x=buy_signals.index,
                    y=buy_signals['Close'],
                    mode='markers',
                    name='매수 시그널',
                    marker=dict(
                        color=['green' if s == 1 else 'blue' for s in buy_signals['Signal']],
                        size=10,
                        symbol='triangle-up'
                    ),
                    showlegend=True
                ),
                row=1, col=1
            )

        # RSI
        fig.add_trace(
            go.Scatter(
                x=chart_data.index,
                y=chart_data['RSI'],
                mode='lines',
                name='RSI',
                line=dict(color='purple', width=2),
                showlegend=False
            ),
            row=2, col=1
        )

        fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

        # 시그널 바
        fig.add_trace(
            go.Bar(
                x=chart_data.index,
                y=chart_data['Signal'],
                name='시그널',
                marker_color=['green' if s == 1 else 'blue' if s == 2 else 'gray'
                              for s in chart_data['Signal']],
                showlegend=False
            ),
            row=3, col=1
        )

        # 레이아웃 업데이트
        fig.update_xaxes(title_text="날짜", row=3, col=1)
        fig.update_yaxes(title_text="가격 ($)", row=1, col=1)
        fig.update_yaxes(title_text="RSI", row=2, col=1)
        fig.update_yaxes(title_text="시그널", row=3, col=1)

        fig.update_layout(
            height=900,
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        st.plotly_chart(fig, use_container_width=True)

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
                    lambda x: 'background-color: #d4edda' if isinstance(x, (int, float)) and x > 0
                    else 'background-color: #f8d7da' if isinstance(x, (int, float)) and x < 0
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

    # 예시 종목
    st.subheader("추천 종목")
    st.markdown("""
    **레버리지 ETF:**
    - `SOXL`: 반도체 3배 레버리지
    - `TQQQ`: 나스닥 3배 레버리지
    - `UPRO`: S&P500 3배 레버리지
    - `TMF`: 미국 채권 3배 레버리지

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
