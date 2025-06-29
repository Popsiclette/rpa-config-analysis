import time
import requests
import csv

from util import REPOS_BY_CODE

def save(dict, filename):
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(["repository", "search_string"])

        for key in dict.keys():
            writer.writerow([key, dict[key]['search_string']])
"""
Prompt utilizado para gerar a lista:

me liste as 20 ferramentas mais utilizadas para RPA e possíveis strings que identifiquem esses projetos em bases de código

exemplo: para o python-rpa sua string poderia ser import RPA
para o scrapy sua string poderia ser import scrapy
"""
LIST_OF_SEARCH_STRINGS = [
    '"import rpa" in:file',                              # Python-RPA / Robocorp
    '"from rpa" in:file',                                # Robocorp
    '"*** Tasks ***" in:file',                           # Robot Framework
    '"*** Keywords ***" in:file',                        # Robot Framework
    '"import scrapy" in:file',                           # Scrapy
    '"from scrapy" in:file',                             # Scrapy
    '"import tagui" in:file',                            # TagUI (Python wrapper)
    '"tagui.do" in:file',                                # TagUI
    '"import sikuli" in:file',                           # SikuliX
    '"org.sikuli.script" in:file',                       # SikuliX (Java)
    '"UiPath.Core" in:file',                             # UiPath
    'extension:bprelease',                               # Blue Prism
    'extension:bpproj',                                  # Blue Prism
    '"Automation Anywhere" in:file',                     # Automation Anywhere
    'extension:atmx',                                    # Automation Anywhere
    'extension:aabot',                                   # Automation Anywhere (new gen)
    '"Microsoft.Flow" in:file',                          # Power Automate
    '"flowDefinition" in:file',                          # Power Automate JSON
    '"com.workfusion" in:file',                          # WorkFusion
    '"bot-task" in:file',                                # WorkFusion
    'extension:rpae',                                    # WorkFusion project files
    'extension:aml',                                     # HelpSystems Automate
    '"WinAutomation" in:file',                           # WinAutomation
    'extension:wap',                                     # WinAutomation files
    'extension:ahk',                                     # AutoHotkey
    '"#Persistent" in:file',                             # AutoHotkey
    'extension:robot',                                   # Robot Framework / Robocorp
    '"electroneek" in:file',                             # ElectroNeek
    'extension:enbot',                                   # ElectroNeek bots
    '"AntWorks" in:file',                                # AntWorks
    'extension:awproj',                                  # AntWorks
    '"OpenRPA" in:file',                                 # OpenRPA
    '"OpenFlow" in:file',                                # OpenRPA
    'extension:nra',                                     # NICE RPA
    'extension:nicescript'                               # NICE RPA
]

import requests
import time

GITHUB_TOKEN = ""
PER_PAGE = 100
MAX_PAGES = 100

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

repositories = {}

for string in LIST_OF_SEARCH_STRINGS:
    for page in range(1, MAX_PAGES + 1):
        print(f"Página {page}: {string}")

        url = f"https://api.github.com/search/code?q={string}&per_page={PER_PAGE}&page={page}"

        response = requests.get(url, headers=headers)
        
        if response.status_code == 403:
            print("Rate limit atingido. Aguardando 60 segundos...")
            time.sleep(60)
            continue

        data = response.json()
        items = data.get("items", [])
        
        if not items:
            print("Sem mais resultados.")
            break

        for item in items:
            repo_data = item['repository']
            repo_data['search_string'] = string
            repo_key = f"{repo_data['owner']['login']}/{repo_data['name']}"
            repositories[repo_key] = repo_data

        time.sleep(1)

print(f"\nTotal de repositórios únicos encontrados: {len(repositories)}\n")

save(repositories, REPOS_BY_CODE)