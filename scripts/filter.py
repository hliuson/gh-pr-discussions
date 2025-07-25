
import json
import sys
from pathlib import Path

INPUT_FILE = Path("mock_data.json")
OUTPUT_FILE = Path("filtered_output/filtered_output.json")

def is_substantive(comment):
    text = comment['text'].strip().lower()
    author = comment['author'].lower()
    if 'bot' in author or author.endswith('-bot'):
        return False
    if len(text.split()) < 5:
        return False
    if any(kw in text for kw in ['nit', 'typo', 'ping', 'bump', 'spacing', 'lgtm', '+1']):
        return False
    return True

def filter_pr(pr):
    if not pr.get("merged", False):
        return None
    filtered_comments = [c for c in pr['comments'] if is_substantive(c)]
    if len(filtered_comments) < 2:
        return None
    pr['comments'] = filtered_comments
    return pr


def main():
    if not INPUT_FILE.exists():
        print(f"Input file {INPUT_FILE} does not exist.")
        sys.exit(1)

    with open(INPUT_FILE, 'r') as infile:
        data = json.load(infile)

    filtered_data = [filter_pr(pr) for pr in data if filter_pr(pr) is not None]

    with open(OUTPUT_FILE, 'w') as outfile:
        json.dump(filtered_data, outfile, indent=2)

    print(f"Filtered data written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()