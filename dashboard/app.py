# dashboard/app.py

import streamlit as st
import pandas as pd
import plotly.express as px
from data_loader import load_db_data, load_latest_qa_report

# --- 페이지 기본 설정 ---
st.set_page_config(
    page_title="🚀 통합 품질 대시보드",
    page_icon="✅",
    layout="wide",
)

st.title("🚀 통합 품질 대시보드")
st.caption("운영, 성능, QA 데이터를 통합하여 애플리케이션의 상태를 한눈에 파악합니다.")

# --- 데이터 로딩 ---
# 로더 함수를 호출하여 데이터 가져오기
db_data = load_db_data()
qa_report, latest_commit, error_msg = load_latest_qa_report()

# --- 탭 구성 ---
tab1, tab2, tab3 = st.tabs(["📊 메인 요약 (Overall Health)", "📈 운영 상태 (Operations)", "📝 품질 보증 (Quality Assurance)"])

# ======================================================================================
# 탭 1: 메인 요약 (Overall Health)
# ======================================================================================
with tab1:
    st.header("✅ 핵심 지표 (Key Performance Indicators)")
    
    col1, col2, col3 = st.columns(3)

    # KPI 1: 최신 테스트 성공률
    if qa_report:
        summary = qa_report.get('summary', {})
        total_tests = summary.get('total', 0)
        passed_tests = summary.get('passed', 0)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        col1.metric("최신 빌드 테스트 성공률", f"{success_rate:.2f}%", f"{passed_tests} / {total_tests} 통과")
    else:
        col1.metric("최신 빌드 테스트 성공률", "N/A", "데이터 로드 실패")

    # KPI 2 & 3: DB 기반 데이터 (예시)
    if db_data and 'time_series_requests' in db_data:
        total_requests_24h = db_data['time_series_requests']['request_count'].sum() # 예시 계산
        avg_response_time = db_data['slowest_10_endpoints']['avg_duration_ms'].mean() # 예시 계산
        col2.metric("최근 24시간 API 총 요청 수", f"{total_requests_24h:,} 건")
        col3.metric("최근 24시간 평균 응답 시간", f"{avg_response_time:.2f} ms")
    else:
        col2.metric("최근 24시간 API 총 요청 수", "N/A")
        col3.metric("최근 24시간 평균 응답 시간", "N/A")

    st.divider()
    
    st.header("🚀 최신 CI/CD 빌드 상태")
    if latest_commit:
        st.success(f"**성공 ✅** - 가장 최근 빌드가 성공적으로 완료되었습니다.")
        st.info(f"**최신 커밋 메시지:** {latest_commit}")
    elif error_msg:
        st.error(f"**실패 ❌** - 빌드 상태를 가져오는 데 실패했습니다: {error_msg}")
    else:
        st.warning("빌드 정보를 찾을 수 없습니다.")

# ======================================================================================
# 탭 2: 운영 상태 (Operations)
# ======================================================================================
with tab2:
    st.header("📈 DB 로그 기반 상세 분석")
    if not db_data:
        st.warning("운영 데이터를 불러올 수 없습니다.")
    else:
        # 상호작용 필터 (예시)
        date_range = st.date_input(
            "데이터 조회 기간을 선택하세요",
            [], # (pd.to_datetime('today') - pd.DateOffset(days=7), pd.to_datetime('today')),
            key="date_filter"
        )
        
        # 1. 시간대별 API 요청 수 추이
        st.subheader("시간대별 API 요청 수")
        if 'time_series_requests' in db_data:
            st.line_chart(db_data['time_series_requests'].set_index('hour'))
        
        col1, col2 = st.columns(2)
        
        # 2. 가장 많이 요청된 엔드포인트
        with col1:
            st.subheader("가장 많이 요청된 엔드포인트 TOP 10")
            if 'top_10_endpoints' in db_data:
                st.bar_chart(db_data['top_10_endpoints'].set_index('endpoint'))
        
        # 3. 가장 느린 엔드포인트
        with col2:
            st.subheader("가장 느린 엔드포인트 TOP 10 (평균 응답속도)")
            if 'slowest_10_endpoints' in db_data:
                st.dataframe(db_data['slowest_10_endpoints'], use_container_width=True)

# ======================================================================================
# 탭 3: 품질 보증 (Quality Assurance)
# ======================================================================================
with tab3:
    st.header("📝 QA 테스트 결과 분석")
    if not qa_report:
        st.warning(f"QA 리포트를 불러올 수 없습니다. 오류: {error_msg}")
    else:
        summary = qa_report.get('summary', {})
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        
        # 1. 테스트 결과 요약 (파이 차트)
        st.subheader("최신 빌드 테스트 결과 요약")
        pie_data = pd.DataFrame({
            '결과': ['성공 (Passed)', '실패 (Failed)'],
            '개수': [passed, failed]
        })
        fig = px.pie(pie_data, values='개수', names='결과', title='테스트 성공/실패 비율',
                     color_discrete_map={'성공 (Passed)': 'green', '실패 (Failed)': 'red'})
        st.plotly_chart(fig, use_container_width=True)
        
        # 2. 실패한 테스트 상세 정보
        if failed > 0:
            st.subheader("❌ 실패한 테스트 상세 정보")
            failed_tests = [test for test in qa_report.get('tests', []) if test.get('outcome') == 'failed']
            
            with st.expander(f"{failed}개의 실패한 테스트 목록 보기"):
                for test in failed_tests:
                    st.error(f"**Test Case:** `{test['nodeid']}`")
                    st.code(test['longrepr'], language='text')