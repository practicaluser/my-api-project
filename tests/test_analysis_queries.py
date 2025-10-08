import pytest
import pandas as pd
from sqlalchemy import text
import re


# --- 헬퍼 함수: SQL 파일을 읽고 쿼리별로 분리 ---
def load_queries_from_file(filepath="analysis_queries.sql"):
    """SQL 파일을 읽어 주석을 기반으로 쿼리를 분리하여 딕셔너리로 반환합니다."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # ';' 기준으로 쿼리 블록 분리
    raw_queries = [q.strip() for q in content.split(";") if q.strip()]

    queries = {}
    for query_block in raw_queries:
        # 주석에서 '쿼리 X.X' 패턴 찾기
        match = re.search(r"--\s*쿼리\s*([\d\.]+):", query_block)
        if match:
            query_name = match.group(1)
            queries[query_name] = query_block

    return queries


# 테스트 시작 전에 쿼리를 한 번만 로드
all_queries = load_queries_from_file()


# --- 테스트 함수들 ---


@pytest.mark.parametrize("query_name", ["1.1", "1.2", "1.3", "2.3"])
def test_queries_run_without_errors(mysql_engine, setup_test_data, query_name):
    """
    결과를 특정하기 어려운 일반 분석 쿼리들이 SQL 에러 없이
    정상적으로 실행되는지 확인하는 'Smoke Test'입니다.
    """
    query = all_queries.get(query_name)
    assert query, f"쿼리 {query_name}을 찾을 수 없습니다."

    try:
        # 쿼리를 실행하고 결과를 DataFrame으로 읽어옵니다.
        df = pd.read_sql_query(text(query), mysql_engine)
        # 에러가 발생하지 않고 DataFrame 객체가 생성되면 성공으로 간주합니다.
        assert isinstance(df, pd.DataFrame)
        print(f"\n✅ 쿼리 {query_name} 실행 성공 (결과 {len(df)} 행)")
    except Exception as e:
        pytest.fail(f"쿼리 {query_name} 실행 중 에러 발생: {e}")


def test_brute_force_query_finds_guaranteed_scenario(mysql_engine, setup_test_data):
    """
    쿼리 2.1: Brute-force 공격 탐지 쿼리가 '보장된 시나리오' 데이터를 정확히 찾아내는지 테스트합니다.
    - 모의 데이터는 IP '10.0.0.1'에서 10번의 로그인 실패를 생성합니다.
    """
    query = all_queries.get("2.1")
    assert query, "쿼리 2.1을 찾을 수 없습니다."

    df = pd.read_sql_query(text(query), mysql_engine)

    # 결과가 반드시 1건 이상이어야 함
    assert not df.empty, "Brute-force 공격 시나리오를 탐지하지 못했습니다."

    # 탐지된 IP가 시나리오 데이터와 일치하는지 확인
    detected_ip = df.iloc[0]["ip_address"]
    assert detected_ip == "10.0.0.1"

    # 실패 횟수가 시나리오 데이터와 일치하는지 확인
    failed_attempts = df.iloc[0]["failed_attempts"]
    assert failed_attempts == 10


def test_web_scanner_query_finds_guaranteed_scenario(mysql_engine, setup_test_data):
    """
    쿼리 2.2: 웹 스캐너 탐지 쿼리가 '보장된 시나리오' 데이터를 정확히 찾아내는지 테스트합니다.
    - 모의 데이터는 IP '203.0.113.5'에서 15번의 404 에러를 생성합니다.
    """
    query = all_queries.get("2.2")
    assert query, "쿼리 2.2를 찾을 수 없습니다."

    df = pd.read_sql_query(text(query), mysql_engine)

    assert not df.empty, "웹 스캐너 공격 시나리오를 탐지하지 못했습니다."

    detected_ip = df.iloc[0]["ip_address"]
    assert detected_ip == "203.0.113.5"

    not_found_count = df.iloc[0]["not_found_count"]
    assert not_found_count == 15


def test_traffic_spike_query_finds_guaranteed_scenario(mysql_engine, setup_test_data):
    """
    쿼리 2.4: 트래픽 급증 탐지 쿼리가 '보장된 시나리오' 데이터를 정확히 찾아내는지 테스트합니다.
    - 모의 데이터는 IP '198.51.100.25'에서 어제 30건, 오늘 200건의 요청을 생성합니다.
    - 쿼리 조건: 5배 이상 증가 & 100건 이상 -> (200 > 30*5) 이므로 탐지되어야 함
    """
    query = all_queries.get("2.4")
    assert query, "쿼리 2.4를 찾을 수 없습니다."

    df = pd.read_sql_query(text(query), mysql_engine)

    assert not df.empty, "트래픽 급증 시나리오를 탐지하지 못했습니다."

    detected_ip = df.iloc[0]["ip_address"]
    assert detected_ip == "198.51.100.25"

    # 오늘과 어제의 요청 건수가 시나리오와 일치하는지 확인
    today_requests = df.iloc[0]["total_requests"]
    yesterday_requests = df.iloc[0]["previous_day_requests"]
    assert today_requests == 200
    assert yesterday_requests == 30
