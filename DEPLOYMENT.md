# 🚀 Streamlit 앱 배포 가이드

이 가이드는 표준편차 매매법 대시보드를 웹에 배포하여 다른 사람들과 공유하는 방법을 설명합니다.

## 📋 목차

1. [로컬 실행](#로컬-실행)
2. [Streamlit Community Cloud 배포 (추천)](#streamlit-community-cloud-배포-추천)
3. [Hugging Face Spaces 배포](#hugging-face-spaces-배포-대안)
4. [문제 해결](#문제-해결)

---

## 로컬 실행

먼저 로컬에서 테스트해보세요:

```bash
# 1. 저장소 클론
git clone <your-repo-url>
cd investment

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 앱 실행
streamlit run app.py
```

브라우저에서 `http://localhost:8501`로 접속하면 대시보드를 볼 수 있습니다.

---

## Streamlit Community Cloud 배포 (추천)

### 장점
- ✅ **완전 무료**
- ✅ **GitHub와 직접 연동**
- ✅ **1분 안에 배포 완료**
- ✅ **자동 업데이트** (코드 푸시 시)
- ✅ **HTTPS 자동 제공**

### 단계별 가이드

#### 1단계: GitHub 리포지토리 준비

코드가 이미 GitHub에 푸시되어 있어야 합니다:

```bash
git push origin <your-branch-name>
```

#### 2단계: Streamlit Community Cloud 계정 만들기

1. [https://share.streamlit.io](https://share.streamlit.io) 접속
2. **Sign up** 또는 **Continue with GitHub** 클릭
3. GitHub 계정으로 로그인

#### 3단계: 앱 배포하기

1. **"New app"** 버튼 클릭
2. 배포 설정:
   ```
   Repository: stat17-hb/investment
   Branch: claude/test-standard-deviation-trading-011CUNJadSgHKbWmXBk3f9jk
   Main file path: app.py
   ```
3. **"Deploy!"** 버튼 클릭

#### 4단계: 배포 완료

- 2~5분 정도 기다리면 배포 완료
- 자동으로 생성된 URL (예: `https://your-app-name.streamlit.app`) 받기
- 이 URL을 다른 사람들과 공유!

### 배포 후 관리

#### 코드 업데이트
```bash
# 코드 수정 후
git add .
git commit -m "Update dashboard"
git push

# Streamlit Cloud가 자동으로 재배포합니다 (약 1-2분 소요)
```

#### 앱 설정 변경
1. Streamlit Cloud 대시보드에서 앱 선택
2. **Settings** 클릭
3. 환경 변수, 리소스 제한 등 설정 가능

#### 로그 확인
- Streamlit Cloud 대시보드에서 **Logs** 탭으로 이동
- 실시간 로그 및 에러 확인 가능

---

## Hugging Face Spaces 배포 (대안)

Streamlit Cloud의 대안으로 Hugging Face Spaces도 좋은 선택입니다.

### 장점
- ✅ 무료 (2GB 스토리지)
- ✅ ML 커뮤니티에 노출
- ✅ GPU 지원 (유료)

### 단계별 가이드

#### 1단계: Hugging Face 계정 만들기

1. [https://huggingface.co](https://huggingface.co) 접속
2. **Sign Up** 클릭

#### 2단계: Space 생성

1. 프로필 → **Spaces** → **Create new Space** 클릭
2. Space 설정:
   ```
   Space name: standard-deviation-trading
   License: MIT
   Space SDK: Streamlit
   ```

#### 3단계: 파일 업로드

필요한 파일들을 업로드:
- `app.py`
- `strategy.py`
- `backtest.py`
- `data_fetcher.py`
- `requirements.txt`
- `README.md`

또는 Git으로 푸시:
```bash
git remote add hf https://huggingface.co/spaces/<username>/standard-deviation-trading
git push hf main
```

#### 4단계: 배포 확인

- URL: `https://huggingface.co/spaces/<username>/standard-deviation-trading`
- 자동으로 빌드 및 배포됩니다

---

## 문제 해결

### 1. yfinance 403 오류

**문제**: Yahoo Finance에서 데이터를 가져올 때 403 Forbidden 오류 발생

**해결 방법**:

#### 옵션 A: 재시도 로직 추가
`data_fetcher.py`에 이미 User-Agent가 설정되어 있습니다. 일시적인 문제일 수 있으므로 몇 초 기다렸다가 다시 시도하세요.

#### 옵션 B: 다른 데이터 소스 사용
- Alpha Vantage API (무료 티어 제공)
- Polygon.io API
- 직접 CSV 파일 업로드 기능 추가

#### 옵션 C: 캐싱 사용
```python
@st.cache_data(ttl=3600)  # 1시간 캐시
def get_data(ticker):
    return fetcher.get_historical_data(period="2y")
```

### 2. 메모리 부족 (Out of Memory)

**문제**: Streamlit Cloud의 1GB RAM 제한 초과

**해결 방법**:
- 데이터 기간 단축 (`2y` → `1y`)
- 캐싱 적극 활용
- 불필요한 컬럼 제거

### 3. 배포가 느림

**원인**: 패키지 설치 시간

**해결 방법**:
- `requirements.txt`에 버전 고정
- 불필요한 패키지 제거
- 더 가벼운 대안 사용

### 4. 앱이 자주 재시작됨

**원인**: 비활성화 시 슬립 모드 진입

**해결 방법**:
- Streamlit Cloud 무료 플랜의 정상 동작
- 첫 접속 시 약 30초 대기
- 유료 플랜 업그레이드 ($20/월)

---

## 📊 리소스 제한

### Streamlit Community Cloud (무료)

| 리소스 | 제한 |
|--------|------|
| RAM | 1 GB |
| CPU | 0.078 cores |
| 스토리지 | 제한 없음 |
| 앱 개수 | 무제한 (공개), 1개 (비공개) |
| 트래픽 | 제한 없음 |

### Hugging Face Spaces (무료)

| 리소스 | 제한 |
|--------|------|
| RAM | 16 GB |
| CPU | 2 cores |
| 스토리지 | 50 GB |
| GPU | 없음 (유료: T4 GPU) |

---

## 🎯 다음 단계

배포 후 추천 작업:

1. **커스텀 도메인 연결** (Streamlit Cloud Pro)
2. **Google Analytics 추가**
3. **사용자 피드백 수집 기능**
4. **실시간 알림 기능** (특정 종목이 매수 시그널 발생 시)
5. **포트폴리오 추적 기능**

---

## 🆘 추가 도움말

- [Streamlit 공식 문서](https://docs.streamlit.io)
- [Streamlit Community Forum](https://discuss.streamlit.io)
- [Streamlit Gallery](https://streamlit.io/gallery) - 다른 앱 예시

---

**배포 성공을 기원합니다!** 🚀

문제가 발생하면 GitHub Issues에 질문을 남겨주세요.
