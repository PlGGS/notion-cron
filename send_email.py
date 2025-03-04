import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import requests
from dotenv import load_dotenv

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_WORKSPACE = os.getenv("NOTION_WORKSPACE")
NOTION_FOOD_TRACKER_DATABASE_ID = os.getenv("NOTION_FOOD_TRACKER_DATABASE_ID")
NOTION_DAILY_JOURNAL_DATABASE_ID = os.getenv("NOTION_DAILY_JOURNAL_DATABASE_ID")

def get_top_page_id(database_id):
    try:
        response = requests.post(f"https://api.notion.com/v1/databases/{database_id}/query", headers=headers)
    except Exception as e:
        print(f"Failed to query Notion: {e}")

    if response.status_code == 200:
        database_data = response.json()
        results = database_data["results"]
        
        if results:
            recent_page = results[0] # Get the most recent page (first in the sorted list)
            return recent_page["id"].replace('-', '')
        else:
            print(f"No results returned in page data: {database_data}")
            return None
    else:
        print(f"Bad response from Notion: {response.json()}")
        return None

def get_page_json(page_id):
    try:
        response = requests.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers)
    except Exception as e:
        print(f"Failed to get Notion Template json: {e}")

    if response.status_code == 200:
        template_data = response.json()
    else:
        print(f"Bad response from Notion for Template: {response.json()}")
        return None

# Default page_id values
food_tracker_page_id = get_top_page_id(NOTION_FOOD_TRACKER_DATABASE_ID)
daily_journal_page_id = get_top_page_id(NOTION_DAILY_JOURNAL_DATABASE_ID)

daily_journal_data = get_page_json(daily_journal_page_id)
print(daily_journal_data)

# TODO get the three tasks from the json
threeKeyTasks = ''

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

sender_email = os.getenv("GMAIL_SENDER_EMAIL")
receiver_email = os.getenv("GMAIL_RECEIVER_EMAIL")
app_password = os.getenv("GMAIL_APP_PASSWORD")
smtp_ssl = os.getenv("SMTP_SSL")

subject = "LETS GET IT"
emailBody = ''
if food_tracker_page_id is not None:
    emailBody = f"Good morning! Here's today's food tracker page: https://www.notion.so/{food_tracker_page_id}"
else:
    emailBody = f"Good morning! Couldn't get today's food tracker page ID, so here's the general food tracker page: https://www.notion.so/{NOTION_FOOD_TRACKER_DATABASE_ID}"

if daily_journal_page_id is not None:
    emailBody += f"\n\nHere's today's daily journal page: https://www.notion.so/{daily_journal_page_id} \
        \n\nAnd here's today's 3 Key Tasks:\n{threeKeyTasks}"
else:
    emailBody = f"\n\nGood morning! Couldn't get today's daily journal page ID, so here's the general daily journal page: https://www.notion.so/{NOTION_DAILY_JOURNAL_DATABASE_ID}"

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
