import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
import json
import yt_dlp
import vimeo
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# --- CONFIGURAÇÕES ---
DRIVE_FOLDER_ID = '1juS64LbqPwLtqyOuG3cSNHY3EryG4pef'
VIMEO_PROJECT_ID = '28448698' # Pasta "IBC" no Vimeo
LIST_FILE = 'videos_longos_bariatrictv.txt'
STATE_FILE = 'batch_progress_state.json'
LIMIT = 9999 # Sem limites, processo rodará até acabar o arquivo TXT (139 vídeos no momento)

SCOPES = ['https://www.googleapis.com/auth/drive.file']
VIMEO_TOKEN_FILE = 'vimeo_token.txt'

def get_vimeo_client():
    with open(VIMEO_TOKEN_FILE, 'r') as f:
        token = f.read().strip()
    return vimeo.VimeoClient(token=token, key='null', secret='null')

def get_drive_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token_file:
            token_file.write(creds.to_json())
    return build('drive', 'v3', credentials=creds)

def parse_txt_list():
    videos = []
    current_video = {}
    with open(LIST_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('LISTA') or line.startswith('Ordem') or line.startswith('====') or line.startswith('----'):
                continue
            
            # Formato esperado: "1. https://www.youtube.com/watch?v=..."
            if line[0].isdigit() and '. https' in line:
                parts = line.split('. ', 1)
                idx = int(parts[0])
                url = parts[1].strip()
                current_video = {'index': idx, 'url': url}
            elif line.startswith('Título: '):
                current_video['title'] = line.replace('Título: ', '').strip()
            elif line.startswith('Duração: '):
                current_video['duration'] = line.replace('Duração: ', '').strip()
                # O bloco termina na duração, então adiciona na lista
                videos.append(current_video)
                current_video = {}
    return videos

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'completed': []}

def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=4)

def download_youtube_video(url, custom_title=None):
    print(f"[*] Iniciando download: {url}")
    ydl_opts = {
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        'merge_output_format': 'mp4',
        'outtmpl': r'D:\downloads\%(title)s.%(ext)s',
        'sleep_interval': 1,
        'max_sleep_interval': 3,
        'ignoreerrors': True, # Diz ao yt-dlp para continuar se um vídeo falhar (age-restricted)
        'cookiefile': 'cookies.txt', # Usando o novo cookie
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            
            # Se o info_dict voltar None, significa que o ignoreerrors pulou o vídeo por erro de restrição.
            if not info_dict:
                 print(f"\n[AVISO!] O vídeo a seguir falhou no download (provavelmente por restrição de idade).")
                 print(f"URL: {url}")
                 print(f"PULANDO para o próximo...")
                 return None, None, None
                 
            filename = ydl.prepare_filename(info_dict)
            final_filename = os.path.splitext(filename)[0] + '.mp4'
            if not os.path.exists(final_filename) and os.path.exists(filename):
                 final_filename = filename
                 
            title = custom_title if custom_title else info_dict.get('title', 'Video')
            return final_filename, title, info_dict.get('description', '')
    except Exception as e:
        print(f"\n[AVISO!] Exceção inesperada ou erro de restrição capturado: {e}")
        print(f"URL: {url}")
        print(f"PULANDO para o próximo vídeo...")
        return None, None, None

def upload_to_drive(service, file_path, title):
    print(f"[*] Fazendo backup no Google Drive...")
    file_metadata = {'name': os.path.basename(file_path), 'parents': [DRIVE_FOLDER_ID]}
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"[+] Salvo no Drive. ID = {file.get('id')}")
    return file.get('id')

