import pytest
import pandas as pd
from sqlalchemy import text

# test_analysis_queries.py 에 있던 헬퍼 함수를 가져오거나 공통 유틸리티로 분리할 수 있습니다.
from tests.test_analysis_queries import load_queries_from_file

# 테스트 시작 전에 전체 쿼리를 미리 로드합니다.
all_queries = load_queries_from_file()

# --- ⭐️ 모니터링 테스트의 핵심 원칙 ---
# "정상적인 상황에서는, 이상 징후 쿼리가 아무것도 찾아내지 못해야 한다."
# 따라서 모든 테스트는 쿼리 결과가 비어있음(empty)을 검증합니다.

def test_monitor_for_brute_force_attacks(mysql_engine, setup_normal_operation_data):
    """[모니터링] Brute-force 공격 시도가 없는지 감시합니다."""
    query = all_queries.get("2.1")
    assert query, "쿼리 2.1을 찾을 수 없습니다."
    
    df = pd.read_sql_query(text(query), mysql_engine)
    
    # 쿼리 결과가 비어있지 않다면(= 공격이 탐지되었다면), 테스트를 실패시키고 탐지 내용을 출력합니다.
    assert df.empty, f"🚨 [보안 경고] Brute-Force 공격 시도가 탐지되었습니다!\n{df.to_string()}"

def test_monitor_for_web_scanners(mysql_engine, setup_normal_operation_data):
    """[모니터링] 웹 스캐너 활동이 없는지 감시합니다."""
    query = all_queries.get("2.2")
    assert query, "쿼리 2.2를 찾을 수 없습니다."
    
    df = pd.read_sql_query(text(query), mysql_engine)
    
    assert df.empty, f"🚨 [보안 경고] 웹 스캐너 활동이 탐지되었습니다!\n{df.to_string()}"

def test_monitor_for_sqli_attempts(mysql_engine, setup_normal_operation_data):
    """[모니터링] SQL Injection 시도 기록이 없는지 감시합니다."""
    query = all_queries.get("2.3")
    assert query, "쿼리 2.3을 찾을 수 없습니다."
    
    df = pd.read_sql_query(text(query), mysql_engine)
    
    assert df.empty, f"🔥 [보안 경고] SQL Injection 시도 기록이 발견되었습니다! 즉시 조치 필요!\n{df.to_string()}"

def test_monitor_for_traffic_spikes(mysql_engine, setup_normal_operation_data):
    """[모니터링] 비정상적인 트래픽 급증이 없는지 감시합니다."""
    query = all_queries.get("2.4")
    assert query, "쿼리 2.4를 찾을 수 없습니다."
    
    df = pd.read_sql_query(text(query), mysql_engine)
    
    assert df.empty, f"⚠️ [운영 경고] 비정상적인 트래픽 급증이 탐지되었습니다!\n{df.to_string()}"