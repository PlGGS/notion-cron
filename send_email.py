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

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def get_page_id(database_id, index=0):
    response = None
    
    try:
        response = requests.post(f"https://api.notion.com/v1/databases/{database_id}/query", headers=headers)
    except Exception as e:
        print(f"Failed to query Notion: {e}")

    if response.status_code == 200:
        database_data = response.json()
        results = database_data["results"]
        
        if results:
            if results[index]:
                recent_page = results[index] # Get the most recent page (first in the sorted list)
                return recent_page["id"].replace('-', '')
            else:
                print(f"Page data does not include row at index: {database_data}")
                return None
        else:
            print(f"No results returned in page data: {database_data}")
            return None
    else:
        print(f"Bad response from Notion: {response.json()}")
        return None

def get_page_metadata(page_id):
    response = None
    
    try:
        response = requests.get(f"https://api.notion.com/v1/pages/{page_id}", headers=headers)
    except Exception as e:
        print(f"Failed to get Notion page metadata: {e}")

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Bad response from Notion for page metadata: {response.json()}")
        return None

# Default page_id values
food_tracker_page_id = get_page_id(NOTION_FOOD_TRACKER_DATABASE_ID)
prev_journal_page_id = get_page_id(NOTION_DAILY_JOURNAL_DATABASE_ID, 1) # We want the second from the top to get todo blocks from prev day

# Recursively gets all child blocks from a parent (or page)
def get_children(block_id):
    response = requests.get(f"https://api.notion.com/v1/blocks/{block_id}/children", headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch children for block {block_id}: {response.text}")
        return []

    children = response.json().get("results", [])

    for child in children:
        if child.get("has_children"):
            child.setdefault("children", [])
            child["children"] = get_children(child["id"])  # Recursively fetch children

    return children

def append_block_children(page_id, json):
    response = None
    
    try:
        response = requests.patch(f"https://api.notion.com/v1/blocks/{page_id}/children", json=json, headers=headers)
        
    except Exception as e:
        print(f"Failed to get Notion page content: {e}")

    if response.status_code == 200:
        print("Successfully appended block to today's journal!")
    else:
        print(f"Bad response from Notion for attempted update to page content: {response.json()}")


def add_todo_blocks_to_page(target_page_id, blocks):
    for block in blocks:
        if block.get("type") == "to_do":
            block_payload = {
                "children": [
                    {
                        "object": "block",
                        "type": "to_do",
                        "to_do": {
                            "rich_text": block["to_do"].get("rich_text", []),
                            "checked": block["to_do"].get("checked", False)
                        }
                    }
                ]
            }

            # Send PATCH request to create the to-do block on the new page
            append_block_children(target_page_id, block_payload)

            # If the block has children, recursively add them
            if block.get("children"):
                # Get the last inserted block ID (assuming last response contains the new block ID)
                new_block_id = get_last_inserted_block_id(target_page_id)

                # Recursively insert child blocks into this newly created block
                add_todo_blocks_to_page(new_block_id, block["children"])

def get_last_inserted_block_id(page_id):
    response = requests.get(f"https://api.notion.com/v1/blocks/{page_id}/children", headers=headers)
    
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return results[-1]["id"]  # Get the last inserted block's ID
    print(f"Failed to fetch last inserted block for {page_id}: {response.text}")
    return None

def remove_checked_blocks(blocks, only_top_level=False):
    for block in blocks:
        print(block)

        if only_top_level == False:
            if block.get("children"):
                remove_checked_blocks(block["children"])

        if block.get("type") == "to_do" and block["to_do"].get("checked"):
            print("Removed")
            blocks.remove(block)

    return blocks

# Get previous day's todo blocks
prev_day_todo_blocks = get_children(prev_journal_page_id)

# Exclude top level checked blocks
prev_day_todo_blocks = remove_checked_blocks(prev_day_todo_blocks, True)

# Get top journal page to insert previous day's todo blocks into
top_journal_page_id = get_page_id(NOTION_DAILY_JOURNAL_DATABASE_ID, 0)
# Insert previous day's todo blocks at the bottom of the newest journal page
add_todo_blocks_to_page(top_journal_page_id, prev_day_todo_blocks)

def format_todo_list(blocks, indent=0):
    formatted_list = ""

    for block in blocks:
        if block.get("type") == "to_do":
            todo = block["to_do"]
            checked = "x" if todo.get("checked") else " "

            # Build the full string in plaintext from "rich_text"
            text = " ".join([item["text"]["content"].strip() for item in todo.get("rich_text", [])])

            formatted_list += f"{'    ' * indent}- [{checked}] {text}\n"

            # Recursively format any children already stored in the block
            if "children" in block and isinstance(block["children"], list):
                formatted_list += format_todo_list(block["children"], indent + 1)

    return formatted_list

# Get to do list as list of formatted strings
formatted_todo_list = format_todo_list(prev_day_todo_blocks)

# Prepare email
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

if top_journal_page_id is not None:
    emailBody += f"\n\nHere's today's daily journal page: https://www.notion.so/{top_journal_page_id} \
        \n\nAnd here's today's Key Tasks:\n"
    
    for item in formatted_todo_list:
        emailBody += item
else:
    emailBody = f"\n\nGood morning! Couldn't get today's daily journal page ID, so here's the general daily journal page: https://www.notion.so/{NOTION_DAILY_JOURNAL_DATABASE_ID}"

message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject
message.attach(MIMEText(emailBody, "plain"))

try:
    with smtplib.SMTP_SSL(smtp_ssl, 465) as server:
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        print("Email sent successfully!")
except Exception as e:
    print(f"Failed to send email: {e}")
