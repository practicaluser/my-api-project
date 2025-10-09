# dashboard/data_loader.py

import streamlit as st
import pandas as pd
import requests
import json
import zipfile
import io
from sqlalchemy import create_engine, text

# -----------------------------------------------------------------------------
# 데이터 소스 1: 운영 DB (MySQL)
# -----------------------------------------------------------------------------


# st.cache_data: DB 쿼리 결과를 캐싱하여 반복적인 호출을 방지합니다.
# ttl=600: 캐시는 10분(600초) 동안 유효합니다.
@st.cache_data(ttl=600)
def load_db_data():
    """운영 DB에 연결하여 분석 쿼리를 실행하고 결과를 DataFrame으로 반환합니다."""
    try:
        # Streamlit의 Secrets Management를 사용하여 DB 연결 정보를 안전하게 관리합니다.
        # 로컬 테스트 시: .streamlit/secrets.toml 파일에 아래 내용을 추가
        # [connections.mysql_db]
        # url = "mysql+pymysql://user:password@host:port/database"
        conn = st.connection("mysql_db", type="sql")

        # 프로젝트 루트의 analysis_queries.sql 파일 내용을 읽어옵니다.
        # 실제 배포 환경에 맞게 경로를 조정해야 할 수 있습니다.
        with open("../analysis_queries.sql", "r") as f:
            queries = f.read().split(";")

        # 각 쿼리를 실행하고 결과를 딕셔너리에 저장합니다.
        results = {}
        # 예시: 쿼리 이름과 실제 쿼리를 매핑 (analysis_queries.sql 내용에 맞게 수정)
        query_map = {
            "time_series_requests": queries[0],
            "top_10_endpoints": queries[1],
            "slowest_10_endpoints": queries[2],
        }

        for name, query in query_map.items():
            if query.strip():
                results[name] = conn.query(query, ttl=600)  # 개별 쿼리 결과도 캐싱

        return results

    except Exception as e:
        st.error(f"데이터베이스 연결 또는 쿼리 실행 중 오류 발생: {e}")
        return None


# -----------------------------------------------------------------------------
# 데이터 소스 2: QA 테스트 결과 (GitHub Artifacts)
# -----------------------------------------------------------------------------


@st.cache_data(ttl=600)
def load_latest_qa_report():
    """GitHub API를 통해 가장 최근의 QA 테스트 리포트(JSON)를 가져옵니다."""
    try:
        # GitHub 토큰과 레포지토리 정보는 Streamlit secrets에서 가져옵니다.
        # .streamlit/secrets.toml
        # GITHUB_TOKEN = "your_personal_access_token"
        # GITHUB_REPO = "owner/repo_name"
        token = st.secrets["GITHUB_TOKEN"]
        repo = st.secrets["GITHUB_REPO"]

        headers = {"Authorization": f"token {token}"}

        # 1. 가장 최근에 성공한 워크플로우 실행(run) ID 찾기
        runs_url = f"https://api.github.com/repos/{repo}/actions/workflows/python-ci.yml/runs?branch=main&status=success&per_page=1"
        response = requests.get(runs_url, headers=headers)
        response.raise_for_status()
        latest_run_id = response.json()["workflow_runs"][0]["id"]
        commit_message = response.json()["workflow_runs"][0]["head_commit"]["message"]

        # 2. 해당 실행(run)의 아티팩트 정보 가져오기
        artifacts_url = f"https://api.github.com/repos/{repo}/actions/runs/{latest_run_id}/artifacts"
        response = requests.get(artifacts_url, headers=headers)
        response.raise_for_status()

        # 'qa-test-report' 아티팩트 찾기
        artifact_info = next(
            (
                item
                for item in response.json()["artifacts"]
                if item["name"] == "qa-test-report"
            ),
            None,
        )
        if not artifact_info:
            return None, None, "QA 리포트 아티팩트를 찾을 수 없습니다."

        # 3. 아티팩트 다운로드 (zip 파일)
        download_url = artifact_info["archive_download_url"]
        response = requests.get(download_url, headers=headers)
        response.raise_for_status()

        # 4. 메모리 내에서 zip 파일 압축 해제 및 JSON 파일 읽기
        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            with z.open("pytest-report.json") as f:
                report_data = json.load(f)

        return report_data, commit_message, None

    except Exception as e:
        return None, None, f"GitHub 아티팩트 로딩 중 오류 발생: {e}"
