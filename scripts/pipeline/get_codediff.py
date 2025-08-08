import time
import requests
from shared_utils import HEADERS, REQUEST_DELAY

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

print(getPRDiff("TheAlgorithms/Python", 7092))  
