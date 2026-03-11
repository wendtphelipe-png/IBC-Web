import yt_dlp

CHANNEL_URL = 'https://www.youtube.com/@IBCTVBariatricTV/streams'
OUTPUT_FILE = 'videos_longos_bariatrictv.txt'

def fetch_videos():
    print(f"[*] Acessando o canal: {CHANNEL_URL}")
    print("[*] Varrendo todos os vídeos. Isso pode levar alguns segundos...")
    
    ydl_opts = {
        'extract_flat': True,       # Extrai rápido os dados da playlist sem baixar
        'quiet': True,              # Suprime output massivo
    }

    long_videos = []

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(CHANNEL_URL, download=False)
        
        if 'entries' in info:
            for entry in info['entries']:
                if not entry:
                    continue
                
                duration = entry.get('duration')
                # duration is in seconds. 1 hour = 3600 seconds.
                if duration and duration > 3600:
                    long_videos.append({
                        'title': entry.get('title', 'Sem Titulo'),
                        'url': entry.get('url') or entry.get('webpage_url', f"https://www.youtube.com/watch?v={entry.get('id')}"),
                        'duration': duration,
                    })
    
    # O youtube por padrão retorna do mais novo pro mais antigo.
    # Vamos inverter a lista para ficar do MAIS ANTIGO para o MAIS RECENTE
    long_videos.reverse()
    
    print(f"\n[+] Encontrados {len(long_videos)} vídeos com mais de 1 hora de duração.")
    print(f"[*] Salvando no arquivo {OUTPUT_FILE}...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("LISTA DE VÍDEOS BARIATRIC TV (MAIS DE 1 HORA)\n")
        f.write("Ordem: Do Mais Antigo para o Mais Recente\n")
        f.write("="*60 + "\n\n")
        
        for i, video in enumerate(long_videos, 1):
            horas = int(video['duration'] // 3600)
            minutos = int((video['duration'] % 3600) // 60)
            duracao_formatada = f"{horas}h {minutos}m"
            
            f.write(f"{i}. {video['url']}\n")
            f.write(f"   Título: {video['title']}\n")
            f.write(f"   Duração: {duracao_formatada}\n")
            f.write("-" * 40 + "\n")
            
    print("[OK] Arquivo gerado com sucesso!")

if __name__ == '__main__':
    fetch_videos()
