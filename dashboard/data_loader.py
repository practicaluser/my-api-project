# dashboard/data_loader.py

import streamlit as st
import requests
import json
import zipfile
import io
import pandas as pd
from sqlalchemy.exc import OperationalError
import os

# -----------------------------------------------------------------------------
# 헬퍼 함수: secrets.toml 파일 확인 및 상태 메시지를 화면에 영구적으로 표시
# -----------------------------------------------------------------------------
def _check_and_display_secrets_status():
    """
    st.session_state를 사용해 앱 세션에서 단 한번만 secrets.toml 파일의
    존재 여부를 확인하고, 그 결과를 st.success() 또는 st.error()로 화면에 고정 표시합니다.
    """
    # session_state에 'secrets_status_checked' 키가 없다면, 즉 처음 실행될 때
    if 'secrets_status_checked' not in st.session_state:
        if os.path.exists(".streamlit/secrets.toml"):
            st.success("✅ .streamlit/secrets.toml 파일이 존재하며, 성공적으로 로드되었습니다.")
            # 파일이 존재한다는 상태를 세션에 저장
            st.session_state['secrets_file_exists'] = True
        else:
            st.error("❌ .streamlit/secrets.toml 파일을 찾을 수 없습니다. 프로젝트 루트에 파일을 생성해주세요.")
            # 파일이 없다는 상태를 세션에 저장
            st.session_state['secrets_file_exists'] = False
        
        # 확인 작업이 완료되었음을 세션에 기록하여 중복 실행 방지
        st.session_state['secrets_status_checked'] = True

    # 세션에 저장된 파일 존재 여부 결과를 반환
    return st.session_state.get('secrets_file_exists', False)

# -----------------------------------------------------------------------------
# 데이터 소스 1: 운영 DB (MySQL)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def load_db_data():
    """운영 DB에 연결하여 분석 쿼리를 실행하고 결과를 DataFrame으로 반환합니다."""
    
    # 헬퍼 함수를 호출하여 파일 상태를 확인하고 화면에 표시
    if not _check_and_display_secrets_status():
        return None

    try:
        conn = st.connection("mysql_db", type="sql")
        with open('../analysis_queries.sql', 'r', encoding='utf-8') as f:
            queries = [q.strip() for q in f.read().split(";") if q.strip()]

        results = {}
        query_names = ["time_series_requests", "top_10_endpoints", "slowest_10_endpoints"]

        for i, query in enumerate(queries):
            if i < len(query_names):
                results[query_names[i]] = conn.query(query, ttl=600)

        return results
    
    except OperationalError as e:
        st.error(f"데이터베이스 연결 오류가 발생했습니다. 'secrets.toml'의 DB 이름과 `docker-compose.yml`의 `MYSQL_DATABASE` 값이 일치하는지 확인해주세요. 원본 오류: {e}")
        return None
    except Exception as e:
        st.error(f"데이터베이스 처리 중 예측하지 못한 오류 발생: {e}")
        return None

# -----------------------------------------------------------------------------
# 데이터 소스 2: QA 테스트 결과 (GitHub Artifacts)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def load_latest_qa_report():
    """GitHub API를 통해 가장 최근의 QA 테스트 리포트(JSON)를 가져옵니다."""
    
    # 헬퍼 함수를 호출하여 파일 상태를 확인하고 화면에 표시
    if not _check_and_display_secrets_status():
        return None, None, "`.streamlit/secrets.toml` 파일 없음"

    try:
        if "GITHUB_TOKEN" not in st.secrets or "GITHUB_REPO" not in st.secrets:
            st.error("secrets.toml 파일에 GITHUB_TOKEN 또는 GITHUB_REPO 키가 없습니다. 파일을 다시 확인해주세요.")
            return None, None, "필수 secret 키 누락"

        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]

        headers = {"Authorization": f"token {token}"}
        runs_url = f"https://api.github.com/repos/{repo}/actions/workflows/python-ci.yml/runs?branch=main&status=success&per_page=1"
        response = requests.get(runs_url, headers=headers)
        response.raise_for_status()
        
        workflow_runs = response.json().get("workflow_runs", [])
        if not workflow_runs:
            return None, None, "조건에 맞는 성공한 워크플로우 실행 기록을 찾을 수 없습니다."

        latest_run = workflow_runs[0]
        latest_run_id = latest_run["id"]
        commit_message = latest_run.get("head_commit", {}).get("message", "커밋 메시지 없음")

        artifacts_url = f"https://api.github.com/repos/{repo}/actions/runs/{latest_run_id}/artifacts"
        response = requests.get(artifacts_url, headers=headers)
        response.raise_for_status()

        artifacts = response.json().get("artifacts", [])
        artifact_info = next((item for item in artifacts if item["name"] == "qa-test-report"), None)
        
        if not artifact_info:
            return None, None, "워크플로우 실행에서 'qa-test-report' 아티팩트를 찾을 수 없습니다."

        download_url = artifact_info["archive_download_url"]
        response = requests.get(download_url, headers=headers)
        response.raise_for_status()

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            with z.open("pytest-report.json") as f:
                report_data = json.load(f)

        return report_data, commit_message, None

    except requests.exceptions.HTTPError as e:
        error_message = f"GitHub API 요청 실패 (HTTP {e.response.status_code}): {e}"
        st.error(error_message)
        return None, None, error_message
    except Exception as e:
        error_message = f"GitHub 아티팩트 처리 중 예측하지 못한 오류 발생: {e}"
        st.error(error_message)
        return None, None, error_message