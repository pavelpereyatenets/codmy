import os
import openai
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# Load environment variables
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
GOOGLE_CREDENTIALS_FILE = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
SPREADSHEET_NAME = os.environ.get("SPREADSHEET_NAME", "ChatGPT Results")
URLS_FILE = os.environ.get("URLS_FILE", "urls.txt")

if not OPENAI_API_KEY:
    raise EnvironmentError("OPENAI_API_KEY environment variable is required")
if not GOOGLE_CREDENTIALS_FILE:
    raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS environment variable is required")

# Setup OpenAI client
openai.api_key = OPENAI_API_KEY

# Setup Google Sheets client
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_CREDENTIALS_FILE, scope)
client = gspread.authorize(creds)

def get_or_create_sheet(spreadsheet_name):
    try:
        return client.open(spreadsheet_name).sheet1
    except gspread.SpreadsheetNotFound:
        sh = client.create(spreadsheet_name)
        sh.share(None, perm_type='anyone', role='writer')
        return sh.sheet1

sheet = get_or_create_sheet(SPREADSHEET_NAME)


def read_urls(path):
    with open(path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def query_chatgpt(url):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": url}],
    )
    return response.choices[0].message['content'].strip()


urls = read_urls(URLS_FILE)

for url in urls:
    try:
        result = query_chatgpt(url)
    except Exception as e:
        result = f"Error: {e}"
    sheet.append_row([url, result])
    print(f"Processed {url}")
