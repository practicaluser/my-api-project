import os
import smtplib # 실제 이메일 발송을 위한 라이브러리
from dotenv import load_dotenv
import pandas as pd

load_dotenv() # .env 파일에서 환경 변수를 로드

def send_email_alert(subject: str, body: str, findings_df: pd.DataFrame):
    SENDER = os.getenv("SENDER_EMAIL")
    RECEIVER = os.getenv("RECEIVER_EMAIL")
    PASSWORD = os.getenv("EMAIL_PASSWORD")

    # 환경 변수가 설정되지 않았으면 시뮬레이션 모드로 작동
    if not all([SENDER, RECEIVER, PASSWORD]):
        print("\n[알림 시뮬레이션] 이메일 정보가 설정되지 않았습니다.")
        # ... (기존의 print문으로 된 시뮬레이션 로직) ...
        return

    # --- 👇 실제 이메일 발송 로직 ---
    try:
        message = f"Subject: {subject}\n\n{body}\n\nDetected Data:\n{findings_df.to_string()}"
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SENDER, PASSWORD)
            server.sendmail(SENDER, RECEIVER, message.encode('utf-8'))
        print("✅ 실제 이메일 알림을 성공적으로 발송했습니다.")
    except Exception as e:
        print(f"❌ 이메일 발송 실패: {e}")