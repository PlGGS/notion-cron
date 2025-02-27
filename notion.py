import os
import requests
from datetime import datetime

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_TEMPLATE_ID = os.getenv("NOTION_TEMPLATE_ID")

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    log_message("ERROR: Missing environment variables!")
    exit(1)

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

today = datetime.today().strftime("%Y-%m-%d")

data = {
    "parent": {"database_id": NOTION_DATABASE_ID},
    "properties": {
        "Name": {"title": [{"text": {"content": today}}]}
    },
    "template": {"id": NOTION_TEMPLATE_ID}
}

response = requests.post("https://api.notion.com/v1/pages", json=data, headers=headers)
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"[{timestamp}] {response.json()}")
