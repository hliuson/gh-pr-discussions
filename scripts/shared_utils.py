import json
import os

GITHUB_TOKEN = os.environ.get('MY_GITHUB_TOKEN')

HEADERS = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github+json'
}

REQUEST_DELAY = 2
MAX_REPOS = 100
MAX_PRS_PER_REPO = 10

def saveJSON(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {filename}")
    return filename

# Display the info gathered, used for visual of progress or debugging
def summaryDisplay(data, data_type="data"):
    print(f"\n=== {data_type.upper()} SUMMARY ===")
    print(f"Total items: {len(data)}")

    if data and isinstance(data[0], dict):
        print("Sample item keys:", list(data[0].keys()))
        if len(data) > 0:
            print("First item preview:")
            for k, v in list(data[0].items())[:3]:
                preview = str(v)[:100] + "..." if len(str(v)) > 100 else str(v)
                print(f"  {k}: {preview}")

    return data