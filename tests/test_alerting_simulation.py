import pytest
import pandas as pd
from sqlalchemy import text

# 1. 이전 테스트에서 사용했던 헬퍼 함수와 새로 만든 알림 함수를 가져옵니다.
from tests.test_analysis_queries import load_queries_from_file
from app.services.alerting import send_email_alert

# 파일 전체에 마커를 적용합니다.
pytestmark = pytest.mark.simulation

all_queries = load_queries_from_file()

def test_detection_and_alerting_pipeline(mysql_engine, setup_test_data):
    """
    [E2E 시뮬레이션]
    - GIVEN: 의도적으로 이상 징후가 포함된 데이터가 주입된 환경에서 (setup_test_data 사용)
    - WHEN: 주요 보안 위협 탐지 쿼리를 실행했을 때
    - THEN: 이상 징후가 탐지되면, 'send_email_alert' 함수를 호출하여 알림을 성공적으로 생성해야 한다.
            (이 테스트는 알림 생성 로직이 정상 작동하는지 확인하므로, 항상 통과되어야 함)
    """
    print("\n\n--- [시뮬레이션 시작] 이상 징후 탐지 및 알림 파이프라인 ---")
    
    # 2. 모니터링하고 알림을 받을 쿼리들을 정의합니다.
    queries_to_monitor = {
        "2.1_brute_force": {
            "query": all_queries.get("2.1"),
            "subject": "[보안 경고] Brute-Force 공격 시도가 탐지되었습니다.",
            "body": "다음 IP 주소에서 비정상적인 로그인 시도가 감지되었습니다."
        },
        "2.2_web_scanner": {
            "query": all_queries.get("2.2"),
            "subject": "[보안 경고] 웹 스캐너 활동이 탐지되었습니다.",
            "body": "다음 IP 주소에서 다수의 404 에러가 발생했습니다."
        },
        # 필요에 따라 다른 쿼리(2.4 등)도 추가할 수 있습니다.
    }
    
    alert_triggered = False
    for name, details in queries_to_monitor.items():
        query = details.get("query")
        if not query:
            print(f"  - 쿼리 '{name}'을 찾을 수 없어 건너뜁니다.")
            continue
            
        print(f"\n  - '{name}' 쿼리 실행하여 모니터링 중...")
        df = pd.read_sql_query(text(query), mysql_engine)
        
        # 3. (핵심) 쿼리 결과가 비어있지 않다면(= 탐지 성공), 알림 함수를 호출합니다.
        if not df.empty:
            alert_triggered = True
            print(f"  🚨 이상 징후 탐지! 알림을 생성합니다...")
            send_email_alert(
                subject=details["subject"],
                body=details["body"],
                findings_df=df
            )
        else:
            print(f"  ✅ '{name}' 항목에 대한 특이사항 없음.")

    print("\n--- [시뮬레이션 종료] ---")
    
    # 4. 이 테스트의 목적은 알림이 '생성'되는 것이므로, 실제 탐지 여부와 상관없이 에러만 없으면 통과입니다.
    #    (단, 하나라도 알림이 발생했는지 확인하는 단언(assert)을 추가하여 시뮬레이션 자체의 유효성을 검증할 수 있습니다)
    assert alert_triggered, "시뮬레이션이 실행되었으나, 어떤 이상 징후도 탐지되지 않았습니다. setup_test_data Fixture를 확인하세요."