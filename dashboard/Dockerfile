# 1. 베이스 이미지 선택
FROM python:3.11-slim

# 2. 작업 디렉토리 설정
WORKDIR /app

# 3. requirements.txt 복사 및 의존성 설치
# 먼저 복사하여 레이어 캐싱을 활용합니다.
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. 나머지 대시보드 애플리케이션 파일 복사
COPY . .

# 5. Streamlit이 사용할 포트 노출
EXPOSE 8501

# 6. 애플리케이션 상태 확인을 위한 헬스체크
HEALTHCHECK CMD streamlit hello --server.port=8501

# 7. 컨테이너 실행 시 실행될 명령어
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]