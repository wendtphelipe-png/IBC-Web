import vimeo
import json
import os

VIMEO_TOKEN_FILE = 'vimeo_token.txt'

def get_vimeo_client():
    with open(VIMEO_TOKEN_FILE, 'r') as f:
        token = f.read().strip()
    return vimeo.VimeoClient(token=token, key='null', secret='null')

def check_text_tracks(video_id):
    client = get_vimeo_client()
    print(f"[*] Checking text tracks for video: {video_id}")
    response = client.get(f'/videos/{video_id}/texttracks')
    if response.status_code == 200:
        data = response.json()
        print(f"[+] Found {data['total']} text tracks")
        for track in data['data']:
            print(f" - [{track['language']}] {track['name']} | Type: {track['type']} | Link: {track['link']}")
        return data['data']
    else:
        print(f"[!] Error checking text tracks: {response.status_code}")
        return None

if __name__ == "__main__":
    import sys
    video_id = sys.argv[1] if len(sys.argv) > 1 else "1171125048"
    check_text_tracks(video_id)
