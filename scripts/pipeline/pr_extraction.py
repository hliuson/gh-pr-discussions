import time
import re
import requests
import json
from shared_utils import saveJSON, summaryDisplay, HEADERS, REQUEST_DELAY

''' Look for Pull Requests that specifically have comments, this is a pivot from the original idea of just taking the most recent prs and filtering them
since many of the new prs(up to 100, when I tested) had no comments'''

def searchPRsWithComments(repo_fullName, max_prs=50):

    search_url = "https://api.github.com/search/issues"

    # Search for PRs with comments in this specific repo
    query = f"repo:{repo_fullName} type:pr comments:>0"

    params = {
        'q': query,
        'sort': 'comments',     # Sort by number of comments
        'order': 'desc',        # Most comments first
        'per_page': max_prs
    }

    #print(f"Searching for PRs with comments in {repo_fullName}") ################################################## For Debugging
    time.sleep(REQUEST_DELAY)

    response = requests.get(search_url, headers=HEADERS, params=params)

    if response.status_code != 200:
        print(f"Error searching PRs: {response.status_code}") ################################################## For Debugging
        return []

    prs = response.json().get('items', [])

    for pr in prs:
        pr['repository_full_name'] = repo_fullName

    return response.json().get('items', [])

# Filter for quality PRS with the conditions specified below
def filterPRs(prs, repo_fullName):
  print(f"    Filtering {len(prs)} PRs...")
  quality_prs = []
  no_comments_count = 0

  for pr in prs:
    pr['repository_full_name'] = repo_fullName
    has_quality_title = len(pr.get('title', '')) > 10
    has_description = pr.get('body') and len(pr['body']) > 30
    has_comments = pr.get('comments', 0) > 0
    not_draft = not pr.get('draft', False)

    if (has_quality_title or has_description) and has_comments and not_draft:
      quality_prs.append(pr)

      ################################################## The proceeding logic is all for debugging
    elif pr.get('comments', 0) == 0:
      no_comments_count += 1
      # Only print first few to avoid spam
      if no_comments_count <= 3:
          print(f"    Filtered out PR #{pr.get('number', '?')}: No comments")
    elif pr.get('draft', False):
      pass
      #print(f"    Filtered out PR #{pr.get('number', '?')}: Draft PR")

    #print(f"    Summary: {no_comments_count} PRs with no comments") ################################################## For Debugging
    #print(f"    Found {len(quality_prs)} quality PRs") ################################################## For Debugging

  return quality_prs

#Get the comments from the chosen quality PRs
def getComments(repo_fullName, pr_number):

  url = f"https://api.github.com/repos/{repo_fullName}/issues/{pr_number}/comments"

  #print(f"      Fetching comments from: {url}") ################################################## For Debugging
  time.sleep(REQUEST_DELAY)

  response = requests.get(url, headers=HEADERS)

  #print(f"      Response status: {response.status_code}") ################################################## For Debugging

  if response.status_code != 200:
    print(f"Error getting comments for PR #{pr_number}: {response.status_code}")
    print(f"      Error details: {response.text}")
    return []

  comments = response.json()
  print(f"      API returned {len(comments)} comments for PR #{pr_number}") ################################################## For Debugging

  return comments

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

