import json
import os
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.environ.get('MY_GITHUB_TOKEN')

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

REQUEST_DELAY = 0.72
MAX_REPOS = 100
MAX_PRS_PER_REPO = 10

def saveJSON(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

# Display the info gathered, used for visual of progress or debugging
def summaryDisplay(data, data_type="data"):
    print(f"\n=== {data_type.upper()} SUMMARY ===")
    print(f"Total items: {len(data)}")

    return data