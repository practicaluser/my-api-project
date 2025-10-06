from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

# 다른 파일에서 필요한 클래스와 함수들을 가져옵니다.
from. import models, schemas
from.database import SessionLocal, engine

# 데이터베이스 테이블 생성 (애플리케이션 시작 시)
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# API 요청마다 데이터베이스 세션을 생성하고, 요청이 끝나면 닫는 의존성 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- CRUD 엔드포인트 구현 ---

# Create (생성)
@app.post("/posts", response_model=schemas.Post, status_code=201)
def create_post(post: schemas.PostCreate, db: Session = Depends(get_db)):
    # schemas.PostCreate 모델을 models.Post 모델로 변환
    db_post = models.Post(title=post.title, content=post.content)
    db.add(db_post)  # DB 세션에 추가
    db.commit()     # DB에 커밋 (실제 저장)
    db.refresh(db_post) # 생성된 객체의 정보를 다시 로드 (ID 등)
    return db_post

# Read (전체 조회)
@app.get("/posts", response_model=List[schemas.Post])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = db.query(models.Post).offset(skip).limit(limit).all()
    return posts

# Read (단일 조회)
@app.get("/posts/{post_id}", response_model=schemas.Post)
def read_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post

# Update (수정)
@app.put("/posts/{post_id}", response_model=schemas.Post)
def update_post(post_id: int, post: schemas.PostCreate, db: Session = Depends(get_db)):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db_post.title = post.title
    db_post.content = post.content
    db.commit()
    db.refresh(db_post)
    return db_post

# Delete (삭제)
@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    db.delete(db_post)
    db.commit()
    return