def upload_to_vimeo(vimeo_client, file_path, title, description):
    print(f"[*] Enviando para o Vimeo: '{title}'...")
    try:
        uri = vimeo_client.upload(file_path, data={
            'name': title,
            'description': description,
            'privacy': {'view': 'anybody'}
        })
        print(f"[+] Upload finalizado. Vídeo URI: {uri}")
        
        # O uri é algo como "/videos/123456789"
        video_id = uri.split('/')[-1]
        
        # Mover para a pasta(Project) IBC. 
        # API do Vimeo permite vincular um projeto via PUT
        folder_uri = f'/me/projects/{VIMEO_PROJECT_ID}/videos/{video_id}'
        print(f"[*] Movendo o vídeo para a pasta 'IBC' (ID: {VIMEO_PROJECT_ID})...")
        response = vimeo_client.put(folder_uri)
        if response.status_code == 204 or response.status_code == 200:
             print("[+] Vídeo atrelado à pasta IBC com sucesso!")
        else:
             print(f"[-] O alerta na movimentação de pasta retornou HTTP {response.status_code}.")
             
        return uri
    except Exception as e:
        print(f"[-] Erro catastrofico no Vimeo: {e}")
        return None

def main():
    print("==================================================")
    print(">>> MEDIA BRIDGE PRO - MASS BATCH PROCESSOR <<<<")
    print("==================================================")
    
    videos = parse_txt_list()
    state = load_state()
    completed_indices = state.get('completed', [])
    
    drive_service = get_drive_service()
    vimeo_client = get_vimeo_client()
    
    contador = 0
    # Processamos os LIMIT (20) primeiros da ordem (mais antigos)
    for video in videos:
        if contador >= LIMIT:
            print(f"\n[!] Pausa programada: Os {LIMIT} primeiros vídeos foram processados com sucesso.")
            break
            
        idx = video['index']
        if idx in completed_indices:
            print(f"[SKIP] Vídeo {idx} já processado anteriormente. Pulando...")
            contador += 1
            continue
        
        print(f"\n--------------------------------------------------")
        print(f"-> PROCESSANDO VÍDEO [{idx}]: {video['title']}")
        print(f"--------------------------------------------------")
        
        max_retries = 5
        retry_count = 0
        success = False
        
        while not success and retry_count < max_retries:
            try:
                # 1. Download
                file_path, title, desc = download_youtube_video(video['url'], custom_title=video['title'])
                
                if not file_path:
                    print(f"[SKIP] Não foi possível baixar o vídeo {idx}. Pulando etapas de upload e indo para o próximo vídeo...")
                    break
                
                # 2. Upload Drive
                drive_id = upload_to_drive(drive_service, file_path, title)
                
                # 3. Upload Vimeo e Linkar a Pasta
                vimeo_uri = upload_to_vimeo(vimeo_client, file_path, title, desc)
                
                # 4. Limpeza Local
                if os.path.exists(file_path):
                    print(f"[*] Limpando arquivo temporário local para poupar disco...")
                    try:
                        os.remove(file_path)
                    except Exception as clean_e:
                        print(f"[WARN] Não foi possível deletar o arquivo local: {clean_e}")
                        print("[*] Continuando o processo de qualquer forma...")
                    
                if vimeo_uri and drive_id:
                    completed_indices.append(idx)
                    state['completed'] = completed_indices
                    save_state(state)
                    print(f"[OK] Vídeo {idx} finalizado integralmente!")
                    success = True
                else:
                    print(f"[WARN] Vídeo {idx} teve sucesso parcial. Pulando para revisão manual.")
                    break # Sai do retry loop, erro irrecoveravel
            
            except Exception as e:
                retry_count += 1
                import time
                print(f"[ERRO] Falha de conexão ou timeout no vídeo {idx} (Tentativa {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    print(f"[*] Aguardando 30 segundos antes de tentar novamente para evitar rate limits...")
                    time.sleep(30)
                else:
                    print(f"[ERRO FATAL] Limite de tentativas alcançado para o vídeo {idx}. Pulando para o PRÓXIMO vídeo do lote.")
                    break # Quebra o loop While deste vídeo, mas permite que o script continue para o próximo
            
        contador += 1
        
if __name__ == '__main__':
    main()
