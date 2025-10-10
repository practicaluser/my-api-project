from sqlalchemy import Column, Integer, String, DateTime, Float, Text, func
from .database import Base


class Post(Base):
    __tablename__ = "posts"  # 데이터베이스에 생성될 테이블 이름

    id = Column(Integer, primary_key=True, index=True)  # 고유 ID, 기본 키
    title = Column(String(100), index=True)  # 제목, 최대 100자
    content = Column(String(500))  # 내용, 최대 500자


class AccessLog(Base):
    """
    성능 및 보안 분석을 위한 통합 액세스 로그 테이블
    """

    __tablename__ = "access_logs"

    # 기본 키
    id = Column(Integer, primary_key=True, index=True)

    # --- 기본 접속 정보 (모델 1의 장점: 데이터 무결성) ---
    ip_address = Column(String(50), nullable=False)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    method = Column(String(10), nullable=False)
    path = Column(String(255), nullable=False)
    status_code = Column(Integer, nullable=False)

    # --- 성능 분석용 컬럼 (모델 1의 장점) ---
    response_time_ms = Column(Float, nullable=False)

    # --- 보안 분석용 컬럼 (모델 2의 장점) ---
    event_type = Column(String(50), nullable=False, default="NORMAL")
    details = Column(Text, nullable=True)  # 상세 정보는 없을 수 있으므로 nullable=True


# --- ⚔️🛡️ 과제 4.1: 보안 이벤트 로깅을 위한 모델 추가 ---
class SecurityEvent(Base):
    """
    보안 이벤트 기록을 위한 테이블
    """

    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(
        String(50), nullable=False, index=True
    )  # LOGIN_FAIL, SUSPICIOUS_QUERY 등
    username = Column(String(100), nullable=True)  # 관련 사용자 이름
    ip_address = Column(String(50), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    description = Column(String(500))  # 이벤트 상세 설명


