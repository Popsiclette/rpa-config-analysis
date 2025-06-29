import datetime
import os
import time
from pprint import pprint

import pandas as pd
import requests

from util import PROJECTS_FILE

# Minimum number of stars
# MIN_STARS = 700

# Maximum number of stars (None for no maximum limit)
# MAX_STARS = 900



def load():
    repositories = dict()
    print(f'Loading repositories from {PROJECTS_FILE}...', end=' ')
    try:
        df = pd.read_csv(PROJECTS_FILE, keep_default_na=False)
        for i, row in df.iterrows():
            repo = row.to_dict()
            repositories[repo['owner'] + '/' + repo['name']] = repo
        print('Done!')
    except IOError:
        print('Failed!')
    return repositories


def save(repositories):
    repositories.update(load())
    print(f'Saving repositories to {PROJECTS_FILE}...', end=' ')
    df = pd.DataFrame(repositories.values())
    df.loc[df.description.str.contains('(?i)\\bmirror\\b', na=False), 'isMirror'] = True  # Check 'mirror' in the description

    df.createdAt = pd.to_datetime(df.createdAt, infer_datetime_format=True, errors='coerce')
    df.pushedAt = pd.to_datetime(df.pushedAt, infer_datetime_format=True, errors='coerce')

    if pd.api.types.is_datetime64_any_dtype(df['createdAt']):
        df['createdAt'] = df['createdAt'].dt.tz_localize(None)
    else:
        print("Aviso: 'createdAt' não pôde ser convertido corretamente para datetime.")
        print(df['createdAt'].head())  # Mostra os primeiros valores para depuração

    if pd.api.types.is_datetime64_any_dtype(df['pushedAt']):
        df['pushedAt'] = df['pushedAt'].dt.tz_localize(None)
    else:
        print("Aviso: 'pushedAt' não pôde ser convertido corretamente para datetime.")
        print(df['pushedAt'].head())  # Mostra os primeiros valores para depuração

    df.sort_values('stargazers', ascending=False, inplace=True)
    df.to_csv(PROJECTS_FILE, index=False)
    print('Done!')


def query_filter(min_stars, max_stars, last_activity=120):
    """
    Builds the query filter string compatible to GitHub
    :param min_stars: minimum number of stargazers in the repository
    :param last_activity: number of days to check recent push activity in the repository
    :return: query filter string compatible to GitHub
    """
    date = datetime.datetime.now() - datetime.timedelta(days=last_activity)
    if max_stars:
        stars = f'{min_stars}..{max_stars}'
    else:
        stars = f'>={min_stars}'
    return f'is:public archived:false fork:false stars:{stars} pushed:>={date:%Y-%m-%d} sort:stars-asc'


def process(some_repositories, all_repositories):
    for repo in some_repositories:
        # Flattening fields
        for k, v in repo.items():
            while isinstance(v, dict):
                v = next(iter(v.values()))
            repo[k] = v

        all_repositories[repo['owner'] + '/' + repo['name']] = repo


def main():
    all_repositories = dict()
    os.environ['GITHUB_TOKEN'] = ''
    token = os.getenv('GITHUB_TOKEN')
    if not token:
        print(
            'Please, set the GITHUB_TOKEN environment variable with your OAuth token (https://help.github.com/en/articles/creating-a-personal-access-token-for-the-command-line)')
        exit(1)
    headers = {
        'Authorization': f'bearer {token}'
    }

    # AIMD parameters for auto-tuning the page size
    ai = 8  # slow start: 1, 2, 4, 8 (max)
    md = 0.5

    STARS = list(range(1000, 100, -200))
    for i in STARS:
        MIN_STARS = i
        MAX_STARS = None
        stars = MIN_STARS

        variables = {
            'filter': query_filter(MIN_STARS, MAX_STARS, last_activity=120),
            'repositoriesPerPage': 1,  # from 1 to 100
            'cursor': None
        }

        request = {
            'query': open('src/query.graphql', 'r').read(),
            'variables': variables
        }

        print(f"\n\n\n ######### RUNNING MIN_STARS {MIN_STARS} - MAX_STARS {MAX_STARS}")
        try:
            repository_count = -1
            has_next_page = True
            while has_next_page:
                print(f'Trying to retrieve the next {variables["repositoriesPerPage"]} repositories (> {stars} stars)...')
                response = requests.post(url="https://api.github.com/graphql", json=request, headers=headers)
                try:
                    result = response.json()
                except:
                    print(f'Failed with http code {response.status_code} reason {response.reason}.')
                    continue

                if 'Retry-After' in response.headers:  # reached retry limit
                    print(f'Waiting for {response.headers["Retry-After"]} seconds before continuing...', end=' ')
                    time.sleep(int(response.headers['Retry-After']))

                if 'errors' in result:
                    if 'timeout' in result['errors'][0]['message']:  # reached timeout
                        print(f'Timeout!', end=' ')
                        variables['repositoriesPerPage'] = int(max(1, variables['repositoriesPerPage'] * md))  # using AIMD
                        ai = 1  # resetting slow start
                    else:  # some unexpected error.
                        pprint(result['errors'])
                        exit(1)

                if 'data' in result and result['data']:
                    if repository_count == -1:
                        repository_count = result["data"]["search"]["repositoryCount"]

                    some_repositories = result['data']['search']['nodes']
                    process(some_repositories, all_repositories)
                    print(
                        f'Processed {len(all_repositories)} of {repository_count} repositories at {datetime.datetime.now():%H:%M:%S}.',
                        end=' ')

                    # Keeps the number of stars already processed to restart the process when reaching 1,000 repositories limit
                    if some_repositories:
                        stars = some_repositories[-1]['stargazers']

                    page_info = result['data']['search']['pageInfo']
                    variables['cursor'] = page_info['endCursor']
                    variables['repositoriesPerPage'] = min(100, variables['repositoriesPerPage'] + ai)  # using AIMD
                    ai = min(8, ai * 2)  # slow start

                    if not page_info['hasNextPage']:  # We may have finished all repositories or reached the 1,000 limit
                        if result["data"]["search"]["repositoryCount"] > 1000:  # We reached the 1,000 repositories limit
                            print(f'We reached the limit of 1,000 repositories.', end=' ')
                            variables['filter'] = query_filter(stars - 10, MAX_STARS)  # some overlap to accommodate changes in stars
                            variables['cursor'] = None
                        else:  # We have finished all repositories
                            print(f'Finished.')
                            has_next_page = False

                time.sleep(1)  # Wait 1 second before next request (https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api)
        except:
            print(response)
            save(all_repositories)
            time.sleep(60)
            continue
            #breakpoint()
        finally:
            save(all_repositories)


if __name__ == "__main__":
    main()
