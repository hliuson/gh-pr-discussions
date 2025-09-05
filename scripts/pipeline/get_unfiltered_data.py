import json
import requests
import time
from shared_utils import HEADERS, REQUEST_DELAY

def get_finetune_data(input_file, output_file):
    
    try:
        with open(input_file, 'r', encoding="utf-8") as file:
            data = json.load(file)
        
        transformed_data = []
        index = 1
        for item in data:
            repository = item.get("repository", "")
            pr_number = item.get("pr_number", "")
            code_diff = getPRDiff(repository, pr_number)

            transformed_item = {
                "index": index,
                "repository": repository,
                "pr_number": pr_number,
                "comments": item.get("comments", ""),
                "code_diff": code_diff,
            }
            transformed_data.append(transformed_item)
            print(f"Processing pr {index} #{pr_number}")
            index += 1

        with open(output_file, 'w', encoding="utf-8") as file:
            json.dump(transformed_data, file, indent=2, ensure_ascii=False)
        
        print(f"Successfully transformed {len(transformed_data)} items")
        print(f"Output written to: {output_file}")

    except FileNotFoundError:
        print(f"Error: Input file {input_file} not found.")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON in file '{input_file}'")
    except Exception as e:
        print(f"Error: {str(e)}")




def getPRDiff(repo_fullName, pr_number):
  url = f"https://api.github.com/repos/{repo_fullName}/pulls/{pr_number}"

  diff_headers = {
     **HEADERS,
      'Accept': 'application/vnd.github.v3.diff'
  }

  #print(f"      Fetching PR diff from: {url}") ################################################## For Debugging
  time.sleep(REQUEST_DELAY)

  response = requests.get(url, headers=diff_headers)

  if response.status_code != 200:
    print(f"Error getting PR diff for PR #{pr_number}: {response.status_code}")
    print(f"      Error details: {response.text[:200]}")
    return None
  
  return response.text

get_finetune_data("../../data/pr_discussions_cleaned.json", "../../data/pipeline/3_unfiltered_data.json")