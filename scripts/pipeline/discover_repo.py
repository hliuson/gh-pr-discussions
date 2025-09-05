import requests
import aiohttp
import asyncio
import json

from shared_utils import saveJSON, summaryDisplay, HEADERS, MAX_REPOS

# Searches python Repos for at least 1000 stars, 100 forks, and not older than Jan 1st 2024

def load_existing_repo_ids(output_file):
      """Load existing repo IDs to avoid duplicates"""
      try:
          with open(output_file, 'r', encoding='utf-8') as f:
              existing_repos = json.load(f)
          existing_ids = {repo['id'] for repo in existing_repos}
          print(f"Found {len(existing_repos)} existing repos, will skip duplicates")
          return existing_repos, existing_ids
      except FileNotFoundError:
          print("No existing repos found, starting fresh")
          return [], set()

async def searchRepos(session, language, page, skip_ids=None, min_stars=1000, min_forks=100):

  search_url = "https://api.github.com/search/repositories"

  queries = [
      f"stars:>{min_stars}",
      f"forks:>{min_forks}",
      f"language:{language}",
      "pushed:>2023-01-01",
      "archived:false"
  ]

  params = {
      'q': ' '.join(queries),
      'sort': 'stars',
      'order': 'desc',
      'per_page': MAX_REPOS,
      'page': page
  }

  print(f"Repo query: {params['q']}")

  async with session.get(search_url, headers=HEADERS, params=params) as response:
    data = await response.json()
    all_repos = data.get('items', [])
    # if response.status_code != 200:
    #   print(f"Error: {response.status_code} -  {response.text}") ################################################## For Debugging
    #   return []

    if skip_ids:
       all_repos = [repo for repo in all_repos if repo['id'] not in skip_ids]
       
    return all_repos

async def searchPages(session, language, skip_ids=None):
  tasks = [searchRepos(session, language, page, skip_ids) for page in range(1, 8)]

  page_results = await asyncio.gather(*tasks)

  all_repos = []
  for page_repos in page_results:
    all_repos.extend(page_repos)
  
  return all_repos

#Filter repositories with conditions below and create and return a dictionary with important imfo about the repository

def filterRepos(repos):

  quality_repos = []

  avoid_keywords = [
    'awesome-',                    
    'free-programming-books',      
    'big-list-of',                
    'list of useful',             
    'list of awesome',            
    'opinionated list',           
    'various collection',         
    'collection of awesome',      
  ]

  whitelist_repos = [
    'labmlai/annotated_deep_learning_paper_implementations',  # Actual code implementations
  ]

  i = 1
  for repo in repos:
    if (repo['stargazers_count'] >= 500 and # Greater than 1000 stars
        repo['forks_count'] >= 50 and       # More than 100 forks
        repo['open_issues_count'] > 5 and    # Look for Repos that have open issues, tackling real challenges developers face
        repo['open_issues_count'] < 500 and  # But not more than 500 then there might be issues with the repo and code base itself
        repo['size'] > 100 and               # Look for a Repo greater than 100KB in size
        repo.get('license') and              # Allows us to use this repo legally
        repo.get('description') and          # Has a description
        len(repo['description']) > 20 and    # Description is at least 20 characters
        not repo['archived'] and             # Look for active Repo
        not repo['disabled']):               # Look for active Repo part 2

      quality_repo = {
          'index': i,
          'total_index': None,
          'id': repo['id'],
          'name': repo['name'],
          'full_name': repo['full_name'],
          'description': repo['description'][:200],
          'stars': repo['stargazers_count'],
          'forks': repo['forks_count'],
          'language': repo['language'],
          'open_issues': repo['open_issues_count'],
          'updated_at': repo['updated_at'],
          'pushed_at': repo['pushed_at'],
          'license': repo['license']['name'] if repo['license'] else 'Unknown',
          'size': repo['size'],
          'has_wiki': repo['has_wiki'],
          'has_pages': repo['has_pages'],
          'url': repo['html_url']
      }

      name_lower = quality_repo['name'].lower()
      desc_lower = quality_repo.get('description', '').lower()

      if quality_repo['full_name'] in whitelist_repos:
        print(f"Kept whitelisted repo: {quality_repo['full_name']}")
        i += 1
        quality_repos.append(quality_repo)
        continue

      is_directory = any(keyword in name_lower or keyword in desc_lower for keyword in avoid_keywords)

      if is_directory:
        print(f"Filtered out directory repo: {quality_repo['full_name']}")
        for keyword in avoid_keywords:
          if keyword in name_lower or keyword in desc_lower:
            print(f"   Filtered due to keyword '{keyword}' in {name_lower} or {desc_lower}") ################################################## For Debugging
      else: 
        quality_repos.append(quality_repo)
        i += 1

  return quality_repos


async def repositoryDiscovery():
    print("=== STAGE 1: REPOSITORY DISCOVERY ===")

    output_file = '../../data/pipeline/1_quality_repos.json'

    existing_repos, existing_ids = load_existing_repo_ids(output_file)

    languages = ['C++', 'java', 'C', 'rust', 'go']

    async with aiohttp.ClientSession() as session:
      # Search for repositories

      language_tasks = [searchPages(session, lang, skip_ids=existing_ids) for lang in languages]

      language_results = await asyncio.gather(*language_tasks)

      repos = []
      for repo in language_results:
        repos.extend(repo)
      print(f"Found {len(repos)} repositories from search") ################################################## For Debugging

      # Filter for quality
      quality_repos = filterRepos(repos)
      print(f"Filtered to {len(quality_repos)} high-quality repositories\n") ################################################## For Debugging

      combined_repos = existing_repos + quality_repos

      for i, repo in enumerate(combined_repos, 1):
         repo['total_index'] = i

      # Save to JSON
      saveJSON(combined_repos, output_file)
      summaryDisplay(combined_repos, "repositories")

      return combined_repos

if __name__ == "__main__":
    asyncio.run(repositoryDiscovery())