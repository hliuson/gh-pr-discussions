import time
import re
import requests
import aiohttp
import asyncio
import json
from shared_utils import saveJSON, summaryDisplay, HEADERS, REQUEST_DELAY
import os

''' Look for Pull Requests that specifically have comments, this is a pivot from the original idea of just taking the most recent prs and filtering them
since many of the new prs(up to 100, when I tested) had no comments'''



def getRepos():
   with open('../../data/pipeline/1_quality_repos.json', 'r', encoding="utf-8") as f:
        repos = json.load(f)
   return repos



async def searchPRsWithComments(session, repo_fullName, max_prs=50):

    search_url = "https://api.github.com/search/issues"

    await asyncio.sleep(2.5)

    # Search for PRs with comments in this specific repo
    query = f"repo:{repo_fullName} type:pr comments:>0"

    params = {
        'q': query,
        'sort': 'comments',     # Sort by number of comments
        'order': 'desc',        # Most comments first
        'per_page': max_prs
    }

    try:
       async with session.get(search_url, headers=HEADERS, params=params) as response:
          if response.status != 200:
             print(f"Error searching PRs for {repo_fullName}: {response.status}")
             return []
          
          data = await response.json()
          prs = data.get("items", [])

          for pr in prs:
            pr['repository_full_name'] = repo_fullName

          return prs
    except Exception as e:
      print(f"Error fetching PRs for {repo_fullName}: {e}")
      return []



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
async def getComments(session, repo_fullName, pr_number):

  url = f"https://api.github.com/repos/{repo_fullName}/issues/{pr_number}/comments"

  try:
     async with session.get(url, headers=HEADERS) as response:
        if response.status != 200:
           print(f"Error searching PRs for {repo_fullName}: {response.status}")
           return []
        
        comments = await response.json()
        return comments
  except Exception as e:
     print(f"Error fetching comments for PR #{pr_number}: {e}")
     return []
  


async def getDiff(session, repo_fullName, pr_number):
      """Get PR diff - now async"""

      url = f"https://api.github.com/repos/{repo_fullName}/pulls/{pr_number}"

      diff_headers = {
          **HEADERS,
          'Accept': 'application/vnd.github.v3.diff'
      }

      try:
          async with session.get(url, headers=diff_headers) as response:
              if response.status != 200:
                  print(f"Error getting PR diff for PR #{pr_number}: {response.status}")
                  return None

              return await response.text()

      except Exception as e:
          print(f"Error fetching diff for PR #{pr_number}: {e}")
          return None



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
                'index': None,
                'repository': pr_data.get('repository_full_name', 'Unknown'),
                'pr_title': pr_data.get('title', 'Unknown'),
                'pr_body': pr_data.get('body', '')[:500] if pr_data.get('body') else '',
                'pr_number': pr_data.get('number', 0),
                'comments': quality_comments,
                'num_comments': len(quality_comments),
                'diff': codeDiff,
                'diff_length': len(codeDiff)
  }

  return cleaned_comment
  


async def processPR(session, repo_fullName, prs, semaphore):
   """Process multiple PRs concurrently with rate limiting"""
   async def processSinglePR(pr):
      async with semaphore:
        pr_number = pr['number']

        comment_task = getComments(session, repo_fullName, pr_number)
        diff_task = getDiff(session, repo_fullName, pr_number)

        comments, codeDiff = await asyncio.gather(comment_task, diff_task)

        quality_comments = processComments(comments, pr, codeDiff)

        return quality_comments if quality_comments['num_comments'] > 10 else None
   tasks = [processSinglePR(pr) for pr in prs]
   results =  await asyncio.gather(*tasks, return_exceptions=True)

   valid_results = [r for r in results if r is not None and not isinstance(r, Exception)]

   return valid_results



async def prDiscussionExtraction(repos, iteration=0, checkpoint_callback=None, start_repo=0):
    print("=== STAGE 2: PR DISCUSSION EXTRACTION ===")

    all_discussions = []

    semaphore = asyncio.Semaphore(15)
    index = 1
    num_repo = 3 #change to 40
    pr_per = 5 #change to 60

    async with aiohttp.ClientSession() as session:

       for i, repo in enumerate(repos[:num_repo]):
          if i < start_repo:
            print(f"⏭️ Skipping repo {i+1}/{num_repo}: {repo['full_name']} (already completed)")
            continue

          print(f"\n🔄 Processing repo {i+1}/{num_repo}: { repo['full_name']}")

          # Search for PRs
          prs = await searchPRsWithComments(session, repo['full_name'], max_prs=100)
          print(f"   Total PRs found: {len(prs)} PRs")

          # Filter PRs
          substantial_prs = filterPRs(prs, repo['full_name'])[:pr_per]
          print(f"   Found {len(substantial_prs)} substantial PRs")

          if substantial_prs:
            repo_discussions = await processPR(session, repo['full_name'], substantial_prs, semaphore)

            all_discussions.extend(repo_discussions)

          if checkpoint_callback:
             last_completed_repo = repo['full_name']   
             checkpoint_callback(iteration, i + 1, last_completed_repo)
             print(f"✅ Checkpoint saved: {i + 1}/{num_repo} repos completed")
                    

    print(f"\n Total quality discussions collected: {len(all_discussions)}")
    
    if all_discussions:

      for discussion in all_discussions:
        if discussion:  
          discussion['index'] = index 
          index += 1  
      pr_dir = "../../data/iterations/pr"
      os.makedirs(pr_dir, exist_ok=True)
      saveJSON(all_discussions, f'{pr_dir}/prs_iter{iteration}.json')

    return all_discussions
  


async def main():
   repos = getRepos()
   discussions = await prDiscussionExtraction(repos)

   print("\n Pipeline completed!")
   print(f" Collected {len(repos)} repositories and {len(discussions)} discussions")
   return discussions

if __name__ == "__main__":
   discussions = asyncio.run(main())