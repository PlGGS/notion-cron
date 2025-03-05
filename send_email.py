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

def get_page_content(page_id):
    response = None
    
    try:
        response = requests.get(f"https://api.notion.com/v1/blocks/{page_id}/children", headers=headers)
    except Exception as e:
        print(f"Failed to get Notion page content: {e}")

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Bad response from Notion for page content: {response.json()}")
        return None


# Default page_id values
food_tracker_page_id = get_page_id(NOTION_FOOD_TRACKER_DATABASE_ID)
daily_journal_page_id = get_page_id(NOTION_DAILY_JOURNAL_DATABASE_ID, 1) # We want the second from the top to get todo blocks from prev day

# Get all blocks within the page
blocks = get_page_content(daily_journal_page_id).get("results", [])

# Find all unchecked 'to_do' blocks after "3 Key Things for Tomorrow"
target_heading = "3 Key Things for Tomorrow"
found_heading = False
todo_blocks = []

# Insert blocks into todo_blocks if they're unchecked with 'type' of 'to_do'
for block in blocks:
    # If we found the target heading, start collecting 'to_do' blocks
    if found_heading:
        if block.get("type") == "to_do" and block["to_do"].get("checked") == False:
            todo_blocks.append(block)
        else:
            continue
    
    # Check if current block is the target heading
    elif block.get("type") == "heading_2":
        text = block["heading_2"]["rich_text"][0]["plain_text"] if block["heading_2"]["rich_text"] else ""
        if text == target_heading:
            found_heading = True  # Start collecting from the next block



def get_children(block_id):
    response = requests.get(f"https://api.notion.com/v1/blocks/{block_id}/children", headers=headers)

    if response.status_code != 200:
        print(f"Failed to fetch children for block {block_id}: {response.text}")
        return []

    children = response.json().get("results", [])

    for child in children:
        if child.get("has_children"):
            child["children"] = get_children(child["id"])  # Recursively fetch children

    return children

def update_page_content(page_id, json, with_children=False):
    response = None
    
    try:
        response = requests.patch(f"https://api.notion.com/v1/blocks/{page_id}/children", json=json, headers=headers)
        
    except Exception as e:
        print(f"Failed to get Notion page content: {e}")

    if response.status_code == 200:
        print("Updated today's journal successfully!")
    else:
        print(f"Bad response from Notion for attempted update to page content: {response.json()}")

# Get top journal page to insert into
top_journal_page_id = get_page_id(NOTION_DAILY_JOURNAL_DATABASE_ID, 0)

# Create page_data from todo_blocks
page_data = {
	"children": []
}

for block in todo_blocks:
    page_data["children"].append(block)
    page_data["children"].append(get_children(block["id"]))

# Insert todo_blocks at the bottom of the newest journal page
update_page_content(top_journal_page_id, page_data)





def format_todo_list(blocks, indent=0):
    formatted_list = ""
    
    for block in blocks:
        if block.get("type") == "to_do":
            todo = block["to_do"]
            checked = "x" if todo.get("checked") else " "
            
            # Loop over each "rich_text" element to build full string in plaintext
            text = " ".join([item["text"]["content"].strip() for item in todo["rich_text"]])

            formatted_list += f"{'    ' * indent}- [{checked}]  {text}\n"
            
            if block.get("has_children"):
                # Fetch and process child blocks recursively
                child_blocks = get_children(block["id"])
                formatted_list += format_todo_list(child_blocks, indent + 1)

    return formatted_list

# Get to do list as list of formatted strings
formatted_todo_list = format_todo_list(todo_blocks)

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

if daily_journal_page_id is not None:
    emailBody += f"\n\nHere's today's daily journal page: https://www.notion.so/{daily_journal_page_id} \
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
