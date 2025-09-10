import json
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

GITHUB_TOKEN = os.environ.get('MY_GITHUB_TOKEN')

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

REQUEST_DELAY = 0.72
MAX_REPOS = 100
MAX_PRS_PER_REPO = 10

TEST_MODE = True
ERROR_RATE = 0.3

def log_error(error_type, component, details, iteration=None):
    error_entry = {
        "timestamp": datetime.now().isoformat(),
        "iteration": iteration,
        "component": component,
        "error_type": error_type,
        "details": details
    }

    error_file = f"../../data/errors/error_log_iter{iteration}.json" if iteration else "../../data/errors/pipeline_errors.json"

    try:
        with open(error_file, 'a') as f:
            f.write(json.dumps(error_entry) + '\n')
    except Exception as e:
        print(f"Failed to log error: {e}")

def saveJSON(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return filename

# Display the info gathered, used for visual of progress or debugging
def summaryDisplay(data, data_type="data"):
    print(f"\n=== {data_type.upper()} SUMMARY ===")
    print(f"Total items: {len(data)}")

    return data