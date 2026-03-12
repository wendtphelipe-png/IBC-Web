import json
import os
import re

DB_FILE = 'data/database.json'
TEMPLATES_DIR = 'templates'
DEPLOY_DIR = '.'

def load_db():
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_video_pages(videos):
    with open(os.path.join(TEMPLATES_DIR, 'video.html'), 'r', encoding='utf-8') as f:
        template = f.read()
    
    for video in videos:
        print(f"[*] Generating page for: {video['title']}")
        
        # Build Chapters HTML
        chapters_html = ""
        for chapter in video.get('chapters', []):
            chapters_html += f"""
            <li class="chapter-item" onclick="seekTo('{chapter['time']}')">
                <span class="chapter-time">{chapter['time']}</span>
                <span class="chapter-title">{chapter['title']}</span>
            </li>
            """
        
        page_content = template
        page_content = page_content.replace('{{VIDEO_TITLE}}', video['title'])
        page_content = page_content.replace('{{VIDEO_ID}}', video['id'])
        page_content = page_content.replace('{{VIDEO_DESCRIPTION}}', video['description'])
        page_content = page_content.replace('{{VIDEO_DURATION}}', video['duration'])
        page_content = page_content.replace('{{VIDEO_DATE}}', video['publish_date'])
        page_content = page_content.replace('{{CHAPTERS_LIST}}', chapters_html)
        
        output_path = os.path.join(DEPLOY_DIR, f"video_{video['id']}.html")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(page_content)

def generate_index_page(videos):
    with open(os.path.join(TEMPLATES_DIR, 'index.html'), 'r', encoding='utf-8') as f:
        template = f.read()
    
    # Inject Search Data for client-side searching
    search_data = json.dumps(videos, ensure_ascii=False)
    injection = f"<script>window.VIDEO_DB = {search_data};</script>\n<script src='search.js'></script>"
    template = template.replace('</body>', f"{injection}\n</body>")

    cards_html = ""
    for video in videos:
        cards_html += f"""
        <a href="video_{video['id']}.html" class="glass-card video-card-link" data-id="{video['id']}" style="text-decoration: none; padding: 0; display: flex; flex-direction: column; overflow: hidden; position: relative; z-index: 5;">
            <div style="width: 100%; height: 180px; background: url('{video['thumbnail']}') center/contain no-repeat; background-color: rgba(0,0,0,0.3); border-bottom: 1px solid var(--border-gold); pointer-events: none;"></div>
            <div style="padding: 1.5rem; pointer-events: none;">
                <span class="card-label">{video['duration']}</span>
                <h3 class="card-title" style="font-size: 1.1rem; line-height: 1.3; min-height: 3rem; margin-top: 0.5rem; color: #fff;">{video['title']}</h3>
                <p style="font-size: 0.75rem; color: rgba(255,255,255,0.5); line-height: 1.4; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">{video['description'][:150]}...</p>
                <div style="margin-top: 1rem; display: flex; justify-content: flex-end; align-items: center;">
                    <span class="cta-btn" style="padding: 0.4rem 0.8rem; font-size: 0.6rem; border-radius: 6px; display: inline-block;">Watch Session</span>
                </div>
            </div>
        </a>
        """
    
    page_content = template.replace('{{VIDEO_CARDS}}', cards_html)
    
    output_path = os.path.join(DEPLOY_DIR, "index.html")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(page_content)

if __name__ == "__main__":
    if not os.path.exists(DEPLOY_DIR):
        os.makedirs(DEPLOY_DIR)
        
    db = load_db()
    generate_video_pages(db['videos'])
    generate_index_page(db['videos'])
    print("[OK] Site generated successfully in root directory")
