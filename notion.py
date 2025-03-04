import os
import requests
from datetime import datetime

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_TEMPLATE_ID = os.getenv("NOTION_TEMPLATE_ID")

today = datetime.today().strftime("%Y-%m-%d")

if not NOTION_API_KEY or not NOTION_DATABASE_ID:
    log_message("ERROR: Missing environment variables!")
    exit(1)

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Default template_data value
template_data = None

try:
    template_response = requests.get(f"https://api.notion.com/v1/pages/{NOTION_TEMPLATE_ID}", headers=headers)
except Exception as e:
    print(f"Failed to get Notion Template json: {e}")

if template_response.status_code == 200:
    template_data = template_response.json()
else:
    print(f"Bad response from Notion for Template: {template_response.json()}")
    exit(1)

print("template_data:")
print(template_data)

page_data = {
    "parent": {"database_id": NOTION_DATABASE_ID},
    "properties": {
        "Name": {"title": [{"text": {"content": today}}]},
        **template_data.get("properties", {})
    }
}

response = requests.post("https://api.notion.com/v1/pages", json=page_data, headers=headers)
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print(f"[{timestamp}] {response.json()}")
