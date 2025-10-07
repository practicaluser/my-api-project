from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# mysql+mysqlconnector → mysql+pymysql 로 변경
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:1234@localhost:3306/mydatabase?charset=utf8mb4"

# engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# --- 👇 [수정] create_engine에 옵션 추가 ---
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=50,         # 동시에 유지할 최소 커넥션 수를 50으로 늘립니다.
    max_overflow=20,      # 최소 커넥션을 초과하여 임시로 맺을 수 있는 커넥션 수를 20으로 늘립니다.
    pool_recycle=3600     # 1시간(3600초)이 지난 커넥션은 자동으로 재연결하여 끊김을 방지합니다.
)
# --- 여기까지 수정 ---

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
