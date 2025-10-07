import logging
import sys

def setup_logger():
    """프로젝트에서 사용할 기본 로거를 설정하고 반환합니다."""
    # 로거 인스턴스 생성
    logger = logging.getLogger("MyApiProjectLogger")
    logger.setLevel(logging.INFO) # INFO 레벨 이상의 로그만 처리

    # 이미 핸들러가 설정되어 있다면 중복 추가 방지
    if logger.hasHandlers():
        return logger

    # 로그 포맷 설정
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s'
    )

    # 콘솔(stdout) 핸들러 설정
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger

# 전역적으로 사용할 로거 인스턴스
logger = setup_logger()