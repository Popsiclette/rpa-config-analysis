import requests as rq

def listar_arquivos_config(repo_full_name, token=None):
    """
    Lista arquivos de configuração comuns em um repositório público do GitHub.
    
    Parâmetros:
        repo_full_name (str): nome completo do repositório (ex: "owner/nome")
        token (str): token de acesso GitHub (opcional, para aumentar o limite de requisições)
    
    Retorna:
        List[str]: lista de caminhos de arquivos de configuração encontrados
    """

    # Headers de autenticação
    headers = {}
    if token:
        headers['Authorization'] = f'token {token}'

    # Lista de extensões e nomes típicos de arquivos de configuração
    padroes_config = [
        '.env', '.ini', '.cfg', '.config', '.conf',
        '.yaml', '.yml', '.json', 'settings.xml',
        'config.json', 'config.yaml', 'settings.py',
        'config.yml', 'docker-compose.yml'
    ]

    # Endpoint para obter a árvore de arquivos do repositório (modo recursivo = todos os arquivos)
    url = f'https://api.github.com/repos/{repo_full_name}/git/trees/HEAD?recursive=1'
    response = rq.get(url, headers=headers)

    if response.status_code != 200:
        print(f"Erro ao acessar repositório: {response.status_code}")
        return []

    data = response.json()
    arquivos = data.get('tree', [])

    # Filtrar apenas arquivos (não diretórios)
    arquivos_config = [
        item['path'] for item in arquivos 
        if item['type'] == 'blob' and any(pat in item['path'].lower() for pat in padroes_config)
    ]

    return arquivos_config


# 🔍 Exemplo de uso:
if __name__ == "__main__":
    repo = "miso-lims/miso-lims"  # Substitua por qualquer repositório de RPA
    token = 'my_token'  # Ou forneça seu token pessoal: 'ghp_xxx...'

    arquivos_config = listar_arquivos_config(repo, token=token)

    if arquivos_config:
        print(f"\nArquivos de configuração encontrados no repositório '{repo}':")
        for arq in arquivos_config:
            print(" -", arq)
    else:
        print(f"Nenhum arquivo de configuração encontrado em '{repo}'.")
