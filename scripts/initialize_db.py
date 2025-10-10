# scripts/initialize_db.py (수정 후)

import sys
import os
from sqlalchemy.orm import Session

# 프로젝트 루트 경로 설정 (이 부분은 그대로 둡니다)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- 👇 [수정] app.database에서 engine과 Base를 직접 가져옵니다 ---
from app.database import engine, Base
from app.models import * # models.py에 정의된 모든 모델을 가져옵니다.
# -------------------------------------------------------------

from scripts.create_mock_data import run_data_creation


def initialize_database():
    """
    데이터베이스에 연결하여 모든 테이블을 (재)생성하고
    모의 데이터를 주입하는 초기화 작업을 수행합니다.
    """
    print("▶️ 데이터베이스 초기화를 시작합니다...")
    try:
        # [수정] 더 이상 직접 engine을 만들지 않습니다.
        print(" 	- 기존 테이블을 삭제합니다 (있을 경우)...")
        # [수정] AnalysisBase 대신 app.database에서 가져온 Base를 사용합니다.
        Base.metadata.drop_all(bind=engine)
        print(" 	- 새로운 테이블을 생성합니다...")
        Base.metadata.create_all(bind=engine)
        print(" 	- 모의(mock) 데이터를 주입합니다...")
        
        # [수정] Session(engine) 대신 SessionLocal을 사용하면 더 일관성 있습니다.
        # 하지만 기존 방식도 동작은 하므로 그대로 두거나 아래처럼 바꿔도 됩니다.
        with Session(engine) as db: 
            run_data_creation(db)
            db.commit()
            
        print("\n✅ 데이터베이스 초기화가 성공적으로 완료되었습니다!")
    except Exception as e:
        print(f"\n❌ 데이터베이스 초기화 중 오류가 발생했습니다: {e}")
        print(" 	- Docker 컨테이너가 실행 중인지 확인해주세요.")
        print(" 	- DATABASE_URL이 올바른지 확인해주세요. (app/database.py)")

if __name__ == "__main__":
    initialize_database()