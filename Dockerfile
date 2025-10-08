# --- Stage 1: Builder ---
# 의존성을 설치하고 빌드 아티팩트를 생성하는 단계
FROM python:3.11 AS builder

# 컨테이너 내 작업 디렉토리 설정
WORKDIR /usr/src/app

# 시스템 패키지 매니저 업데이트 및 빌드에 필요한 도구 설치
# (예: C 확장 모듈을 사용하는 라이브러리를 위해)
# RUN apt-get update && apt-get install -y --no-install-recommends gcc

# 파이썬 가상 환경 생성
RUN python -m venv /opt/venv
# 가상 환경을 활성화하도록 PATH 환경 변수 설정
ENV PATH="/opt/venv/bin:$PATH"

# requirements.txt 파일을 복사하고 의존성 설치
# 이 단계를 코드 복사보다 먼저 수행하여 레이어 캐싱을 활용
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# --- Stage 2: Final Image ---
# 실제 애플리케이션을 실행하는 경량화된 최종 단계
FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# Builder 단계에서 생성된 가상 환경을 그대로 복사
COPY --from=builder /opt/venv /opt/venv

# 애플리케이션 소스 코드 복사 ('app' 폴더를 컨테이너의 '/app/app' 폴더로)
COPY ./app /app/app

# 가상 환경의 경로를 PATH에 추가
ENV PATH="/opt/venv/bin:$PATH"

# 컨테이너가 8000번 포트를 외부에 노출하도록 설정
EXPOSE 8000

# 컨테이너가 시작될 때 실행할 기본 명령어
# Gunicorn을 사용하여 4개의 워커 프로세스로 애플리케이션을 실행
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "app.main:app", "--bind", "0.0.0.0:8000"]
