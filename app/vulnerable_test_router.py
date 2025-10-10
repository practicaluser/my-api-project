# app/vulnerable_test_router.py

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models
from .database import get_db

# main.py의 app 대신 APIRouter 객체를 생성합니다.
router = APIRouter()

# 여기에 SQL Injection에 취약한 엔드포인트를 그대로 옮겨옵니다.
@router.get("/items/search")
def search_items(name: str, request: Request, db: Session = Depends(get_db)):
    # ... (이전 main.py에 있던 취약한 코드 전체) ...
    client_ip = request.client.host

    if any(keyword in name.lower() for keyword in ["'", ";", "--", "or", "and"]):
        security_event = models.SecurityEvent(
            event_type="SQL Injection Attempt",
            source_ip=client_ip,
            payload=name,
            description=f"Suspicious pattern detected in search query for items."
        )
        db.add(security_event)
        db.commit()

    raw_query = f"SELECT * FROM items WHERE name = '{name}'"
    
    try:
        result = db.execute(text(raw_query))
        items = [dict(row._mapping) for row in result.fetchall()]
        if not items:
            return {"message": "No items found."}
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred.")