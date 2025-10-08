# init_db.py

from app.database import engine, Base


def init_database():
    """
    SQLAlchemy 모델을 기반으로 모든 테이블을 생성합니다.
    """
    print("Initializing database and creating tables...")
    # Base.metadata.create_all()은 이미 존재하는 테이블은 건드리지 않습니다.
    Base.metadata.create_all(bind=engine)
    print("Database initialization complete.")


if __name__ == "__main__":
    init_database()
