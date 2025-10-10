import os
import json
import requests
import time
import sqlalchemy
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timezone

# --- 👇 1단계: 모델 임포트를 위한 경로 설정 및 import 추가 ---
import sys

# penetration_tests 디렉터리의 부모 디렉터리(프로젝트 루트)를 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models import (
    SecurityEvent,
)  # app/models.py에서 SecurityEvent 모델을 직접 가져옵니다.

# --- 환경 설정 ---
TARGET_URL = os.getenv("TARGET_URL", "http://127.0.0.1:8088")
DB_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:1234@127.0.0.1:3306/mydatabase_test?charset=utf8mb4",
)
API_ENDPOINT = f"{TARGET_URL}/test-api/items/search"
PAYLOADS_FILE = os.path.join(os.path.dirname(__file__), "payloads.json")
REPORT_FILE = "penetration_test_report.md"

# DB 연결 설정
try:
    engine = sqlalchemy.create_engine(DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print("✅ Database engine created successfully.")
except Exception as e:
    print(f"❌ Failed to create database engine: {e}")
    exit(1)


def wait_for_api(url, timeout=60):
    """API 서버가 응답할 때까지 대기"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # 기본 엔드포인트가 아닌, 애플리케이션의 특정 라우트를 확인하여 준비 상태를 더 정확히 파악
            check_url = f"{TARGET_URL}/posts"
            response = requests.get(check_url, timeout=5)
            if response.status_code == 200:
                print(f"✅ API is up and running at {check_url}")
                return True
        except requests.ConnectionError:
            time.sleep(2)
        except requests.Timeout:
            print(".. API connection timed out, retrying ..")
    print(f"❌ API did not become available within {timeout} seconds.")
    return False


# 🔴 --- Red Team: 공격 페이즈 --- 🔴
def execute_attack_phase():
    """payloads.json을 읽어와 SQL Injection 공격을 수행합니다."""
    print("\n--- 🔴 Starting Attack Phase (Red Team) 🔴 ---")
    attack_results = []

    with open(PAYLOADS_FILE, "r", encoding="utf-8") as f:
        payload_data = json.load(f)

    for scenario in payload_data["scenarios"]:
        name = scenario["name"]
        payload = scenario["payload"]
        technique = scenario.get("technique", "Unknown")  # technique 필드 사용

        print(f"[*] Executing scenario: {name} (Technique: {technique})")

        result = {
            "name": name,
            "payload": payload,
            "success": False,
            "response": "",
            "technique": technique,
        }

        try:
            start_time = time.time()
            # 시간 기반 공격을 위해 timeout을 충분히 길게 설정 (예: 10초)
            response = requests.get(API_ENDPOINT, params={"name": payload}, timeout=10)
            elapsed_time = time.time() - start_time

            result["response"] = response.text

            # --- 수정된 부분: technique에 따른 성공 여부 판단 ---
            success = False

            # 1. 시간 기반(Time-Based) 공격 성공 조건: 응답 시간이 특정 임계값(예: 4초) 이상
            if technique == "Time-Based":
                if elapsed_time > 4.0:
                    success = True
                    print(
                        f"  [+] SUCCESS: Time-based attack detected. Response time: {elapsed_time:.2f}s"
                    )
                else:
                    print(
                        f"  [-] FAILED: No significant time delay detected. Response time: {elapsed_time:.2f}s"
                    )

            # 2. 오류 기반(Error-Based) 공격 성공 조건: 500 에러 또는 응답에 DB 에러 메시지 포함
            elif technique == "Error-Based":
                if response.status_code == 500 or any(
                    err in response.text.lower()
                    for err in ["sql syntax", "error", "warning", "fatal"]
                ):
                    success = True
                    print(
                        f"  [+] SUCCESS: Error-based attack detected with status {response.status_code}."
                    )
                else:
                    print("  [-] FAILED: No database error observed in response.")

            # 3. 유니언 기반(UNION-Based) 공격 성공 조건: 정상 응답(200)이면서, 결과가 1개 초과로 반환 (모든 데이터를 훔쳤다고 가정)
            elif technique == "UNION-Based":
                try:
                    if (
                        response.status_code == 200
                        and len(response.json().get("results", [])) > 1
                    ):
                        success = True
                        print(
                            f"  [+] SUCCESS: UNION-based attack seems successful, returned {len(response.json().get('results',[]))} items."
                        )
                    else:
                        print(
                            "  [-] FAILED: UNION-based attack did not return expected data."
                        )
                except json.JSONDecodeError:
                    print(
                        "  [-] FAILED: Response was not valid JSON, which might indicate an error page."
                    )

            # 4. 기타 (Boolean-Based 등) : 일단 200 응답이면 성공으로 간주, 추가 검증 필요
            else:
                if response.status_code == 200:
                    success = (
                        True  # 일단 성공으로 간주하고, Blue Team에서 로그 등을 확인
                    )
                    print(
                        "  [?] SUCCESS (provisional): Attack sent and received HTTP 200. Manual verification or log check needed."
                    )
                else:
                    print(
                        f"  [-] FAILED: Received unexpected status code {response.status_code}"
                    )

            result["success"] = success

        except requests.RequestException as e:
            result["response"] = str(e)
            # 시간 기반 공격 테스트 중 타임아웃은 '성공'일 수 있음
            if technique == "Time-Based" and "Read timed out" in str(e):
                result["success"] = True
                print(
                    "  [+] SUCCESS: Time-based attack detected (Request timed out as expected)."
                )
            else:
                print(f"  [-] FAILED: Request failed - {e}")

        attack_results.append(result)
        time.sleep(1)

    return attack_results


# 🔵 --- Blue Team: 검증 페이즈 --- 🔵
def execute_verification_phase(attack_results):
    """공격 후 DB 상태를 확인하여 영향도와 탐지 여부를 검증합니다."""
    print("\n--- 🔵 Starting Verification Phase (Blue Team) 🔵 ---")
    verification_results = {"impact_analysis": [], "detection_verification": []}
    db = SessionLocal()

    try:
        # --- 1. 영향도 분석 (Impact Analysis) ---
        # 현재 페이로드 목록에는 DB 내용을 직접 변경하는 'tampering' 시나리오가 없습니다.
        # 따라서 해당 테스트는 '해당 없음'으로 처리합니다.
        print("[*] Performing Impact Analysis...")
        impact_msg = (
            "NOT_APPLICABLE: No data tampering payloads were executed in this test run."
        )
        print(f"  [*] {impact_msg}")
        verification_results["impact_analysis"].append(
            {
                "check": "Data Tampering",
                "status": "NOT_APPLICABLE",
                "details": impact_msg,
            }
        )

        # --- 2. 탐지 능력 검증 (Detection Verification) ---
        print("[*] Performing Detection Verification...")
        try:
            # events_query = sqlalchemy.text("SELECT event_type, description FROM security_events WHERE event_type = 'SQL_INJECTION_ATTEMPT'")
            # events = db.execute(events_query).fetchall()
            events = (
                db.query(SecurityEvent)
                .filter(SecurityEvent.event_type == "SQL_INJECTION_ATTEMPT")
                .all()
            )

            # 성공한 공격 시도 수만큼 로그가 있어야 함
            successful_attacks = sum(1 for r in attack_results if r["success"])

            if len(events) >= successful_attacks and successful_attacks > 0:
                detect_msg = f"SUCCESS: Found {len(events)} 'SQL_INJECTION_ATTEMPT' events. Matched or exceeded the {successful_attacks} successful attacks."
                print(f"  [+] {detect_msg}")
                verification_results["detection_verification"].append(
                    {
                        "check": "Log Existence",
                        "status": "SUCCESS",
                        "details": detect_msg,
                    }
                )
            elif successful_attacks == 0:
                detect_msg = "INFO: No attacks were successful, so no detection logs are expected."
                print(f"  [*] {detect_msg}")
                verification_results["detection_verification"].append(
                    {"check": "Log Existence", "status": "INFO", "details": detect_msg}
                )
            else:
                detect_msg = f"FAILURE: Expected at least {successful_attacks} 'SQL_INJECTION_ATTEMPT' events, but found only {len(events)}."
                print(f"  [-] {detect_msg}")
                verification_results["detection_verification"].append(
                    {
                        "check": "Log Existence",
                        "status": "FAILURE",
                        "details": detect_msg,
                    }
                )
        except Exception as e:
            # security_events 테이블이 없는 경우 등 예외 처리
            detect_msg = f"ERROR: Could not verify detection logs. Reason: {e}"
            print(f"  [!] {detect_msg}")
            verification_results["detection_verification"].append(
                {"check": "Log Existence", "status": "ERROR", "details": detect_msg}
            )

    finally:
        db.close()

    return verification_results


# 📝 --- 보고서 생성 --- 📝
def generate_report(attack_results, verification_results):
    """테스트 결과를 종합하여 Markdown 보고서를 생성합니다."""
    print("\n--- 📝 Generating Report 📝 ---")

    report_content = f"""
# ⚔️🛡️ Automated Penetration Test Report

- **Test Execution Time:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
- **Target URL:** `{TARGET_URL}`

## 🏁 Executive Summary

This report details the results of an automated SQL Injection attack and verification workflow.

- **Attack Scenarios Executed:** {len(attack_results)}
- **Successful Attacks:** {sum(1 for r in attack_results if r['success'])}
- **Attack Detection Verified:** {'✅' if any(r['status'] == 'SUCCESS' for r in verification_results['detection_verification']) else '❌'}

**Overall Assessment:**
"""
    # 최종 결론
    detection_failed = any(
        r["status"] == "FAILURE" for r in verification_results["detection_verification"]
    )
    attack_succeeded = any(r["success"] for r in attack_results)

    if attack_succeeded and detection_failed:
        report_content += "**🔴 CRITICAL FAILURE: The system was successfully attacked, but the detection mechanisms FAILED to log the event. Immediate investigation is required.**\n"
    elif attack_succeeded and not detection_failed:
        report_content += "**🟠 WARNING: The system is vulnerable and was compromised, but the detection systems correctly logged the attack.**\n"
    elif not attack_succeeded:
        report_content += "**✅ SUCCESS: The application successfully resisted all attack payloads.**\n"
    else:  # not attack_succeeded and detection_failed (공격은 실패했는데 로그 시스템도 실패)
        report_content += "**⚪️ INFO: The attack was not successful, but detection logs are incomplete. The logging system may have issues.**\n"

    report_content += "\n## 🔴 Red Team: Attack Phase Results\n\n| Status | Technique | Scenario | Payload |\n| :----: | --------- | -------- | ------- |\n"
    for res in attack_results:
        status_icon = "✅" if res["success"] else "❌"
        report_content += f"| {status_icon} | {res['technique']} | {res['name']} | `{res['payload']}` |\n"

    report_content += "\n## 🔵 Blue Team: Verification Phase Results\n\n"
    report_content += "### Impact Analysis (Blast Radius)\n"
    for res in verification_results["impact_analysis"]:
        report_content += f"- **Check:** {res['check']} | **Status:** {res['status']} | **Details:** {res['details']}\n"

    report_content += "\n### Detection Verification\n"
    for res in verification_results["detection_verification"]:
        report_content += f"- **Check:** {res['check']} | **Status:** {res['status']} | **Details:** {res['details']}\n"

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(report_content)
    print(f"✅ Report generated: {REPORT_FILE}")

    # CI/CD 실패 조건: 공격이 성공했거나, 탐지 시스템이 실패했을 때
    return attack_succeeded or detection_failed


def main():
    """메인 실행 함수"""
    if not wait_for_api(f"{TARGET_URL}/posts/"):
        exit(1)

    attack_results = execute_attack_phase()
    verification_results = execute_verification_phase(attack_results)
    is_failure_condition_met = generate_report(attack_results, verification_results)

    if is_failure_condition_met:
        print("\n❌ Test workflow completed with CRITICAL FINDINGS.")
        exit(1)  # CI/CD 파이프라인을 실패 처리
    else:
        print("\n✅ Test workflow completed successfully. No vulnerabilities detected.")
        exit(0)


if __name__ == "__main__":
    main()
