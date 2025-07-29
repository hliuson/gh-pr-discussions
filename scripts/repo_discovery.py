import requests

from shared_utils import saveJSON, summaryDisplay, HEADERS, MAX_REPOS


# Searches python Repos for at least 1000 stars, 100 forks, and not older than Jan 1st 2024
def searchRepos(language='python', min_stars=1000, min_forks=100):

  search_url = "https://api.github.com/search/repositories"

  queries = [
      f"stars:>{min_stars}",
      f"forks:>{min_forks}",
      f"language:{language}",
      "pushed:>2024-01-01",
      "archived:false"
  ]

  params = {
      'q': ' '.join(queries),
      'sort': 'stars',
      'order': 'desc',
      'per_page': MAX_REPOS
  }

  print(f"Repo query: {params['q']}")

  response = requests.get(search_url, headers=HEADERS, params=params)

  if response.status_code != 200:
    print(f"Error: {response.status_code} -  {response.text}") ################################################## For Debugging
    return []

  return response.json().get('items', [])

#Filter repositories with conditions below and create and return a dictionary with important imfo about the repository
def filterRepos(repos):

  quality_repos = []

  for repo in repos:
    if (repo['stargazers_count'] >= 1000 and # Greater than 1000 stars
        repo['forks_count'] >= 100 and       # More than 100 forks
        repo['open_issues_count'] > 5 and    # Look for Repos that have open issues, tackling real challenges developers face
        repo['open_issues_count'] < 500 and  # But not more than 500 then there might be issues with the repo and code base itself
        repo['size'] > 100 and               # Look for a Repo greater than 100KB in size
        repo.get('license') and              # Allows us to use this repo legally
        repo.get('description') and          # Has a description
        len(repo['description']) > 20 and    # Description is at least 20 characters
        not repo['archived'] and             # Look for active Repo
        not repo['disabled']):               # Look for active Repo part 2

      quality_repo = {
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

      quality_repos.append(quality_repo)

  return quality_repos


def repositoryDiscovery():
    print("=== STAGE 1: REPOSITORY DISCOVERY ===")

    # Search for repositories
    repos = searchRepos(language='python', min_stars=1000)
    print(f"Found {len(repos)} repositories from search") ################################################## For Debugging

    # Filter for quality
    quality_repos = filterRepos(repos)
    print(f"Filtered to {len(quality_repos)} high-quality repositories") ################################################## For Debugging

    # Save to JSON
    filename = saveJSON(quality_repos, 'data/high_quality_repos.json')
    summaryDisplay(quality_repos, "repositories")

    return quality_repos

repos = repositoryDiscovery()