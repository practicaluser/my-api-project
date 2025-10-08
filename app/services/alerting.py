import os
import smtplib
from dotenv import load_dotenv
import pandas as pd

# 1. 방금 만든 로거를 가져옵니다.
from app.logger_config import logger

load_dotenv()


def send_email_alert(subject: str, body: str, findings_df: pd.DataFrame):
    SENDER = os.getenv("SENDER_EMAIL")
    RECEIVER = os.getenv("RECEIVER_EMAIL")
    PASSWORD = os.getenv("EMAIL_APP_PASSWORD")

    if not all([SENDER, RECEIVER, PASSWORD]):
        # 2. print 대신 logger.warning 사용
        logger.warning(
            "이메일 정보(SENDER, RECEIVER, PASSWORD)가 .env 파일에 설정되지 않았습니다. 시뮬레이션 모드로 작동합니다."
        )
        return

    try:
        # 3. 이메일 발송 시도 전/후에 INFO 레벨 로그 기록
        logger.info(f"이메일 발송 시도: (발신: {SENDER}, 수신: {RECEIVER})")
        message = (
            f"Subject: {subject}\n\n{body}\n\nDetected Data:\n{findings_df.to_string()}"
        )

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            logger.info("smtp.gmail.com:465 서버에 연결 성공")
            server.login(SENDER, PASSWORD)
            logger.info(f"'{SENDER}' 계정으로 로그인 성공")
            server.sendmail(SENDER, RECEIVER, message.encode("utf-8"))

        logger.info("✅ 이메일 알림을 성공적으로 발송했습니다.")

    except Exception:
        # 4. (핵심) 에러 발생 시, 에러의 전체 추적 내용을 로그로 남깁니다.
        logger.error("❌ 이메일 발송 중 에러 발생", exc_info=True)
