import pandas as pd
import requests
import time
from itertools import islice
from util import REPOS_BY_CODE, REPOS_DETAILS

# GitHub token pessoal (necessário para GraphQL)

GITHUB_TOKEN = ""

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v4+json"
}

def load_by_code():
    repositories = dict()
    print(f'Loading repositories from {REPOS_BY_CODE}...', end=' ')
    try:
        df = pd.read_csv(REPOS_BY_CODE, keep_default_na=False)
        for i, row in df.iterrows():
            repo = row.to_dict()
            repositories[repo['repository']] = repo
        print('Done!')
    except IOError:
        print('Failed!')
    return repositories

def build_query(owner, name):
    return {
        "query": f"""
        {{
          repository(owner: "{owner}", name: "{name}") {{
            nameWithOwner
            createdAt
            pushedAt
            isMirror
            diskUsage
            description
            primaryLanguage {{ name }}
            contributors: mentionableUsers {{ totalCount }}
            languages(first: 10) {{
              nodes {{ name }}
            }}
            watchers {{ totalCount }}
            stargazers {{ totalCount }}
            forks {{ totalCount }}
            issues {{ totalCount }}
            defaultBranchRef {{
              target {{
                ... on Commit {{
                  history(first: 0) {{ totalCount }}
                }}
              }}
            }}
            pullRequests {{ totalCount }}
            branches: refs(refPrefix: "refs/heads/") {{ totalCount }}
            tags: refs(refPrefix: "refs/tags/") {{ totalCount }}
            releases {{ totalCount }}
          }}
        }}
        """
    }

def fetch_repo_data(owner, name):
    print(f"Fetching {owner}/{name}...   ")
    try:
        response = requests.post(
            "https://api.github.com/graphql",
            headers=HEADERS,
            json=build_query(owner, name)
        )
        response.raise_for_status()
        data = response.json()
        print("Done!\n")
        return data["data"]["repository"]
    except Exception as e:
        print(f"Erro em {owner}/{name}: {e}")
        return None
    
def save(results):
    df = pd.DataFrame(results)
    df.to_csv(REPOS_DETAILS, index=False)
    print(f"Dados salvos com {len(results)}")


def main():
    repos = load_by_code()  # CSV no estilo owner/repo
    first_five = dict(islice(repos.items(), 100))
    results = []

    i = 0
    for full_name in repos.keys():
        if i == 50:
            save(results)
            i = 0

        if "/" not in full_name:
            continue
        owner, name = full_name.split("/")
        data = fetch_repo_data(owner, name)
        if data:
            row = {
                "repository": data.get("nameWithOwner"),
                "createdAt": data.get("createdAt"),
                "pushedAt": data.get("pushedAt"),
                "isMirror": data.get("isMirror"),
                "diskUsage": data.get("diskUsage"),
                "description": data.get("description"),
                "contributors": data["contributors"]["totalCount"],
                "primaryLanguage": data["primaryLanguage"]["name"] if data.get("primaryLanguage") else None,
                "languages": ", ".join(lang["name"] for lang in data["languages"]["nodes"]),
                "watchers": data["watchers"]["totalCount"],
                "stargazers": data["stargazers"]["totalCount"],
                "forks": data["forks"]["totalCount"],
                "issues": data["issues"]["totalCount"],
                "commits": data["defaultBranchRef"]["target"]["history"]["totalCount"]
                    if data.get("defaultBranchRef") else None,
                "pullRequests": data["pullRequests"]["totalCount"],
                "branches": data["branches"]["totalCount"],
                "tags": data["tags"]["totalCount"],  # tags usa o mesmo campo sem paginação
                "releases": data["releases"]["totalCount"],
                "search_string": repos[full_name]["search_string"]
            }
            results.append(row)
        i += 1
        time.sleep(1)  # Evita limite de rate

    # Salvar no CSV
    save(results)

if __name__ == "__main__":
    main()