#Filter out comments with patterns of botting and non-substantial info
def processComments(comments, pr_data, codeDiff):

  bot_patterns = [
      'bot', 'Bot', '[bot]', 'github-actions', 'dependabot',
      'codecov', 'travis', 'circleci', 'sonarcloud'
  ]

  unwanted_patterns = [
      r'^lgtm$',
      r'^👍$',
      r'^thanks$',
      r'^ping @',
      r'^cc @',
      r'^\+1$',
      r'^approved$',
      r'^merge$'
  ]

  quality_comments = []

  for comment in comments:
    username = comment['user']['login']
    body = comment['body']

    is_bot = (any(pattern in username for pattern in bot_patterns) or
            comment['user']['type'] == 'Bot')

    is_too_short = len(body) < 30

    is_unwanted = any(re.match(pattern, body.strip(), re.IGNORECASE)
                    for pattern in unwanted_patterns)

    is_minor_fix = re.match(r'^(fix:|type:|lint:|format:)', body, re.IGNORECASE)

    reasons_filtered = []
    if is_bot:
        reasons_filtered.append("IS_BOT")
    if is_too_short:
        reasons_filtered.append("TOO_SHORT")
    if is_unwanted:
        reasons_filtered.append("UNWANTED_PATTERN")
    if is_minor_fix:
        reasons_filtered.append("MINOR_FIX")
        
    if reasons_filtered:
        print(f"❌ FILTERED OUT - Reasons: {', '.join(reasons_filtered)}")
    else:
        print(f"✅ PASSED - Adding to quality comments")
        quality_comments.append(body)
          
    #quality_comments.append(body)

  cleaned_comment = {
                'pr_title': pr_data.get('title', 'Unknown'),
                'pr_body': pr_data.get('body', '')[:500] if pr_data.get('body') else '',
                'pr_number': pr_data.get('number', 0),
                'comments': quality_comments,
                'num_comments': len(quality_comments),
                'repository': pr_data.get('repository_full_name', 'Unknown'),
                'diff_length': len(codeDiff) if codeDiff else 0,
                'code_diff': codeDiff[:300]
  }
  return cleaned_comment

def getRepos():
   with open('../../data/high_quality_repos.json', 'r', encoding="utf-8") as f:
        repos = json.load(f)
   return repos
  
def prDiscussionExtraction(repos):

    print("=== STAGE 2: PR DISCUSSION EXTRACTION ===")

    all_discussions = []
    critique_data_unfiltered = []

    for i, repo in enumerate(repos[:5]):  # !!!!!IMPORTANT!!!!! Limit to first 10 repo for testing
        #print(f"\nProcessing repository {i+1}/{min(len(repos), 10)}: {repo['full_name']}")

        # Get pull requests
        prs = searchPRsWithComments(repo['full_name'], max_prs=100)
        print(f"  Total PRs found: {len(prs)}")

        # Filter substantial PRs
        substantial_prs = filterPRs(prs, repo['full_name'])
        print(f"Found {len(substantial_prs)} substantial PRs")

        # Process each PR
        for pr in substantial_prs[:10]:  # !!!!!IMPORTANT!!!!! Limit PRs per repo
            #print(f"  Processing PR #{pr['number']}: {pr['title'][:50]}...")

            # Get comments
            comments = getComments(repo['full_name'], pr['number'])

            codeDiff = getPRDiff(repo['full_name'], pr['number'])

            # Clean and filter comments
            quality_comments = processComments(comments, pr, codeDiff)

            #print(quality_comments)

            if len(quality_comments) > 0:
              print(f"  Raw comments retrieved: {len(comments)}")
              print(f"  Quality comments after filtering: {quality_comments['num_comments']}")

            #print(pr_with_comments)   

            if quality_comments['num_comments'] > 5:
                critique_data = {
                   'comments': quality_comments['comments'],
                   'code_diff': codeDiff,
                }
                critique_data_unfiltered.append(critique_data)

                all_discussions.append(quality_comments)

    print(f"\nTotal quality discussions collected: {len(all_discussions)}")

    #Save to JSON
    if all_discussions:
        filename = saveJSON(all_discussions, '../../data/pr_discussions_test.json')
        summaryDisplay(all_discussions, "discussions")

    if critique_data_unfiltered:
       pass
        #filename = saveJSON(critique_data_unfiltered, '../../data/filtered/unfiltered_critique_data.json')
        #summaryDisplay(all_discussions, "discussions")

    return all_discussions
  

discussions = prDiscussionExtraction(getRepos())

print("\n Pipeline completed!")
print(f" Collected {len(getRepos())} repositories and {len(discussions)} discussions")
print("\n Output files:")
print("  - high_quality_repos.json")
print("  - pr_discussions_cleaned.json")