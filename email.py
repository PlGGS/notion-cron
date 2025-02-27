import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

sender_email = os.getenv("GMAIL_SENDER_EMAIL")
receiver_email = os.getenv("GMAIL_RECEIVER_EMAIL")
app_password = os.getenv("GMAIL_APP_PASSWORD")
smtp_ssl = os.getenv("SMTP_SSL")

subject = "LETS GET IT"
body = "Good morning! Today's food tracker page: https://www.notion.so/blakeboris/1a7ceda5530a80f0b09ec4f18c47f08e"

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message.attach(MIMEText(body, "plain"))

try:
    with smtplib.SMTP_SSL(smtp_ssl, 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
