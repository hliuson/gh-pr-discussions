import time
import re
import requests

from repo_discovery import repos
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
def filterPRs(prs):
  print(f"    Filtering {len(prs)} PRs...")
  quality_prs = []
  no_comments_count = 0

  for pr in prs:
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
      print(f"    Filtered out PR #{pr.get('number', '?')}: Draft PR")

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
  #print(f"      API returned {len(comments)} comments for PR #{pr_number}") ################################################## For Debugging

  return comments

#Filter out comments with patterns of botting and non-substantial info
def processComments(comments, pr_data):

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

    if not (is_bot or is_too_short or is_unwanted or is_minor_fix):
            cleaned_comment = {
                'pr_title': pr_data.get('title', 'Unknown'),
                'pr_body': pr_data.get('body', '')[:500] if pr_data.get('body') else '',
                'pr_number': pr_data.get('number', 0),
                'comment_id': comment['id'],
                'author': username,
                'body': body,
                'created_at': comment['created_at'],
                'updated_at': comment['updated_at'],
                'repository': pr_data.get('repository_full_name', 'Unknown'),
                'comment_length': len(body)
            } # Returns a dictionary of important comment information

            quality_comments.append(cleaned_comment)

    return quality_comments
  
def prDiscussionExtraction(repos):

    print("=== STAGE 2: PR DISCUSSION EXTRACTION ===")

    all_discussions = []

    for i, repo in enumerate(repos[:10]):  # !!!!!IMPORTANT!!!!! Limit to first 10 repo for testing
        #print(f"\nProcessing repository {i+1}/{min(len(repos), 10)}: {repo['full_name']}")

        # Get pull requests
        prs = searchPRsWithComments(repo['full_name'], max_prs=100)
        print(f"  Total PRs found: {len(prs)}")

        # Filter substantial PRs
        substantial_prs = filterPRs(prs)
        print(f"Found {len(substantial_prs)} substantial PRs")

        # Process each PR
        for pr in substantial_prs[:10]:  # !!!!!IMPORTANT!!!!! Limit PRs per repo
            #print(f"  Processing PR #{pr['number']}: {pr['title'][:50]}...")

            # Get comments
            comments = getComments(repo['full_name'], pr['number'])
            print(f"  Raw comments retrieved: {len(comments)}")

            # Clean and filter comments
            quality_comments = processComments(comments, pr)
            print(f"  Quality comments after filtering: {len(quality_comments)}")

            all_discussions.extend(quality_comments)

    print(f"\nTotal quality discussions collected: {len(all_discussions)}")

    # Save to JSON
    if all_discussions:
        filename = saveJSON(all_discussions, 'data/pr_discussions_cleaned.json')
        summaryDisplay(all_discussions, "discussions")

    return all_discussions
  

discussions = prDiscussionExtraction(repos)

print("\n Pipeline completed!")
print(f" Collected {len(repos)} repositories and {len(discussions)} discussions")
print("\n Output files:")
print("  - high_quality_repos.json")
print("  - pr_discussions_cleaned.json")