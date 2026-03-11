import requests

# Testando o token diretamente via REST API, ignorando as abstrações do SDK
with open('vimeo_token.txt', 'r') as f:
    token = f.read().strip()

print("Checando Token e Permissoes no Vimeo API...\n")
headers = {
    'Authorization': f'bearer {token}',
    'Accept': 'application/vnd.vimeo.*+json;version=3.4'
}

response = requests.get('https://api.vimeo.com/tutorial', headers=headers)
print(f"Status Http de Teste: {response.status_code}")
print("Response: ")
print(response.json())

print("\n---")
response_user = requests.get('https://api.vimeo.com/me', headers=headers)
print(f"Meu Usuario - Status: {response_user.status_code}")
try:
    data = response_user.json()
    print(f"Nome da Conta: {data.get('name')}")
    print(f"Escopos/Permissões ativas neste Token: {data.get('app', {}).get('name')} | Upload Quota: {data.get('upload_quota', {}).get('space', {}).get('free')}")
except Exception as e:
    print(response_user.text)
