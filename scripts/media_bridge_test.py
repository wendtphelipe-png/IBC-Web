import os
import time
import yt_dlp
import vimeo
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURAÇÕES INICIAIS ---
# ATENÇÃO: Preencha as duas variáveis abaixo antes de rodar!
DRIVE_FOLDER_ID = '1juS64LbqPwLtqyOuG3cSNHY3EryG4pef'
YOUTUBE_URL = 'https://www.youtube.com/watch?v=CVNariDZgQw'

# Constantes do sistema
SCOPES = ['https://www.googleapis.com/auth/drive.file']
VIMEO_TOKEN_FILE = 'vimeo_token.txt'

def get_vimeo_client():
    with open(VIMEO_TOKEN_FILE, 'r') as f:
        token = f.read().strip()
    # A API do Vimeo exige Key e Secret na classe, mas como estamos usando
    # Personal Access Token, passamos strings vazias pra não dar erro.
    return vimeo.VimeoClient(
        token=token,
        key='null', 
        secret='null'
    )

def get_drive_service():
    creds = None
    # O token.json armazena o access_token e o refresh_token, gerados no primeiro login.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # Se não houver credencial válida, logue
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Salva para a proxima vez
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
            
    return build('drive', 'v3', credentials=creds)

def download_youtube_video(url):
    print(f"[*] Iniciando download do YouTube: {url}")
    # Configuração para buscar no máximo 1080p (juntando áudio e vídeo usando o ffmpeg em MP4)
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'merge_output_format': 'mp4',
        'outtmpl': r'D:\downloads\%(title)s.%(ext)s',
        'username': 'oauth2',
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info_dict)
        
        # Como o merge muda a extensao para mp4, vamos garantir o nome final correto
        final_filename = os.path.splitext(filename)[0] + '.mp4'
        if not os.path.exists(final_filename) and os.path.exists(filename):
             final_filename = filename # Fallback
             
        # Traz titulo e descrição para injetar no Vimeo depois
        return final_filename, info_dict.get('title', 'Video'), info_dict.get('description', '')

def upload_to_drive(service, file_path, title):
    print(f"\n[*] Iniciando upload para o Google Drive: {title}")
    file_metadata = {
        'name': os.path.basename(file_path),
        'parents': [DRIVE_FOLDER_ID]
    }
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"[+] Salvo no Drive. ID do Arquivo: {file.get('id')}")
    return file.get('id')

def upload_to_vimeo(vimeo_client, file_path, title, description):
    print(f"\n[*] Iniciando upload resiliente para o Vimeo: {title}")
    try:
        # TUS protocol upload (recomendado pelo Vimeo)
        uri = vimeo_client.upload(file_path, data={
            'name': title,
            'description': description,
            'privacy': {'view': 'anybody'} # Pode mudar para 'disable' se quiser invisível no vimeo.com
        })
        print(f"[+] Upload para Vimeo concluído. URI do Vídeo: {uri}")
        return uri
    except Exception as e:
        print(f"[-] Erro ao fazer upload para o Vimeo: {e}")
        print(f"Detalhes do args: {getattr(e, 'args', 'Nenhum args encontrado')}")
        if hasattr(e, 'response') and e.response is not None:
             print(f"Detalhes do response: {e.response.text}")
        return None

def main():
    if DRIVE_FOLDER_ID == '1juS64LbqPwLtqyOuG3cSNHY3EryG4pef' and YOUTUBE_URL == 'https://www.youtube.com/watch?v=CVNariDZgQw':
        # Bypass error
        pass
    elif DRIVE_FOLDER_ID == 'COLOQUE_SEU_ID_DA_PASTA_AQUI' or YOUTUBE_URL == 'COLOQUE_O_LINK_DO_YOUTUBE_AQUI':
        print("ERRO: Edite o script e preencha as variáveis DRIVE_FOLDER_ID e YOUTUBE_URL antes de rodar.")
        return

    print(">>> INICIANDO PIPELINE MEDIA BRIDGE <<<")
    # 1. Extração
    file_path, title, description = download_youtube_video(YOUTUBE_URL)
    
    # 2. Persistência (Google Drive)
    drive_service = get_drive_service()
    upload_to_drive(drive_service, file_path, title)
    
    # 3. Distribuição (Vimeo)
    vimeo_client = get_vimeo_client()
    upload_to_vimeo(vimeo_client, file_path, title, description)
    
    # 4. Limpeza (Apagar MP4 pesado do PC local)
    print(f"\n[*] Limpando arquivo temporário local para poupar disco: {file_path}")
    if os.path.exists(file_path):
        os.remove(file_path)
        
    print("\n[OK] Fluxo Concluido com Sucesso!")

if __name__ == '__main__':
    main()
