from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# mysql+mysqlconnector → mysql+pymysql 로 변경
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:1234@localhost:3306/mydatabase?charset=utf8mb4"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
