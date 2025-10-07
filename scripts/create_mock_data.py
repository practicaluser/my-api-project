import random
import datetime
from faker import Faker
from sqlalchemy.orm import Session
# ❗️ app.database 에서 직접 engine, SessionLocal을 가져오지 않습니다.
from app.models import Base, AccessLog, SecurityEvent, Post

fake = Faker()

PATHS = ["/posts", "/posts/1", "/posts/15", "/users/profile", "/users/login", "/admin/dashboard", "/search?q=news"]
METHODS = ["GET", "POST", "PUT", "DELETE"]

# --- '실무' 함수 1: 이름 앞에 _를 붙여 내부용임을 표시 (권장) ---
def _create_guaranteed_scenarios(db: Session): # ✅ db: Session 인자 받기
    """각 분석 쿼리가 반드시 결과를 찾을 수 있도록 보장된 시나리오 데이터를 생성합니다."""
    print("  - 보장된 시나리오 데이터 생성 중...")
    logs_to_add = []
    events_to_add = []
    now = datetime.datetime.now(datetime.timezone.utc)

    # (이하 모든 데이터 생성 로직은 사용자님 코드와 100% 동일)
    brute_force_ip = "10.0.0.1"
    targeted_username = "admin"
    for i in range(10):
        log_time = now - datetime.timedelta(minutes=i*2)
        log = AccessLog(ip_address=brute_force_ip, timestamp=log_time, method="POST", path="/users/login", status_code=401, response_time_ms=150.0, event_type='FAILED_LOGIN', details="Guaranteed brute-force scenario.")
        event = SecurityEvent(event_type="LOGIN_FAIL", username=targeted_username, ip_address=brute_force_ip, timestamp=log_time, description=log.details)
        logs_to_add.append(log)
        events_to_add.append(event)

    scanner_ip = "203.0.113.5"
    for i in range(15):
        log_time = now - datetime.timedelta(seconds=i*10)
        path = f"/admin/{random.choice(['.git', 'config.php', 'backup.zip'])}"
        log = AccessLog(ip_address=scanner_ip, timestamp=log_time, method="GET", path=path, status_code=404, response_time_ms=30.0, event_type='SCANNING_ATTEMPT', details="Guaranteed scanner scenario.")
        logs_to_add.append(log)
    
    spike_ip = "198.51.100.25"
    today_noon = now.replace(hour=12, minute=0, second=0, microsecond=0)
    yesterday_noon = today_noon - datetime.timedelta(days=1)
    for _ in range(30):
        logs_to_add.append(AccessLog(ip_address=spike_ip, timestamp=yesterday_noon, method="GET", path="/posts", status_code=200, response_time_ms=50.0, event_type='NORMAL'))
    for _ in range(200):
        logs_to_add.append(AccessLog(ip_address=spike_ip, timestamp=today_noon, method="GET", path="/posts", status_code=200, response_time_ms=55.0, event_type='NORMAL'))

    db.add_all(logs_to_add)
    db.add_all(events_to_add)
    # ❗️ db.commit() 은 여기서 하지 않습니다.


# --- '실무' 함수 2 ---
def _create_mock_data(db: Session, num_logs: int = 1000, anomalies: bool = True): # ✅ db: Session 인자 받기
    """시나리오 기반의 현실적인 모의 로그 데이터를 생성하고 DB에 저장합니다."""
    print(f"  - {num_logs}개의 배경 노이즈 데이터 생성 중...")
    # (이하 모든 데이터 생성 로직은 사용자님 코드와 100% 동일)
    sqli_attempt_ip = "172.16.0.100"
    logs_to_add = []
    events_to_add = []
    for _ in range(num_logs):
        log_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=random.randint(1, 60 * 24 * 2))

        # --- 🔽 이 부분이 핵심 수정 사항 🔽 ---
        if anomalies:
            # anomalies가 True일 때만 이상 징후 시나리오를 포함
            scenario = random.choices(["normal", "sqli_attempt", "permission_denied"], weights=[95, 3, 2], k=1)[0]
        else:
            # anomalies가 False이면 무조건 'normal' 시나리오만 생성
            scenario = "normal"


        ip_addr = fake.ipv4()
        username = fake.user_name()
        log = AccessLog(timestamp=log_time, response_time_ms=abs(random.gauss(80, 50)) + 10)
        if scenario == "normal":
            log.ip_address = ip_addr; log.path = random.choice(PATHS); log.method = random.choice(METHODS); log.status_code = random.choices([200, 201, 302, 404, 500], weights=[85, 5, 2, 5, 3], k=1)[0]; log.event_type = 'NORMAL'
        elif scenario == "sqli_attempt":
            log.ip_address = sqli_attempt_ip; log.path = "/search?q=' OR 1=1; --"; log.method = "GET"; log.status_code = 400; log.event_type = 'SQL_INJECTION_ATTEMPT'; log.details = "Random SQL injection attempt."; events_to_add.append(SecurityEvent(event_type="SUSPICIOUS_QUERY", username=username, ip_address=sqli_attempt_ip, timestamp=log_time, description=log.details))
        elif scenario == "permission_denied":
            log.ip_address = ip_addr; log.path = "/admin/dashboard"; log.method = "GET"; log.status_code = 403; log.event_type = 'PERMISSION_DENIED'; log.details = f"User '{username}' tried to access admin dashboard."; events_to_add.append(SecurityEvent(event_type="PERMISSION_DENIED", username=username, ip_address=ip_addr, timestamp=log_time, description=log.details))
        logs_to_add.append(log)
    db.add_all(logs_to_add)
    db.add_all(events_to_add)
    # ❗️ db.commit() 은 여기서 하지 않습니다.


# --- ⭐️ '사장님'이 호출할 공식적인 단일 창구 (Public Interface) ---
def run_data_creation(db: Session, num_logs: int = 5000):
    """모의 데이터 생성을 위한 모든 작업을 실행하는 메인 함수."""
    print("\n[데이터 생성 모듈 시작]")
    # ❗️ if __name__ == "__main__": 블록의 로직을 여기로 가져옵니다.
    print("  - 기존 로그 데이터 삭제 중...")
    db.query(AccessLog).delete()
    db.query(SecurityEvent).delete()
    
    # 내부 실무 함수들을 순서대로 호출
    _create_mock_data(db, num_logs=num_logs, anomalies=True) 
    _create_guaranteed_scenarios(db)
    
    print("[데이터 생성 모듈 완료]")
    # ❗️ db.close() 도 여기서 하지 않습니다. (사장님이 처리)

# --- 👇 [신규] 모니터링 테스트를 위한 Public Interface ---
def run_normal_data_creation(db: Session, num_logs: int = 5000):
    """(모니터링용) 이상 징후가 없는 '정상 상태'의 배경 데이터만 생성합니다."""
    print("\n[데이터 생성 모듈 시작 - 정상 상태 데이터]")
    db.query(AccessLog).delete()
    db.query(SecurityEvent).delete()

    # '보장된 시나리오' 생성 함수를 호출하지 않는 것이 핵심입니다.
    _create_mock_data(db, num_logs=num_logs, anomalies=False)

    print("[데이터 생성 모듈 완료 - 정상 상태 데이터]")