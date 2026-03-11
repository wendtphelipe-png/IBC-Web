import vimeo
import json
import os

VIMEO_TOKEN_FILE = 'vimeo_token.txt'

def get_vimeo_client():
    with open(VIMEO_TOKEN_FILE, 'r') as f:
        token = f.read().strip()
    return vimeo.VimeoClient(token=token, key='null', secret='null')

def fetch_metadata(video_id):
    client = get_vimeo_client()
    print(f"[*] Fetching metadata for video: {video_id}")
    response = client.get(f'/videos/{video_id}')
    if response.status_code == 200:
        data = response.json()
        metadata = {
            "id": video_id,
            "title": data.get('name'),
            "description": data.get('description'),
            "duration": data.get('duration'),
            "thumbnail": data.get('pictures', {}).get('base_link'), # or pick a specific size
            "publish_date": data.get('created_time', '').split('T')[0]
        }
        print(f"[+] Metadata fetched successfully: {metadata['title']}")
        return metadata
    else:
        print(f"[!] Error fetching metadata: {response.status_code}")
        print(response.text)
        return None

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python fetch_vimeo_metadata.py <video_id>")
    else:
        video_id = sys.argv[1]
        meta = fetch_metadata(video_id)
        if meta:
            with open(f'data/video_{video_id}_meta.json', 'w', encoding='utf-8') as f:
                json.dump(meta, f, indent=4)
