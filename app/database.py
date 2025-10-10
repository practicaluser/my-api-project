from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# mysql+mysqlconnector → mysql+pymysql 로 변경
# SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:1234@127.0.0.1:3306/mydatabase?charset=utf8mb4"
# SQLALCHEMY_DATABASE_URL = (
#     "mysql+pymysql://root:1234@127.0.0.1:3306/mydatabase_test?charset=utf8mb4"
# )
SQLALCHEMY_DATABASE_URL = (
    "mysql+pymysql://root:1234@db:3306/mydatabase_test?charset=utf8mb4"
)

# engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# --- 👇 [수정] create_engine에 옵션 추가 ---
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=50,  # 동시에 유지할 최소 커넥션 수를 50으로 늘립니다.
    max_overflow=20,  # 최소 커넥션을 초과하여 임시로 맺을 수 있는 커넥션 수를 20으로 늘립니다.
    pool_recycle=3600,  # 1시간(3600초)이 지난 커넥션은 자동으로 재연결하여 끊김을 방지합니다.
)
# --- 여기까지 수정 ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    FastAPI의 의존성 주입 시스템에서 사용할 데이터베이스 세션 생성 함수.
    하나의 API 요청 사이클 동안만 유지되는 세션을 생성하고, 요청이 끝나면 자동으로 닫습니다.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()