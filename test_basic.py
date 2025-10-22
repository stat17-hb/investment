"""
기본 기능 테스트
"""
import sys

try:
    from data_fetcher import DataFetcher
    from strategy import StandardDeviationStrategy
    from backtest import Backtester

    print("✅ 모든 모듈 임포트 성공!")

    # SOXL 데이터 가져오기 테스트
    print("\n📊 SOXL 데이터 가져오기 중...")
    fetcher = DataFetcher("SOXL")
    data = fetcher.get_historical_data(period="1y")
    print(f"✅ 데이터 로드 성공! {len(data)}일치 데이터")

    # 전략 적용
    print("\n📈 표준편차 매매 전략 적용 중...")
    strategy = StandardDeviationStrategy(data, lookback_period=252)
    stats = strategy.get_current_stats()

    print(f"✅ 전략 적용 성공!")
    print(f"\n📋 현재 통계:")
    print(f"  - 현재가: ${stats['current_price']:.2f}")
    print(f"  - 표준편차: {stats['std_dev_pct']:.2f}%")
    print(f"  - 1σ 매수가: ${stats['buy_1sigma_price']:.2f}")
    print(f"  - 2σ 매수가: ${stats['buy_2sigma_price']:.2f}")
    print(f"  - RSI: {stats['rsi']:.1f}")

    # 백테스트
    print("\n🔄 백테스트 실행 중...")
    backtester = Backtester(
        data=strategy.data,
        initial_capital=10000,
        position_size=1000,
        sigma_level=1,
        take_profit_pct=10
    )
    results = backtester.run()

    print(f"✅ 백테스트 완료!")
    print(f"\n📊 백테스트 결과:")
    print(f"  - 총 수익률: {results['total_return_pct']:.2f}%")
    print(f"  - Buy & Hold: {results['buy_hold_return_pct']:.2f}%")
    print(f"  - 총 거래: {results['total_trades']}회")
    print(f"  - 승률: {results['win_rate']:.1f}%")
    print(f"  - 평균 수익률: {results['avg_profit_pct']:.2f}%")
    print(f"  - 최대 낙폭: {results['max_drawdown_pct']:.2f}%")

    print("\n✅ 모든 테스트 통과!")
    print("\n🚀 대시보드 실행: streamlit run app.py")

except Exception as e:
    print(f"❌ 오류 발생: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
