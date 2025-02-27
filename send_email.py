import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests
from dotenv import load_dotenv

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_WORKSPACE = os.getenv("NOTION_WORKSPACE")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Default page_id value
page_id = None

# Default response value
response = None
try:
    response = requests.post("https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query", headers=headers)
except Exception as e:
    print(f"Failed to query Notion: {e}")

if response.status_code == 200:
    database_data = response.json()
    results = database_data["results"]
    
    if results:
        recent_page = results[0] # Get the most recent page (first in the sorted list)
        page_id = recent_page["id"].replace('-', '')
else:
    print(f"Bad response from Notion: {response.json()}")
    exit(1)

sender_email = os.getenv("GMAIL_SENDER_EMAIL")
receiver_email = os.getenv("GMAIL_RECEIVER_EMAIL")
app_password = os.getenv("GMAIL_APP_PASSWORD")
smtp_ssl = os.getenv("SMTP_SSL")

subject = "LETS GET IT"
if page_url is not Nonez:
    body = f"Good morning! Here's today's food tracker page: https://www.notion.so/{page_id}"
else:
    body = f"Good morning! Couldn't get today's page ID, so here's the general food tracker page: https://www.notion.so/{NOTION_DATABASE_ID}"


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
