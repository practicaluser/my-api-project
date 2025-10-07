import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session  # ✅ Session import
from sqlalchemy.pool import StaticPool

from app.main import app, get_db
# API 모델과 분석용 모델의 Base가 다를 수 있으므로 별칭(alias)을 사용해 구분
from app.database import Base as ApiBase 
from app.models import Base as AnalysisBase # 분석용 모델의 Base

# --- API 테스트용 Fixture (이 부분은 수정 없음) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    ApiBase.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        ApiBase.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as client:
        yield client

# --- 👇 데이터 분석 테스트용 Fixture (이 부분을 완성) ---
@pytest.fixture(scope="session")
def mysql_engine():
    """테스트용 MySQL DB 엔진을 생성합니다."""
    DATABASE_URL = "mysql+pymysql://root:1234@localhost:3306/mydatabase_test?charset=utf8mb4"
    engine = create_engine(DATABASE_URL)
    yield engine
    engine.dispose()

@pytest.fixture(scope="session")
def setup_test_data(mysql_engine):
    """
    MySQL 테스트 DB에 연결하고, 테이블을 재생성한 후
    scripts/create_mock_data.py를 호출하여 모의 데이터를 생성합니다.
    """
    # ✅ 1. 'scripts' 폴더에서 데이터 생성 함수를 불러옵니다.
    from scripts.create_mock_data import run_data_creation
    
    print("\n[Fixture 준비] MySQL 테스트 데이터를 설정합니다...")
    AnalysisBase.metadata.drop_all(bind=mysql_engine)
    AnalysisBase.metadata.create_all(bind=mysql_engine)
    
    # ✅ 2. DB와 통신할 세션을 생성하고, 에러가 발생해도 세션을 확실히 닫도록 try...finally 사용
    db = Session(mysql_engine)
    try:
        # ✅ 3. 생성한 세션을 인자로 넘겨주어 데이터 생성을 실행합니다.
        run_data_creation(db)
        
        # ✅ 4. 모든 데이터가 추가되었으면 DB에 최종 저장(commit)합니다.
        db.commit()
    except Exception as e:
        print(f"데이터 생성 중 에러 발생: {e}")
        db.rollback() # 에러 발생 시 작업을 모두 되돌립니다.
    finally:
        # ✅ 5. 작업이 성공하든 실패하든 항상 세션을 닫아줍니다.
        db.close()
        
    print("[Fixture 준비] 데이터 설정 완료.")
    yield
    print("\n[Fixture 정리] 테스트 데이터를 삭제합니다...")
    AnalysisBase.metadata.drop_all(bind=mysql_engine)

# --- 👇 [신규] 데이터 모니터링 테스트용 Fixture ---
@pytest.fixture(scope="session")
def setup_normal_operation_data(mysql_engine):
    """
    MySQL 테스트 DB에 '정상 상태'의 데이터만 생성합니다.
    이 Fixture는 이상 징후가 없어야 통과하는 모니터링 테스트에서 사용됩니다.
    """
    # ❗️ '정상 상태' 데이터 생성 함수를 불러옵니다.
    from scripts.create_mock_data import run_normal_data_creation
    
    print("\n[Fixture 준비] MySQL '정상 상태' 데이터를 설정합니다...")
    AnalysisBase.metadata.drop_all(bind=mysql_engine)
    AnalysisBase.metadata.create_all(bind=mysql_engine)
    
    db = Session(mysql_engine)
    try:
        # '정상 상태' 데이터 생성 함수 호출
        run_normal_data_creation(db)
        db.commit()
    except Exception as e:
        print(f"정상 상태 데이터 생성 중 에러 발생: {e}")
        db.rollback()
    finally:
        db.close()
        
    print("[Fixture 준비] '정상 상태' 데이터 설정 완료.")
    yield
    print("\n[Fixture 정리] 테스트 데이터를 삭제합니다...")
    AnalysisBase.metadata.drop_all(bind=mysql_engine)