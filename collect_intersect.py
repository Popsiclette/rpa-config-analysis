import pandas as pd

from util import PROJECTS_FILE, REPOS_BY_CODE, REPOS_INTERSECT

def load_base():
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

def intersect(dict1, dict2):
    common_keys = dict1.keys() & dict2.keys()
    return {k: {**dict1[k], **dict2[k]} for k in common_keys}

# def save(dict, filename):
#     with open(filename, mode='w', newline='', encoding='utf-8') as file:
#         writer = csv.writer(file)
#         writer.writerow(["repository", "search_string"])

#         for key in dict.keys():
#             writer.writerow([key, dict[key]['search_string']])

def save(repositories):
    print(f'Saving repositories to {REPOS_INTERSECT}...', end=' ')
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
    df.to_csv(REPOS_INTERSECT, index=False)
    print('Done!')

repositories_base = load_base()
repositoreis_by_code = load_by_code()

result = intersect(repositories_base, repositoreis_by_code)

print(f"\nTotal de repositórios utilizados como base: {len(repositories_base)}\n")
print(f"Total de repositórios encontrados por código: {len(repositoreis_by_code)}\n")
print(f"Interseção entre eles: {len(result)}\n")

save(result)